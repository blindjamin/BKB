document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('theme-toggle-btn');
    if (!btn) return;
    
    btn.addEventListener('click', () => {
        const doc = document.documentElement;
        const currentTheme = doc.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        doc.setAttribute('data-theme', newTheme);
        try {
            localStorage.setItem('bkb-theme', newTheme);
        } catch (e) {}
    });
});
