// E2: "Usar el encargado de la empresa" copia nombre y correo del encargado de la empresa elegida.
document.addEventListener('DOMContentLoaded', function () {
    const datos = JSON.parse(document.getElementById('encargados-empresa').textContent);
    document.getElementById('usar-encargado-empresa').addEventListener('click', function () {
        const encargado = datos[document.getElementById('id_empresa').value];
        if (!encargado) return;
        document.getElementById('id_encargado_nombre').value = encargado[0];
        document.getElementById('id_encargado_email').value = encargado[1];
    });
});
