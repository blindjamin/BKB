document.addEventListener('DOMContentLoaded', () => {
    // Manejo de pestañas Documentos / Fotos
    const btns = document.querySelectorAll('.tab-btn');
    const contents = document.querySelectorAll('.tab-content');

    btns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-target');
            btns.forEach(b => b.classList.remove('active'));
            contents.forEach(c => c.classList.add('is-hidden'));

            btn.classList.add('active');
            const targetContent = document.getElementById(target + '-content');
            if (targetContent) {
                targetContent.classList.remove('is-hidden');
            }
        });
    });

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
