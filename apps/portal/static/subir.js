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
    let turno = Promise.resolve();
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

    const subir = async (f, entrada, fila) => {
        const d = entrada.dataset;
        poner(fila, 'Subiendo', 0);
        const res1 = await fetch(d.urlSubir, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': d.csrf },
            body: JSON.stringify({ nombre: f.name, tipo: f.type || 'application/octet-stream', tamano: f.size, carpeta_id: d.carpetaId || null }),
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
        const res2 = await fetch(d.urlConfirmar.replace('00000000-0000-0000-0000-000000000000', id), {
            method: 'POST', headers: { 'X-CSRFToken': d.csrf },
        });
        if (!res2.ok) throw new Error(await error(res2, 'No se pudo confirmar la subida'));
    };

    const encolar = (f, entrada, fila) => {
        poner(fila, 'En cola');
        fila.reintentar.hidden = true;
        // Uno a la vez; si uno falla, los demás siguen.
        turno = turno.then(async () => {
            try {
                await subir(f, entrada, fila);
                poner(fila, 'Listo', 100);
                subidos += 1;
            } catch (e) {
                poner(fila, `Error: ${e instanceof TypeError ? 'Sin conexión, reintenta' : e.message}`);
                fila.reintentar.hidden = false;
            }
            if (subidos) verNuevos.hidden = false;
        });
    };

    entradas.forEach(entrada => {
        entrada.addEventListener('change', () => {
            cola.hidden = false;
            Array.from(entrada.files).forEach(f => {
                const fila = crearFila(f);
                const motivo = validar(f);
                if (motivo) {
                    poner(fila, `Error: ${motivo}`);
                    return;
                }
                fila.reintentar.addEventListener('click', () => encolar(f, entrada, fila));
                encolar(f, entrada, fila);
            });
            entrada.value = '';  // permite volver a elegir el mismo archivo
        });
    });
});
