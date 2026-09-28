// Pasa el aviso de hitos a modal. Sin JS se ve igual, abierto arriba de la página.
// El bloqueo real de archivos lo hace el servidor; esto es solo la interfaz.
document.addEventListener('DOMContentLoaded', () => {
    const d = document.getElementById('aviso-hitos');
    if (!d) return;
    d.close();
    d.showModal();
    if (d.hasAttribute('data-bloqueante')) {
        d.addEventListener('cancel', e => e.preventDefault());
        // Chrome puede cerrar con un segundo Esc pese a preventDefault: se vuelve a abrir.
        d.addEventListener('close', () => { if (!d.open) d.showModal(); });
    }
});
