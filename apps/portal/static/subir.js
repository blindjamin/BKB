document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('archivo-input');
    if (!input) return;
    const s = document.getElementById('upload-status'), p = document.getElementById('progreso-subida'), t = document.getElementById('upload-text'), csrf = input.getAttribute('data-csrf');

    input.addEventListener('change', async (e) => {
        const files = Array.from(e.target.files);
        if (!files.length) return;
        s.style.display = 'block';

        for (let i = 0; i < files.length; i++) {
            const f = files[i];
            t.textContent = `Subiendo ${i + 1}/${files.length}: ${f.name}...`;
            p.value = 0;
            try {
                const res1 = await fetch(input.getAttribute('data-url-subir'), {
                    method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                    body: JSON.stringify({ nombre: f.name, tipo: f.type || 'application/octet-stream', tamano: f.size })
                });
                if (!res1.ok) throw new Error((await res1.json()).error || 'Error al iniciar');
                const { id, firma } = await res1.json();

                const fd = new FormData();
                Object.entries(firma.fields).forEach(([k, v]) => fd.append(k, v));
                fd.append('file', f);

                await new Promise((res, rej) => {
                    const xhr = new XMLHttpRequest();
                    xhr.open('POST', firma.url, true);
                    xhr.upload.onprogress = e => { if (e.lengthComputable) p.value = (e.loaded / e.total) * 100; };
                    xhr.onload = () => xhr.status >= 200 && xhr.status < 300 ? res() : rej(new Error(`Error servidor externo: ${xhr.status}`));
                    xhr.onerror = () => rej(new Error('Error de red al subir al servidor externo.'));
                    xhr.send(fd);
                });

                p.removeAttribute('value');
                t.textContent = `Confirmando ${i + 1}/${files.length}...`;
                const res2 = await fetch(input.getAttribute('data-url-confirmar').replace('00000000-0000-0000-0000-000000000000', id), {
                    method: 'POST', headers: { 'X-CSRFToken': csrf }
                });
                if (!res2.ok) throw new Error((await res2.json()).error || 'Error al confirmar');
            } catch (err) {
                alert(`Error en ${f.name}: ${err.message}`);
                s.style.display = 'none';
                input.value = '';
                return;
            }
        }
        window.location.reload();
    });
});
