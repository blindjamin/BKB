// Aviso flotante del hito en curso (personal y jefe). Aparece al entrar al proyecto, se cierra
// solo al terminar la cuenta regresiva de la franja, con la X o con "Ver hitos", y no vuelve
// en la sesión para ese proyecto. La sección Hitos sigue abajo para revisarla cuando quieran.
document.addEventListener('DOMContentLoaded', () => {
    const aviso = document.getElementById('aviso-hito');
    if (!aviso) return;
    const clave = aviso.dataset.clave;
    try { if (sessionStorage.getItem(clave) === '1') return; } catch (e) {}

    const cerrar = () => {
        aviso.classList.remove('is-open');
        try { sessionStorage.setItem(clave, '1'); } catch (e) {}
        setTimeout(() => { aviso.hidden = true; }, 400);
    };

    aviso.hidden = false;
    requestAnimationFrame(() => aviso.classList.add('is-open'));
    aviso.querySelectorAll('[data-cerrar]').forEach((el) => el.addEventListener('click', cerrar));
    aviso.querySelector('.aviso-hito-franja').addEventListener('animationend', cerrar);
});
