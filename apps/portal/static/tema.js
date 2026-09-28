document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('theme-toggle-btn');
    if (!btn) return;
    const doc = document.documentElement;
    const use = btn.querySelector('use');
    const sprite = use.getAttribute('href').split('#')[0];

    // En tema claro se ofrece la luna (pasar a oscuro); en oscuro, el sol.
    const pintar = () => {
        const oscuro = doc.getAttribute('data-theme') === 'dark';
        use.setAttribute('href', `${sprite}#${oscuro ? 'sol' : 'luna'}`);
        btn.setAttribute('aria-pressed', oscuro ? 'true' : 'false');
    };
    pintar();

    btn.addEventListener('click', () => {
        const newTheme = doc.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        doc.setAttribute('data-theme', newTheme);
        try {
            localStorage.setItem('bkb-theme', newTheme);
        } catch (e) {}
        pintar();
    });
});
