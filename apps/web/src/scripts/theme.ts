export function initThemeToggle() {
  const toggles = document.querySelectorAll<HTMLButtonElement>('[data-theme-toggle]');
  
  function updateAriaLabels(theme: string) {
    const label = theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro';
    toggles.forEach(btn => btn.setAttribute('aria-label', label));
  }

  // Inicializar estado de botones
  const currentTheme = document.documentElement.dataset.theme || 'dark';
  updateAriaLabels(currentTheme);

  toggles.forEach(toggle => {
    toggle.addEventListener('click', () => {
      const isDark = document.documentElement.dataset.theme === 'dark';
      const newTheme = isDark ? 'light' : 'dark';
      
      document.documentElement.dataset.theme = newTheme;
      updateAriaLabels(newTheme);
      
      try {
        localStorage.setItem('bkb-theme', newTheme);
      } catch (e) {}
    });
  });
}

// Inicializar cuando se cargue el DOM
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initThemeToggle);
} else {
  initThemeToggle();
}
