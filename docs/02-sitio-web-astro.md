# 02 · Sitio Web Público (Astro)

> **Nota para IAs y desarrolladores frontend:**  
> Este documento describe la arquitectura, rutas, componentes y directrices de compilación de `apps/web`.

---

## 1. Stack Tecnológico
- **Framework:** Astro 5+
- **Modo:** Salida Estática (`output: 'static'`)
- **Estilos:** `@bkb/tokens` con utilidades personalizadas de diseño en `src/styles/global.css`.
- **Cero JS del Lado del Cliente:** Todo el HTML se pre-renderiza en tiempo de compilación para máxima velocidad y seguridad. Solo pequeños scripts progresivos (menú responsive, copy al portapapeles) se usan en el cliente.

---

## 2. Mapa de Rutas
| Ruta | Archivo Fuente | Propósito |
|---|---|---|
| `/` | `src/pages/index.astro` | Portada institucional, propuesta de valor, métricas y banner del portal. |
| `/servicios` | `src/pages/servicios.astro` | Catálogo de las 5 especialidades de BKB con anclas a cada una. |
| `/obras` | `src/pages/obras.astro` | Portafolio de proyectos industriales destacados y credenciales. |
| `/nosotros` | `src/pages/nosotros.astro` | Historia de BKB desde 1999, pilares de trabajo y seguridad en faena. |
| `/contacto` | `src/pages/contacto.astro` | Formulario de cotización de obras con protección honeypot. |
| `/trabaja-con-nosotros` | `src/pages/trabaja-con-nosotros.astro` | Convocatorias técnicas y subida de CV con consentimiento Ley 21.719. |
| `/privacidad` | `src/pages/privacidad.astro` | Política de tratamiento y protección de datos personales. |
| `/terminos` | `src/pages/terminos.astro` | Términos y condiciones del servicio y portal documental. |

---

## 3. Componentes Clave
- `src/layouts/Layout.astro`: Shell principal. Incluye encabezados de accesibilidad (skip to content), metadatos OpenGraph, Schema.org `LocalBusiness`, y llamada a Header y Footer.
- `src/components/Header.astro`: Barra de navegación con logo SVG vectorial, estados activos por ruta y botón directo al portal de clientes.
- `src/components/Footer.astro`: Pie de página institucional con franja de guardia de emergencia 24/7 y enlaces normativos.
- `src/components/Button.astro`: Botón con variantes `primary`, `secondary` y `tertiary` adaptado a la sensación táctil de faena.

---

## 4. Reglas de Desarrollo
1. Mantener todas las imágenes en formatos optimizados (SVG vectoriales para logos e íconos, WebP/AVIF para fotografías de faena).
2. Asegurar que cada nueva página incluya títulos y metadescripciones únicos en las props de `Layout`.
3. Validar la compilación ejecutando siempre `npm run build:web` antes de confirmar cambios.
