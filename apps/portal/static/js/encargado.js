// E2: "Agregar los encargados de la empresa" suma a la lista los encargados de la empresa elegida que falten.
document.addEventListener('DOMContentLoaded', function () {
    const datos = JSON.parse(document.getElementById('encargados-empresa').textContent);
    const lista = document.getElementById('encargados-lista');
    const boton = document.querySelector('[data-agregar-fila="encargado-nuevo"]');
    document.getElementById('usar-encargado-empresa').addEventListener('click', function () {
        const ya = new Set([...lista.querySelectorAll('input[type="email"]')].map(i => i.value.trim().toLowerCase()));
        (datos[document.getElementById('id_empresa').value] || []).forEach(function ([nombre, email]) {
            if (ya.has(email.toLowerCase())) return;
            // primero las filas vacías; si no hay, una nueva
            let fila = [...lista.children].find(f => !f.querySelector('input[type="email"]').value.trim());
            if (!fila) fila = window.agregarFila(boton);
            fila.querySelector('input[type="text"]').value = nombre;
            fila.querySelector('input[type="email"]').value = email;
        });
    });
});
