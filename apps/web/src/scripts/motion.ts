export function initMotion() {
  const isReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 6.1 Reveal
  const reveals = document.querySelectorAll('.reveal');
  if (isReduced) {
    reveals.forEach(el => el.classList.add('is-visible'));
  } else {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    reveals.forEach(el => observer.observe(el));
  }

  // 6.2 Hero Entrance
  const heroEls = document.querySelectorAll('.hero-in');
  heroEls.forEach((el, i) => {
    if (isReduced) {
      el.classList.add('is-visible');
      return;
    }
    setTimeout(() => {
      el.classList.add('is-visible');
    }, 90 + i * 90);
  });

  // 6.3 Contadores
  const animateCounter = (el: Element) => {
    const target = parseFloat(el.getAttribute('data-target') || '0');
    const suffix = el.getAttribute('data-suffix') || '';
    if (isReduced) {
      el.textContent = target + suffix;
      return;
    }
    const duration = 1100;
    const start = performance.now();
    el.textContent = '0' + suffix;
    
    const tick = (now: number) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3); // cubic ease-out
      el.textContent = Math.round(target * eased) + suffix;
      if (p < 1) {
        requestAnimationFrame(tick);
      }
    };
    requestAnimationFrame(tick);
  };
  
  const counters = document.querySelectorAll('[data-target]');
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.4 });
  counters.forEach(el => counterObserver.observe(el));

  // 6.4 Header Scroll (sólo modo reveal)
  const header = document.getElementById('site-header');
  if (header && header.dataset.mode === 'reveal') {
    const checkHeader = () => {
      if (window.scrollY > 40) {
        header.classList.add('is-scrolled');
      } else {
        header.classList.remove('is-scrolled');
      }
    };
    
    // Check on scroll
    window.addEventListener('scroll', checkHeader, { passive: true });
    
    // Y cuando entra el foco (para accesibilidad por teclado)
    header.addEventListener('focusin', () => {
      header.classList.add('is-scrolled');
    });
    
    header.addEventListener('focusout', () => {
      if (window.scrollY <= 40) {
        // pequeño timeout para permitir que el foco se mueva dentro del header sin cerrarlo
        setTimeout(() => {
          if (!header.contains(document.activeElement)) {
            header.classList.remove('is-scrolled');
          }
        }, 10);
      }
    });

    checkHeader();
  }

  // 6.5 Media query listener
  window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
    if (e.matches) {
      reveals.forEach(el => el.classList.add('is-visible'));
      heroEls.forEach(el => el.classList.add('is-visible'));
      counters.forEach(el => {
        const target = el.getAttribute('data-target');
        const suffix = el.getAttribute('data-suffix') || '';
        if (target) el.textContent = target + suffix;
      });
    }
  });
}

// 6.6 Idempotencia y auto-init
if (!(window as any).__bkbMotionInit) {
  (window as any).__bkbMotionInit = true;
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMotion);
  } else {
    initMotion();
  }
}
