# Revisión Frontend · Pendientes por Solucionar

> **Fecha de revisión:** 15-09-2026
> **Rama:** `benjamin/2026-09-15-revision-frontend-web`
> **Alcance:** `apps/web` (sitio Astro), las 8 rutas, en escritorio (1024 / 1100 / 1280 px) y móvil (375 px), más revisión de código fuente.

---

## Resumen

| Prioridad | Cantidad | Tipo |
|---|---|---|
| 🔴 Crítico | 2 | Errores de funcionamiento |
| 🟠 Contenido | 3 | Datos de relleno que requieren información real |
| 🟡 Menor | 5 | Detalles de UX, tipeo y deuda técnica |

**Lo que funciona bien:** las 8 rutas responden 200, sin errores en consola, todas las imágenes cargan, sin scroll horizontal en móvil y los enlaces siguen funcionando al compilar con la base `/BKB` de GitHub Pages.

---

## 🔴 Críticos

### 1. Los formularios no envían y exponen datos personales en la URL
- **Archivos:** `apps/web/src/pages/contacto.astro:25` (`#quote-form`) y `apps/web/src/pages/trabaja-con-nosotros.astro:66` (`#cv-form`).
- **Problema:** los formularios no tienen `method`, `action` ni un script que los procese. Al presionar "Enviar", el navegador hace un GET a la misma página con nombre, RUT, teléfono y correo en la URL. Eso contradice la Ley 21.719 que citan esas mismas páginas. El CV adjunto se pierde, porque un envío por GET no puede incluir archivos.
- **Solución propuesta:** definir el destino de los datos (endpoint en el portal Django, servicio de formularios o correo). Mientras tanto, bloquear el envío y mostrar un aviso de "formulario en construcción".
- [ ] Pendiente

### 2. El header se rompe entre 1024 y ~1240 px
- **Archivo:** `apps/web/src/components/Header.astro`
- **Problema:** en ese rango (notebooks y tablets en horizontal), los enlaces del menú se parten en dos líneas y el texto "Portal Clientes" se sale del borde de su botón. A 1280 px se ve bien.
- **Solución propuesta:** mostrar el menú de escritorio desde `xl` en vez de `lg` (y el botón hamburguesa hasta `xl`), y agregar `whitespace-nowrap` a los enlaces y botones.
- [ ] Pendiente

---

## 🟠 Contenido (requiere información real)

### 3. Teléfono de guardia inconsistente
- **Archivos:** `apps/web/src/components/Footer.astro:16`, `apps/web/src/pages/contacto.astro:171`, `apps/web/src/layouts/Layout.astro:33`
- **Problema:** el sitio muestra `+56 9 8765 4321`, pero el enlace llama a `tel:+56912345678`: quien toque el número marca otro distinto. Ninguno de los dos parece real, y el `8765 4321` también está en los datos Schema.org para buscadores.
- **Necesito:** el número real de guardia 24/7.
- [ ] Pendiente

### 4. Imagen `civil.jpg` es un dibujo, no una foto de faena
- **Archivo de imagen:** `apps/web/public/assets/images/civil.jpg`
- **Usada en:** Inicio (servicios destacados), Servicios (SRV-04) y Obras (Canalizaciones Pesadas).
- **Problema:** es el dibujo de un casco amarillo, pero el texto alternativo dice "escalerillas portacables". Desentona con el resto de las fotos, que son reales.
- **Necesito:** una fotografía real de canalizaciones o escalerillas.
- [ ] Pendiente

### 5. Confirmar que las obras del portafolio son reales
- **Archivo:** `apps/web/src/pages/obras.astro`
- **Problema:** las 4 obras traen cifras muy concretas (barrajes de 2500 A, 2.400 m de escalerillas, 32 tableros, años y ubicaciones). Hay que validarlas antes de publicar.
- **Necesito:** confirmación o datos corregidos de cada obra.
- [ ] Pendiente

---

## 🟡 Menores

### 6. "Cotizar esta especialidad" no preselecciona el servicio
- **Archivos:** `apps/web/src/pages/servicios.astro:124` y `apps/web/src/pages/contacto.astro:98`
- **Problema:** el botón envía `?servicio=<título>`, pero la página de contacto no lee ese parámetro y el `<select>` usa otros valores (`ingenieria`, `tableros`, …).
- **Solución propuesta:** enviar el `id` del servicio (`?servicio=tableros`) y preseleccionarlo con un script en contacto.
- [ ] Pendiente

### 7. Errores de tipeo
- `apps/web/src/pages/servicios.astro:72`: "Apreté dinanométrico" → **"Apriete dinamométrico"**
- `apps/web/src/pages/obras.astro:42`: "dinanométrico" → **"dinamométrico"**
- [ ] Pendiente

### 8. Clase Tailwind que no hace nada
- **Archivo:** `apps/web/src/pages/nosotros.astro:60`
- **Problema:** `border-[#sand-200]` no es un color válido y no aplica ningún estilo.
- **Solución propuesta:** usar `border-[#E6DDD5]` o el token correspondiente.
- [ ] Pendiente

### 9. Enlaces al portal inconsistentes
- **Archivos:** `Header.astro` (x2), `Footer.astro`, `index.astro`, `obras.astro`, `contacto.astro`
- **Problema:** `https://portal.bkb.cl` está escrito a mano en 6 lugares, y solo el botón del header de escritorio abre en pestaña nueva.
- **Solución propuesta:** centralizar la URL en una constante (por ejemplo en `utils/paths.ts`) y unificar el comportamiento.
- [ ] Pendiente

### 10. Colores escritos a mano en vez de tokens
- **Archivos:** todas las páginas y componentes de `apps/web/src`
- **Problema:** se repiten valores como `#B4470F`, `#1A1513` o `#E6DDD5` en lugar de usar las variables de `@bkb/tokens`. No se ve en pantalla, pero dificulta mantener el sistema de diseño.
- **Solución propuesta:** exponer los tokens como tema de Tailwind v4 (`@theme`) y reemplazar gradualmente.
- [ ] Pendiente
