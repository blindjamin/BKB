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

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializarAlternanciaContrasena);
    } else {
        inicializarAlternanciaContrasena();
    }
})();
