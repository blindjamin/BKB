document.addEventListener('DOMContentLoaded', () => {
    // Confirmación de acciones (por ejemplo, confirmación de borrado)
    document.querySelectorAll('form[data-confirmar]').forEach(form => {
        form.addEventListener('submit', (e) => {
            const mensaje = form.getAttribute('data-confirmar');
            if (mensaje && !window.confirm(mensaje)) {
                e.preventDefault();
            }
        });
    });
});
