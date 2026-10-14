// "+ Agregar ...": clona la fila vacía de un formset (empty_form, en un <template>) las veces que haga falta.
// button[data-agregar-fila=<id del template>][data-prefijo=<prefijo del formset>] y, para ubicarla,
// data-antes=<id> (se inserta antes de ese elemento) o data-destino=<id> (se agrega al final).
window.agregarFila = function (boton) {
    const total = document.querySelector('input[name="' + boton.dataset.prefijo + '-TOTAL_FORMS"]');
    const caja = document.createElement('ul');
    caja.innerHTML = document.getElementById(boton.dataset.agregarFila).innerHTML.replaceAll('__prefix__', total.value);
    const fila = caja.firstElementChild;
    if (boton.dataset.antes) document.getElementById(boton.dataset.antes).before(fila);
    else document.getElementById(boton.dataset.destino).append(fila);
    total.value = Number(total.value) + 1;
    return fila;
};

document.addEventListener('click', function (e) {
    const boton = e.target.closest('[data-agregar-fila]');
    if (!boton) return;
    window.agregarFila(boton).querySelector('input[type="text"], input[type="email"]').focus();
});
