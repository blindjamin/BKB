// Modificaciones del proyecto: buscar por nombre, filtrar por estado y abrir o cerrar todas de una vez.
// Sin JS el filtro queda oculto y cada modificación se abre con su propio <details>.
(() => {
    const filtro = document.querySelector('[data-filtro-modificaciones]');
    if (!filtro) return;
    const buscar = filtro.querySelector('[data-buscar]');
    const estado = filtro.querySelector('[data-estado]');
    const alternar = filtro.querySelector('[data-alternar]');
    const sinResultados = document.querySelector('[data-sin-resultados]');
    const items = [...document.querySelectorAll('#modificaciones details.modificacion')];
    const visibles = () => items.filter((m) => !m.hidden);

    const filtrar = () => {
        const texto = buscar.value.trim().toLowerCase();
        items.forEach((m) => {
            m.hidden = !m.dataset.titulo.includes(texto) || (estado.value && m.dataset.estado !== estado.value);
        });
        sinResultados.hidden = visibles().length > 0;
        rotular();
    };

    const rotular = () => {
        alternar.textContent = visibles().every((m) => m.open) ? 'Ocultar todas' : 'Ver todas';
    };

    alternar.addEventListener('click', () => {
        const abrir = !visibles().every((m) => m.open);
        visibles().forEach((m) => { m.open = abrir; });
        rotular();
    });
    buscar.addEventListener('input', filtrar);
    estado.addEventListener('change', filtrar);
    items.forEach((m) => m.addEventListener('toggle', rotular));
    filtro.hidden = false;
    rotular();
})();
