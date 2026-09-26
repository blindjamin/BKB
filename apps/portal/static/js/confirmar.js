// Diálogo único de confirmación (docs/09 §5.5 y §6). Reemplaza a window.confirm.
// - form[data-confirmar]: si se confirma, envía el formulario original.
// - a[data-confirmar-eliminar]: sin JS lleva a la página de confirmación (GET); con JS, el diálogo envía POST a su href.
// Los textos se ponen con textContent. Cancelar es el principal y recibe el foco; Esc cierra (nativo).
document.addEventListener('DOMContentLoaded', () => {
    const dialogo = document.getElementById('dialogo-confirmar');
    if (!dialogo || typeof dialogo.showModal !== 'function') return;  // sin <dialog>: queda el comportamiento sin JS
    const titulo = document.getElementById('dialogo-confirmar-titulo');
    const texto = document.getElementById('dialogo-confirmar-texto');
    const cancelar = document.getElementById('dialogo-cancelar');
    const accion = document.getElementById('dialogo-accion');
    const formDialogo = document.getElementById('dialogo-confirmar-form');
    let pendiente = null;

    const abrir = (origen) => {
        pendiente = origen;
        titulo.textContent = origen.dataset.confirmarTitulo || '¿Confirmar?';
        texto.textContent = origen.dataset.confirmar || '';
        accion.textContent = origen.dataset.confirmarAccion || 'Confirmar';
        dialogo.showModal();
        cancelar.focus();
    };

    document.addEventListener('submit', (e) => {
        const form = e.target;
        if (form.matches('form[data-confirmar]')) {
            e.preventDefault();
            abrir(form);
        }
    });

    document.addEventListener('click', (e) => {
        const enlace = e.target.closest('a[data-confirmar-eliminar]');
        if (enlace) {
            e.preventDefault();
            abrir(enlace);
        }
    });

    accion.addEventListener('click', () => {
        if (!pendiente) return;
        if (pendiente.tagName === 'FORM') {
            pendiente.submit();  // submit() no vuelve a disparar el evento: no hay bucle
        } else {
            formDialogo.action = pendiente.href;
            formDialogo.submit();
        }
        dialogo.close();
    });

    dialogo.addEventListener('close', () => { pendiente = null; });
});
