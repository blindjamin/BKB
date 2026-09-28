/**
 * Alternancia accesible de visibilidad de contraseña (DS-2).
 * Conforme con CSP estricta (sin manejadores inline ni eval).
 */
(function () {
    function inicializarAlternanciaContrasena() {
        const toggleBtn = document.getElementById('toggle-password-btn');
        const passwordInput = document.getElementById('id_password');

        if (!toggleBtn || !passwordInput) {
            return;
        }

        toggleBtn.addEventListener('click', function () {
            const esPassword = passwordInput.getAttribute('type') === 'password';

            if (esPassword) {
                passwordInput.setAttribute('type', 'text');
                toggleBtn.textContent = 'Ocultar';
                toggleBtn.setAttribute('aria-pressed', 'true');
                toggleBtn.setAttribute('aria-label', 'Ocultar contraseña');
            } else {
                passwordInput.setAttribute('type', 'password');
                toggleBtn.textContent = 'Mostrar';
                toggleBtn.setAttribute('aria-pressed', 'false');
                toggleBtn.setAttribute('aria-label', 'Mostrar contraseña');
            }
        });
    }

    // Estado de carga (docs/09 §5.1): evita el doble envío. El botón no tiene name: no se pierde ningún valor.
    function inicializarEstadoEntrando() {
        const form = document.querySelector('.login-form');
        if (!form) {
            return;
        }
        form.addEventListener('submit', function () {
            const boton = form.querySelector('button[type="submit"]');
            boton.disabled = true;
            boton.textContent = 'Entrando…';
        });
    }

    function inicializar() {
        inicializarAlternanciaContrasena();
        inicializarEstadoEntrando();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        inicializar();
    }
})();
