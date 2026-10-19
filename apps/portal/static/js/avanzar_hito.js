// Diálogo para marcar siguiente hito y solicitar los correos específicos para ese avance.
document.addEventListener('DOMContentLoaded', () => {
    const botonAbrir = document.querySelector('[data-abrir-avanzar-hito]');
    const dialogo = document.getElementById('dialogo-avanzar-hito');
    if (!botonAbrir || !dialogo || typeof dialogo.showModal !== 'function') return;

    const textarea = dialogo.querySelector('textarea[name="correos"]');
    const botonesCerrar = dialogo.querySelectorAll('[data-cerrar-dialogo]');

    botonAbrir.addEventListener('click', (e) => {
        e.preventDefault();
        dialogo.showModal();
        textarea?.focus();
    });

    botonesCerrar.forEach(b => {
        b.addEventListener('click', () => {
            dialogo.close();
        });
    });

    dialogo.addEventListener('click', (e) => {
        const rect = dialogo.getBoundingClientRect();
        const enCaja = (
            rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
            rect.left <= e.clientX && e.clientX <= rect.left + rect.width
        );
        if (!enCaja) dialogo.close();
    });
});
