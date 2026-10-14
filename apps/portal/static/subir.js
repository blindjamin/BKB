// Subida con cola (docs/09 §5.4): iniciar -> POST prefirmado al Space (XHR con progreso) -> confirmar.
// El servidor sigue siendo la autoridad; aquí solo se adelanta el aviso con sus mismos límites.
// Los nombres de archivo se muestran siempre con textContent, nunca con innerHTML.
document.addEventListener('DOMContentLoaded', () => {
    const entradas = ['archivo-input', 'foto-input'].map(id => document.getElementById(id)).filter(Boolean);
    if (!entradas.length) return;
    const cola = document.getElementById('cola-subida');
    const lista = document.getElementById('cola-lista');
    const verNuevos = document.getElementById('ver-nuevos');
    const datos = entradas[0].dataset;
    const maxBytes = Number(datos.maxMb) * 1024 * 1024;
    const extensiones = datos.extensiones.split(',');
    const SIMULTANEOS = 3;
    const pendientes = [];
    let activos = 0;
    let subidos = 0;

    document.querySelectorAll('[data-abrir]').forEach(boton => {
        boton.addEventListener('click', () => document.getElementById(boton.dataset.abrir).click());
    });
    verNuevos.addEventListener('click', () => window.location.reload());

    const validar = (f) => {
        const punto = f.name.lastIndexOf('.');
        const ext = punto >= 0 ? f.name.slice(punto).toLowerCase() : '';
        if (!extensiones.includes(ext)) return `Tipo no permitido: ${ext || 'sin extensión'}`;
        if (f.size > maxBytes) return `Supera los ${datos.maxMb} MB`;
        return null;
    };

    const crearFila = (texto, bytes) => {
        const li = document.createElement('li');
        li.className = 'cola-fila';
        const nombre = document.createElement('span');
        nombre.className = 'cola-nombre';
        nombre.textContent = texto;
        const tamano = document.createElement('span');
        tamano.className = 'cola-tamano';
        tamano.textContent = `${(bytes / 1024 / 1024).toFixed(1)} MB`;
        const barra = document.createElement('progress');
        barra.max = 100;
        barra.value = 0;
        barra.setAttribute('aria-label', `Progreso de ${texto}`);
        const estado = document.createElement('span');
        estado.className = 'cola-estado';
        const porcentaje = document.createElement('span');
        porcentaje.setAttribute('aria-hidden', 'true');  // el porcentaje no se anuncia en cada paso
        const reintentar = document.createElement('button');
        reintentar.type = 'button';
        reintentar.className = 'btn-link';
        reintentar.textContent = 'Reintentar';
        reintentar.hidden = true;
        li.append(nombre, tamano, barra, estado, porcentaje, reintentar);
        lista.append(li);
        return { li, barra, estado, porcentaje, reintentar };
    };

    const poner = (fila, texto, pct) => {
        fila.estado.textContent = texto;
        fila.porcentaje.textContent = pct === undefined ? '' : ` ${pct} %`;
        if (pct !== undefined) fila.barra.value = pct;
    };

    const error = async (res, porDefecto) => {
        try { return (await res.json()).error || porDefecto; } catch (e) { return porDefecto; }
    };

    const subir = async ({ f, fila, carpetaId }) => {
        poner(fila, 'Subiendo', 0);
        const res1 = await fetch(datos.urlSubir, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': datos.csrf },
            body: JSON.stringify({ nombre: f.name, tipo: f.type || 'application/octet-stream', tamano: f.size, carpeta_id: carpetaId || null, modificacion_id: datos.modificacionId || null }),
        });
        if (!res1.ok) throw new Error(await error(res1, 'No se pudo iniciar la subida'));
        const { id, firma } = await res1.json();

        const fd = new FormData();
        Object.entries(firma.fields).forEach(([k, v]) => fd.append(k, v));
        fd.append('file', f);
        await new Promise((ok, falla) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', firma.url, true);
            xhr.upload.onprogress = e => { if (e.lengthComputable) poner(fila, 'Subiendo', Math.round(e.loaded / e.total * 100)); };
            xhr.onload = () => (xhr.status >= 200 && xhr.status < 300 ? ok() : falla(new Error(`El almacenamiento respondió ${xhr.status}`)));
            xhr.onerror = () => falla(new Error('Sin conexión, reintenta'));
            xhr.send(fd);
        });

        poner(fila, 'Confirmando');
        const res2 = await fetch(datos.urlConfirmar.replace('00000000-0000-0000-0000-000000000000', id), {
            method: 'POST', headers: { 'X-CSRFToken': datos.csrf },
        });
        if (!res2.ok) throw new Error(await error(res2, 'No se pudo confirmar la subida'));
    };

    // Al vaciarse la cola: sin errores en pantalla, recarga para mostrar los archivos nuevos
    const alTerminar = () => {
        if (activos || pendientes.length) return;
        if (lista.children.length) verNuevos.hidden = !subidos;
        else if (subidos) window.location.reload();
        else cola.hidden = true;
    };

    // Hasta SIMULTANEOS a la vez; si uno falla, los demás siguen.
    const avanzar = () => {
        while (activos < SIMULTANEOS && pendientes.length) {
            const tarea = pendientes.shift();
            activos += 1;
            subir(tarea).then(() => {
                tarea.fila.li.remove();  // listo: la tarjeta sale y no queda nada que reintentar
                subidos += 1;
            }, (e) => {
                poner(tarea.fila, `Error: ${e instanceof TypeError ? 'Sin conexión, reintenta' : e.message}`);
                tarea.fila.reintentar.hidden = false;
            }).finally(() => {
                activos -= 1;
                avanzar();
                alTerminar();
            });
        }
    };

    const encolar = (tarea) => {
        tarea.fila.reintentar.hidden = true;
        poner(tarea.fila, 'En cola');
        pendientes.push(tarea);
        avanzar();
    };

    // tareas: [{ f, nombre (lo que se muestra), carpetaId }]
    const agregarTareas = (tareas) => {
        cola.hidden = false;
        verNuevos.hidden = true;
        tareas.forEach(tarea => {
            tarea.fila = crearFila(tarea.nombre, tarea.f.size);
            const motivo = validar(tarea.f);
            if (motivo) {
                poner(tarea.fila, `Error: ${motivo}`);
                return;
            }
            tarea.fila.reintentar.addEventListener('click', () => encolar(tarea));
            encolar(tarea);
        });
        alTerminar();
    };

    const agregar = (archivos, carpetaId) => agregarTareas(Array.from(archivos).map(f => ({ f, nombre: f.name, carpetaId })));

    // Carpetas completas (docs/12, S1-S7): se pide el árbol al servidor y cada archivo va a la cola con su carpeta
    const IGNORAR = /^(\.DS_Store|Thumbs\.db|desktop\.ini|~\$.*)$/i;  // S5
    const MAX_ARCHIVOS = 500;  // S4
    const preguntar = (titulo, texto, accion) => (window.confirmar
        ? window.confirmar(titulo, texto, accion)
        : Promise.resolve(window.confirm(`${titulo}\n\n${texto}`)));
    const fallo = (texto, motivo) => {
        cola.hidden = false;
        poner(crearFila(texto, 0), `Error: ${motivo}`);
    };
    const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`;

    // archivos: [{ f, ruta: 'Rev A/plano.pdf' }] relativos a la carpeta; rutas: Set de subcarpetas ('Rev A', …)
    const subirCarpeta = async (raiz, archivos, rutas, carpetaId) => {
        archivos = archivos.filter(a => !IGNORAR.test(a.f.name));
        if (archivos.length > MAX_ARCHIVOS) {
            fallo(raiz, `tiene ${archivos.length} archivos y el máximo es ${MAX_ARCHIVOS}. Súbela por partes.`);
            return;
        }
        const malos = archivos.filter(a => validar(a.f)).length;
        const bytes = archivos.filter(a => !validar(a.f)).reduce((n, a) => n + a.f.size, 0);
        let texto = `${plural(rutas.size, 'subcarpeta', 'subcarpetas')}, ${plural(archivos.length - malos, 'archivo', 'archivos')} (${(bytes / 1024 / 1024).toFixed(1)} MB).`;
        if (malos) texto += ` ${plural(malos, 'archivo no se subirá', 'archivos no se subirán')}: tipo no permitido o muy grande.`;
        if (!await preguntar(`¿Subir la carpeta «${raiz}»?`, texto, 'Subir')) return;

        const res = await fetch(datos.urlArbol, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': datos.csrf },
            body: JSON.stringify({ padre: carpetaId || null, raiz, rutas: Array.from(rutas) }),
        }).catch(() => null);
        if (!res || !res.ok) {
            fallo(raiz, res ? await error(res, 'No se pudo crear la carpeta') : 'Sin conexión, reintenta');
            return;
        }
        const { carpetas } = await res.json();
        subidos += 1;  // la carpeta nueva ya es algo que mostrar, aunque no traiga archivos (S6)
        agregarTareas(archivos.map(({ f, ruta }) => ({
            f,
            nombre: `${raiz}/${ruta}`,  // S7
            carpetaId: carpetas[ruta.includes('/') ? ruta.slice(0, ruta.lastIndexOf('/')) : ''],
        })));
    };

    const rutasDe = (archivos) => {
        const rutas = new Set();
        archivos.forEach(({ ruta }) => {
            const partes = ruta.split('/').slice(0, -1);
            partes.forEach((_, i) => rutas.add(partes.slice(0, i + 1).join('/')));
        });
        return rutas;
    };

    const carpetaInput = document.getElementById('carpeta-input');
    if (carpetaInput) {
        // S1: sin selector de carpetas (o en un teléfono, donde no sirve) el botón no se muestra
        const tactil = !window.matchMedia('(pointer: fine)').matches;
        if (!('webkitdirectory' in carpetaInput) || tactil) document.getElementById('btn-subir-carpeta').hidden = true;
        carpetaInput.addEventListener('change', () => {
            const archivos = Array.from(carpetaInput.files).map(f => ({ f, ruta: f.webkitRelativePath.split('/').slice(1).join('/') }));
            const raiz = carpetaInput.files.length ? carpetaInput.files[0].webkitRelativePath.split('/')[0] : '';
            carpetaInput.value = '';
            if (raiz) subirCarpeta(raiz, archivos, rutasDe(archivos), datos.carpetaId);
        });
    }

    // Arrastrar carpetas: se recorren con la API de entradas; readEntries entrega de a tandas (100 en Chrome)
    const archivoDe = entrada => new Promise((ok, falla) => entrada.file(ok, falla));
    const leerTodo = lector => new Promise((ok, falla) => {
        const todas = [];
        const leer = () => lector.readEntries(tanda => {
            if (!tanda.length) return ok(todas);
            todas.push(...tanda);
            leer();
        }, falla);
        leer();
    });
    const leerCarpeta = async (dir, prefijo = '', res = { archivos: [], rutas: new Set() }) => {
        for (const entrada of await leerTodo(dir.createReader())) {
            const ruta = prefijo ? `${prefijo}/${entrada.name}` : entrada.name;
            if (entrada.isDirectory) {
                res.rutas.add(ruta);  // S6: también las vacías
                await leerCarpeta(entrada, ruta, res);
            } else {
                res.archivos.push({ f: await archivoDe(entrada), ruta });
            }
        }
        return res;
    };

    entradas.forEach(entrada => {
        entrada.addEventListener('change', () => {
            agregar(entrada.files, entrada.dataset.carpetaId);
            entrada.value = '';  // permite volver a elegir el mismo archivo
        });
    });

    // Arrastrar: sobre una carpeta sube a esa carpeta; en cualquier otra parte, a donde se está mirando
    const conArchivos = e => Array.from(e.dataTransfer?.types || []).includes('Files');
    let destino = null;
    const marcar = (pastilla) => {
        destino?.classList.remove('es-destino');
        destino = pastilla;
        destino?.classList.add('es-destino');
        document.body.dataset.destino = destino ? `la carpeta ${destino.dataset.carpetaNombre}`
            : (datos.destino || 'la modificación');
    };
    const soltar = () => {
        marcar(null);
        document.body.classList.remove('arrastrando');
    };
    document.addEventListener('dragover', e => {
        if (!conArchivos(e)) return;
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        document.body.classList.add('arrastrando');
        marcar(e.target.closest?.('[data-carpeta-id]') || null);
    });
    document.addEventListener('dragleave', e => { if (!e.relatedTarget) soltar(); });
    document.addEventListener('drop', e => {
        if (!conArchivos(e)) return;
        e.preventDefault();
        const carpetaId = destino ? destino.dataset.carpetaId : datos.carpetaId;
        soltar();
        // Las entradas se piden ya: después del evento dataTransfer queda vacío
        const soltadas = Array.from(e.dataTransfer.items || []).map(i => i.webkitGetAsEntry?.()).filter(Boolean);
        const carpetas = soltadas.filter(en => en.isDirectory);
        if (!carpetas.length || !datos.urlArbol) {  // solo archivos, o una página sin carpetas (modificación)
            agregar(e.dataTransfer.files, carpetaId);
            return;
        }
        (async () => {
            const sueltos = await Promise.all(soltadas.filter(en => en.isFile).map(archivoDe));
            if (sueltos.length) agregar(sueltos, carpetaId);
            for (const dir of carpetas) {  // de a una: cada carpeta tiene su propia confirmación
                try {
                    const { archivos, rutas } = await leerCarpeta(dir);
                    await subirCarpeta(dir.name, archivos, rutas, carpetaId);
                } catch (err) {
                    fallo(dir.name, 'no se pudo leer la carpeta');
                }
            }
            alTerminar();
        })();
    });
});
