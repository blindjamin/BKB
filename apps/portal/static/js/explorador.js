// Explorador tipo Drive (docs/13): selección, menú contextual, diálogos «Nombre» y «Mover a», eliminar varios y teclado.
// Las acciones siguen siendo formularios POST con redirección: aquí solo se arman. El servidor vuelve a validar todo.
// Los nombres se muestran siempre con textContent, nunca con innerHTML.
document.addEventListener('DOMContentLoaded', () => {
    const zona = document.querySelector('.ex-zona[data-url-mover]');
    if (!zona) return;
    const datos = zona.dataset;
    const filas = [...zona.querySelectorAll('.ex-fila')];
    const herramientas = zona.querySelector('.ex-herramientas');
    const barraSeleccion = zona.querySelector('.ex-seleccion');
    const cuentaSeleccion = zona.querySelector('.ex-seleccion-n');
    const marcarTodo = zona.querySelector('.ex-marcar-todo');
    const menu = document.getElementById('ex-menu');
    const fino = window.matchMedia('(pointer: fine)').matches;  // P1: con mouse, clic selecciona y doble clic abre
    const iconos = (document.querySelector('use')?.getAttribute('href') || '').split('#')[0];
    let ancla = null;  // desde dónde se extiende la selección con Shift
    let objetivos = [];  // sobre qué actúa el menú abierto

    const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`;
    const seleccion = () => filas.filter(f => f.classList.contains('es-seleccionada'));
    const filaDe = (el) => el.closest('.ex-fila');
    const dialogoAbierto = () => document.querySelector('dialog[open]');

    // ----- Selección -----
    const disponibles = (contenedor, objs) => {
        const una = objs.length === 1 ? objs[0].dataset : null;
        const reglas = {
            abrir: una && una.tipo === 'carpeta' && !('objetivo' in una),  // la miga ya es la carpeta abierta
            descargar: una && una.tipo === 'archivo',  // ponytail: de a uno; varios a la vez pide ZIP por selección
            renombrar: !!una,
            mover: objs.length > 0,
            eliminar: objs.length > 0 && objs.every(o => o.dataset.borrable),
        };
        contenedor.querySelectorAll('[data-accion]').forEach(b => {
            if (b.dataset.accion in reglas) b.hidden = !reglas[b.dataset.accion];
        });
        // Sin separadores sueltos al principio, al final ni seguidos
        let anterior = null;
        contenedor.querySelectorAll('.menu-item, .menu-separador').forEach(el => {
            if (!el.classList.contains('menu-separador')) {
                if (!el.hidden) anterior = el;
                return;
            }
            el.hidden = !anterior || anterior.classList.contains('menu-separador');
            if (!el.hidden) anterior = el;
        });
        if (anterior?.classList.contains('menu-separador')) anterior.hidden = true;
    };

    const actualizar = () => {
        const sel = seleccion();
        filas.forEach(f => {
            const casilla = f.querySelector('.ex-marcar');
            if (casilla) casilla.checked = f.classList.contains('es-seleccionada');
        });
        barraSeleccion.hidden = !sel.length;
        herramientas.hidden = !!sel.length;
        zona.classList.toggle('hay-seleccion', sel.length > 0);
        cuentaSeleccion.textContent = sel.length === 1 ? '1 seleccionado' : `${sel.length} seleccionados`;
        if (marcarTodo) {
            marcarTodo.checked = sel.length > 0 && sel.length === filas.length;
            marcarTodo.indeterminate = sel.length > 0 && sel.length < filas.length;
        }
        disponibles(barraSeleccion, sel);
    };

    const elegir = (fila, modo) => {  // modo: 'solo' | 'alternar' | 'rango'
        if (modo === 'rango' && ancla) {
            const [a, b] = [filas.indexOf(ancla), filas.indexOf(fila)].sort((x, y) => x - y);
            filas.forEach((f, i) => f.classList.toggle('es-seleccionada', i >= a && i <= b));
        } else if (modo === 'alternar') {
            fila.classList.toggle('es-seleccionada');
            ancla = fila;
        } else {
            filas.forEach(f => f.classList.toggle('es-seleccionada', f === fila));
            ancla = fila;
        }
        actualizar();
    };

    const soltar = () => {
        filas.forEach(f => f.classList.remove('es-seleccionada'));
        actualizar();
    };

    const modo = e => (e.shiftKey ? 'rango' : (e.ctrlKey || e.metaKey ? 'alternar' : 'solo'));

    zona.addEventListener('click', (e) => {
        if (e.target === marcarTodo) {
            filas.forEach(f => f.classList.toggle('es-seleccionada', marcarTodo.checked));
            actualizar();
            return;
        }
        const fila = filaDe(e.target);
        if (!fila) return;
        if (e.target.closest('.ex-marcar')) {
            elegir(fila, e.shiftKey ? 'rango' : 'alternar');
            return;
        }
        const botonMenu = e.target.closest('[data-accion="menu"]');
        if (botonMenu) {
            if (!fila.classList.contains('es-seleccionada')) elegir(fila, 'solo');
            const r = botonMenu.getBoundingClientRect();
            abrirMenu(seleccion(), r.right, r.bottom, botonMenu);
            return;
        }
        if (e.target.closest('.ex-descargar')) return;  // el botón de descarga funciona siempre
        // Táctil: el toque abre (enlace normal) y la casilla selecciona. Enter sobre el enlace (detail 0) también abre
        if (!fino || e.detail === 0) return;
        e.preventDefault();
        elegir(fila, modo(e));
    });

    zona.addEventListener('dblclick', (e) => {
        const fila = filaDe(e.target);
        if (fino && fila && !e.target.closest('.ex-marcar, [data-accion], .ex-descargar')) abrir(fila);
    });

    zona.addEventListener('contextmenu', (e) => {
        const fila = filaDe(e.target);
        if (!fila) return;
        e.preventDefault();
        if (!fila.classList.contains('es-seleccionada')) elegir(fila, 'solo');
        abrirMenu(seleccion(), e.clientX, e.clientY, fila.querySelector('.ex-nombre'));
    });

    // Clic en un espacio vacío suelta la selección, como en Drive
    document.addEventListener('click', (e) => {
        if (!seleccion().length || dialogoAbierto()) return;
        if (e.target.closest('.ex-fila, .ex-seleccion, #ex-menu, .ex-encabezado')) return;
        soltar();
    });

    // ----- Menú contextual -----
    let devolverFoco = null;
    let abiertoEn = 0;
    const abrirMenu = (objs, x, y, origen) => {
        objetivos = objs;
        abiertoEn = performance.now();
        devolverFoco = origen || null;
        disponibles(menu, objs);
        menu.hidden = false;
        const { width, height } = menu.getBoundingClientRect();
        menu.style.left = `${Math.max(8, Math.min(x, window.innerWidth - width - 8))}px`;
        menu.style.top = `${Math.max(8, y + height > window.innerHeight - 8 ? y - height : y)}px`;
        menu.querySelector('.menu-item:not([hidden])')?.focus();
    };
    const cerrarMenu = (conFoco) => {
        if (menu.hidden) return;
        menu.hidden = true;
        if (conFoco) devolverFoco?.focus();
    };
    menu.addEventListener('click', (e) => {
        const boton = e.target.closest('[data-accion]');
        if (!boton) return;
        const objs = objetivos;
        cerrarMenu(false);
        ejecutar(boton.dataset.accion, objs);
    });
    menu.addEventListener('keydown', (e) => {
        if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
        e.preventDefault();
        const items = [...menu.querySelectorAll('.menu-item:not([hidden])')];
        const i = items.indexOf(document.activeElement);
        items[(i + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length]?.focus();
    });
    document.addEventListener('click', (e) => { if (!e.target.closest('#ex-menu, [data-accion="menu"], [data-objetivo]')) cerrarMenu(false); });
    window.addEventListener('resize', () => cerrarMenu(false));
    // Al hacer scroll se cierra, salvo justo después de abrir (el clic puede llegar con la página aún desplazándose)
    window.addEventListener('scroll', () => { if (performance.now() - abiertoEn > 400) cerrarMenu(false); }, { passive: true });

    // La miga de la carpeta actual abre sus acciones, sin tocar la selección
    zona.querySelectorAll('[data-objetivo]').forEach(boton => {
        boton.addEventListener('click', () => {
            if (!menu.hidden) return cerrarMenu(true);
            const r = boton.getBoundingClientRect();
            abrirMenu([boton], r.left, r.bottom + 4, boton);
        });
    });

    barraSeleccion.addEventListener('click', (e) => {
        const boton = e.target.closest('[data-accion]');
        if (!boton) return;
        if (boton.dataset.accion === 'soltar') soltar();
        else ejecutar(boton.dataset.accion, seleccion());
    });

    // Menús <details> (+ Nuevo, ⋯ del proyecto): se cierran al elegir o al hacer clic afuera
    document.addEventListener('click', (e) => {
        document.querySelectorAll('.menu-desplegable[open]').forEach(d => {
            if (!d.contains(e.target) || e.target.closest('.menu-item')) d.removeAttribute('open');
        });
    });

    // Cancelar es type="button": así Enter en el campo envía con «Guardar» y no con el primer botón
    document.querySelectorAll('[data-cerrar-dialogo]').forEach(b => b.addEventListener('click', () => b.closest('dialog').close()));

    // ----- Acciones -----
    const abrir = (el) => {
        const d = el.dataset;
        window.location.href = d.tipo === 'carpeta' ? `?carpeta=${d.id}` : d.urlDescargar;
    };

    const poner = (form, campo, valores) => {
        form.querySelectorAll(`input[data-extra="${campo}"]`).forEach(i => i.remove());
        valores.forEach(v => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = campo;
            input.value = v;
            input.dataset.extra = campo;
            form.append(input);
        });
    };
    const ids = (objs, tipo) => objs.filter(o => o.dataset.tipo === tipo).map(o => o.dataset.id);

    const ejecutar = (accion, objs) => {
        if (accion === 'nueva-carpeta') return pedirNombre(null);
        if (!objs.length) return;
        if (accion === 'abrir' || accion === 'descargar') return abrir(objs[0]);
        if (accion === 'renombrar' && objs.length === 1) return pedirNombre(objs[0]);
        if (accion === 'mover' && dialogoMover) return abrirMover(objs);
        if (accion === 'eliminar' && objs.every(o => o.dataset.borrable)) return eliminar(objs);
    };

    // Nombre: nueva carpeta o renombrar (D6). Archivos: la extensión queda fija (R2)
    const dialogoNombre = document.getElementById('ex-dialogo-nombre');
    const formNombre = dialogoNombre.querySelector('form');
    const campoNombre = formNombre.elements.nombre;
    const extFija = formNombre.querySelector('.archivo-ext-fija');
    const pedirNombre = (el) => {
        const d = el ? el.dataset : null;
        const archivo = d && d.tipo === 'archivo';
        dialogoNombre.querySelector('h2').textContent = d ? 'Cambiar nombre' : 'Nueva carpeta';
        formNombre.action = d
            ? (archivo ? datos.urlRenombrarArchivo : datos.urlRenombrarCarpeta).replace('00000000-0000-0000-0000-000000000000', d.id)
            : datos.urlCrear;
        formNombre.elements.padre.disabled = !!d;
        campoNombre.maxLength = archivo ? 240 : 100;
        campoNombre.value = d ? (archivo ? d.base : d.nombre) : 'Carpeta sin título';
        extFija.hidden = !archivo;
        extFija.textContent = archivo ? d.ext : '';
        dialogoNombre.showModal();
        campoNombre.select();
    };

    zona.querySelector('[data-accion="nueva-carpeta"]')?.addEventListener('click', () => pedirNombre(null));

    const eliminar = (objs) => {
        const carpetas = ids(objs, 'carpeta');
        const archivos = ids(objs, 'archivo');
        const titulo = objs.length === 1 ? `¿Eliminar «${objs[0].dataset.nombre}»?` : `¿Eliminar ${objs.length} elementos?`;
        const partes = [];
        if (archivos.length) partes.push(`${archivos.length === 1 ? 'El archivo dejará' : 'Los archivos dejarán'} de verse para todos, incluidos los clientes.`);
        if (carpetas.length) partes.push(`No se borra ningún archivo de ${carpetas.length === 1 ? 'la carpeta' : 'las carpetas'}: lo que ${carpetas.length === 1 ? 'tiene' : 'tienen'} adentro pasa a la carpeta de arriba.`);
        const preguntar = window.confirmar || ((t, x) => Promise.resolve(window.confirm(`${t}\n\n${x}`)));
        preguntar(titulo, partes.join(' '), 'Eliminar').then((ok) => {
            if (!ok) return;
            const form = document.getElementById('ex-form-eliminar');
            poner(form, 'archivos', archivos);
            poner(form, 'carpetas', carpetas);
            // Si se elimina la carpeta que se está mirando (desde la miga), se vuelve a la de arriba
            if (objs.some(o => o.dataset.id === datos.desde)) form.elements.desde.value = objs[0].dataset.padre || '';
            form.submit();
        });
    };

    // «Mover a» (D5): navega carpeta por carpeta; las que no sirven quedan deshabilitadas, con el motivo
    const dialogoMover = document.getElementById('ex-dialogo-mover');
    let abrirMover = null;
    if (dialogoMover) {
        const arbol = JSON.parse(document.getElementById('ex-arbol').textContent);
        const porId = new Map(arbol.map(c => [c.id, c]));
        const hijos = id => arbol.filter(c => c.padre === id).sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'));
        const nivel = (id) => { let n = 0; for (let c = porId.get(id); c; c = porId.get(c.padre)) n += 1; return n; };
        const altura = id => 1 + Math.max(0, ...hijos(id).map(h => altura(h.id)));
        const debajo = (id, res = new Set()) => { res.add(id); hijos(id).forEach(h => debajo(h.id, res)); return res; };
        const formMover = dialogoMover.querySelector('form');
        const lista = dialogoMover.querySelector('.ex-mover-lista');
        const vacio = dialogoMover.querySelector('.ex-mover-vacio');
        const aviso = dialogoMover.querySelector('.ex-mover-aviso');
        const nombreLugar = dialogoMover.querySelector('.ex-mover-nombre');
        const subir = dialogoMover.querySelector('[data-mover-subir]');
        const moverAqui = dialogoMover.querySelector('[data-mover-aqui]');
        const max = Number(datos.maxNiveles);
        let moviendo = [];
        let bloqueadas = new Set();
        let lugar = null;

        const motivo = (destino) => {
            for (const o of moviendo) {
                if (o.dataset.tipo !== 'carpeta') continue;
                if (destino && debajo(o.dataset.id).has(destino)) return 'Una carpeta no se puede mover dentro de sí misma.';
                if (nivel(destino) + altura(o.dataset.id) > max) return `Así quedarían más de ${max} niveles de carpetas.`;
            }
            if (moviendo.every(o => (o.dataset.padre || null) === destino)) return 'Ya está en esta carpeta.';
            return '';
        };

        const icono = () => {
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('class', 'icono');
            svg.setAttribute('aria-hidden', 'true');
            const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
            use.setAttribute('href', `${iconos}#carpeta`);
            svg.append(use);
            return svg;
        };

        const pintar = () => {
            nombreLugar.textContent = lugar ? porId.get(lugar).nombre : 'Raíz del proyecto';
            subir.hidden = !lugar;
            lista.replaceChildren(...hijos(lugar).map((c) => {
                const li = document.createElement('li');
                const boton = document.createElement('button');
                boton.type = 'button';
                boton.className = 'ex-mover-carpeta';
                boton.disabled = bloqueadas.has(c.id);
                boton.append(icono(), document.createTextNode(c.nombre));
                boton.addEventListener('click', () => { lugar = c.id; pintar(); });
                li.append(boton);
                return li;
            }));
            vacio.hidden = lista.children.length > 0;
            const problema = motivo(lugar);
            aviso.textContent = problema;
            moverAqui.disabled = !!problema;
            formMover.elements.destino.value = lugar || '';
            (lista.querySelector('button:not([disabled])') || moverAqui).focus();
        };
        subir.addEventListener('click', () => { lugar = porId.get(lugar).padre; pintar(); });

        abrirMover = (objs) => {
            moviendo = objs;
            bloqueadas = new Set();
            ids(objs, 'carpeta').forEach(id => debajo(id, bloqueadas));
            lugar = objs[0].dataset.padre || null;
            dialogoMover.querySelector('h2').textContent = objs.length === 1 ? `Mover «${objs[0].dataset.nombre}»` : `Mover ${plural(objs.length, 'elemento', 'elementos')}`;
            poner(formMover, 'archivos', ids(objs, 'archivo'));
            poner(formMover, 'carpetas', ids(objs, 'carpeta'));
            dialogoMover.showModal();
            pintar();
        };
    }

    // ----- Teclado (D14) -----
    const nombres = () => filas.map(f => f.querySelector('.ex-nombre'));
    document.addEventListener('keydown', (e) => {
        if (dialogoAbierto() || e.target.closest('input, textarea, select, [contenteditable]')) return;
        if (e.key === 'Escape') {
            if (!menu.hidden) cerrarMenu(true);
            else soltar();
            return;
        }
        if (!menu.hidden) return;
        const fila = filaDe(e.target);
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'a' && (fila || e.target === document.body)) {
            e.preventDefault();
            filas.forEach(f => f.classList.add('es-seleccionada'));
            actualizar();
        } else if (e.key === 'Delete' && seleccion().length) {
            e.preventDefault();
            ejecutar('eliminar', seleccion());
        } else if (e.key === 'F2' && seleccion().length === 1) {
            e.preventDefault();
            ejecutar('renombrar', seleccion());
        } else if (fila && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
            e.preventDefault();
            const lista = nombres();
            const siguiente = filas[filas.indexOf(fila) + (e.key === 'ArrowDown' ? 1 : -1)];
            if (!siguiente) return;
            lista[filas.indexOf(siguiente)].focus();
            elegir(siguiente, e.shiftKey ? 'rango' : 'solo');
        } else if (fila && e.key === ' ' && e.target.classList.contains('ex-nombre')) {
            e.preventDefault();
            elegir(fila, 'alternar');
        } else if (fila && e.key === 'ContextMenu') {
            e.preventDefault();
            if (!fila.classList.contains('es-seleccionada')) elegir(fila, 'solo');
            const r = fila.getBoundingClientRect();
            abrirMenu(seleccion(), r.left + 24, r.bottom, e.target);
        }
    });

    actualizar();
});
