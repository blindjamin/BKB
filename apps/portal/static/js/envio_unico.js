// Evita el doble envío de cualquier formulario POST (crear proyecto, empresa, etc.): el primer envío bloquea los
// siguientes hasta que cargue la página nueva. Escucha en window, así corre después de confirmar.js y respeta
// los envíos que otro script canceló (diálogo de confirmación): esos no cuentan.
window.addEventListener('submit', function (e) {
    const form = e.target;
    if (e.defaultPrevented || (form.method || '').toLowerCase() !== 'post') return;
    if (form.dataset.enviando) {
        e.preventDefault();
        return;
    }
    form.dataset.enviando = '1';
    const boton = e.submitter;
    // Se deshabilita después del evento: hacerlo antes quitaría su name/value del envío (p. ej. respuesta=aprobar)
    if (boton) setTimeout(function () { boton.disabled = true; boton.setAttribute('aria-busy', 'true'); }, 0);
});

// Al volver con "Atrás" el navegador puede restaurar la página tal cual: se libera para poder enviar de nuevo.
window.addEventListener('pageshow', function () {
    document.querySelectorAll('form[data-enviando]').forEach(function (form) {
        delete form.dataset.enviando;
        form.querySelectorAll('[aria-busy="true"]').forEach(function (b) { b.disabled = false; b.removeAttribute('aria-busy'); });
    });
});
