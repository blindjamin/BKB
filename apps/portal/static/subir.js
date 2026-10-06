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

    const crearFila = (f) => {
        const li = document.createElement('li');
        li.className = 'cola-fila';
        const nombre = document.createElement('span');
        nombre.className = 'cola-nombre';
        nombre.textContent = f.name;
        const tamano = document.createElement('span');
        tamano.className = 'cola-tamano';
        tamano.textContent = `${(f.size / 1024 / 1024).toFixed(1)} MB`;
        const barra = document.createElement('progress');
        barra.max = 100;
        barra.value = 0;
        barra.setAttribute('aria-label', `Progreso de ${f.name}`);
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

    const agregar = (archivos, carpetaId) => {
        cola.hidden = false;
        verNuevos.hidden = true;
        Array.from(archivos).forEach(f => {
            const fila = crearFila(f);
            const motivo = validar(f);
            if (motivo) {
                poner(fila, `Error: ${motivo}`);
                return;
            }
            const tarea = { f, fila, carpetaId };
            fila.reintentar.addEventListener('click', () => encolar(tarea));
            encolar(tarea);
        });
        alTerminar();
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
        agregar(e.dataTransfer.files, carpetaId);
    });
});
