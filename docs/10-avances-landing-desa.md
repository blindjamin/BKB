# 10 · Avances de la Landing (sesión 24 y 25 de septiembre de 2026)

> **Propósito de este archivo:**
> Registrar los cambios hechos al sitio público (`apps/web`) en la carpeta de trabajo "BKB DESA", partiendo de la rama `desarrollo`, para que el equipo y cualquier IA entiendan qué cambió, por qué y qué queda pendiente antes de fusionar.
>
> Parte del diseño (navbar, carrusel de logos, testimonios, WhatsApp y ubicación) se trajo de la rama `Lisandro`.

---

## 1. Resumen

| Área | Cambio principal |
|---|---|
| Navbar | Siempre visible, estilo de la rama `Lisandro`, colores legibles en ambos temas y enlaces en el orden de la página |
| Carrusel de logos | Franja propia bajo el hero, logos con fondo transparente en tarjeta blanca con borde salmón, gris → color al pasar el mouse |
| Hero | Más bajo, para que los logos se vean completos en la primera pantalla; tarjeta del portal adaptada al tema |
| Servicios | Nueva tarjeta "Tableros Eléctricos", texto nuevo de "Arriendo de Equipos" y arreglo del desborde en celular |
| Testimonios | Sección nueva (contenido **ficticio**) después de Mercados |
| Estadísticas | Quitadas de la landing |
| Portafolio | Especificaciones cambiadas a "rubro · ciudad" |
| Contacto | Formulario, datos de la oficina y mapa en una sola sección; el mapa se carga al hacer clic |
| Emergencias | La tarjeta de guardia pasó a ser un aviso flotante que se puede cerrar, con texto nuevo y sin "24/7" |
| WhatsApp | Botón flotante en todas las páginas |
| Colores | Tema oscuro en negro carbón con degradado; tema claro en durazno tenue; `success` naranjo |
| Dirección | La oficina pasa a **El Parque 110, La Calera** |

---

## 2. Detalle por componente

### 2.1 Navbar (`components/site/SiteHeader.astro`)
- La landing usa `headerMode="solid"`: el header se ve siempre y ya no aparece recién al hacer scroll.
- Del diseño de `Lisandro`: subrayado salmón animado al pasar el mouse y resaltado de la sección visible (IntersectionObserver sobre los `id` de las anclas).
- **Enlaces, en el orden de la página:** Inicio (`#top`) · Servicios · Mercados · Testimonios (nuevo) · Obras · Contacto. El menú móvil usa la misma lista.
- Se quitó la etiqueta "SEC CLASE A" del header (no está en el diseño de `Lisandro`).
- **Colores por tema:** variables `--hdr-text`, `--hdr-hover`, `--hdr-active` y `--pill-*`.
  - **Error corregido:** en tema claro el texto quedaba blanco sobre fondo claro, porque la regla del oscuro (`#site-header`) le ganaba en especificidad a la del claro. Las reglas del claro ahora también llevan `#site-header`.
- Los botones tipo pastilla (tema, Acceso Portal, menú móvil) comparten la clase `header-pill`. Se quitaron unos estilos inline con sintaxis inválida que no hacían nada.

### 2.2 Carrusel de clientes (`components/landing/ClientsMarquee.astro`)
- Es una franja propia **debajo** del hero (antes iba superpuesta a la foto).
- **Logos con fondo transparente:** se generaron desde `assets/clients/originals/` rellenando el blanco desde los bordes, así se conserva el blanco interno de cada logo. Los 7 JPG pasaron a PNG y `data/landing.ts` apunta a los `.png`.
- Cada logo va en una tarjeta blanca con borde salmón de 2 px. Se ve en gris al 60 %; al pasar el mouse toma color, crece al 110 % y la tarjeta toma una sombra salmón.
- Vuelta completa en 55 s (antes 32 s), con desvanecido en los bordes.
- **Error corregido:** había un salto de 12 px en cada vuelta. La animación mueve `-50%`, pero el `gap` entre las dos copias descuadraba la cuenta. Ahora no hay `gap` y cada lista lleva su propio `padding-right`.

### 2.3 Hero (`components/landing/Hero.astro`)
- Alto mínimo `calc(100svh - 310px)` y `pt/pb` de 64 px, para que la franja de logos quede completa al entrar (verificado a 1440×900 y 1366×768).
- `id="top"`, para que "Inicio" se resalte en el navbar.
- La tarjeta "Portal Digital BKB" cambia con el tema (clases `portal-card*`): en oscuro es un degradado carbón y en claro es crema.

### 2.4 Servicios (`components/landing/Services.astro` y `data/landing.ts`)
- **Nueva tarjeta, en segundo lugar:** "Tableros Eléctricos": *Desarrollo, integración y fabricación de tableros eléctricos de fuerza, control y automatización.*
- **"Arriendo de Equipos", texto nuevo:** *Arriendo y/o servicios de medición y análisis eléctrico con equipos de alta gama, certificados y de marcas de prestigio como Fluke: mediciones de red, mallas a tierra, aislación, RIC 19, termografías y alineación láser.*
- **Error corregido (celular):** la sección medía 1360 px en un celular de 360 px y estiraba la página hacia el lado. `main` es flex en columna, y un hijo con `mx-auto` toma el ancho de su contenido (todo el carrusel). Se agregó `w-full` a `Services` y, por prevención, a `Markets`.
- En celular (menos de 640 px) se ocultan las flechas porque tapaban el texto; se desliza con el dedo.

### 2.5 Testimonios (`components/landing/Testimonials.astro`)
- Traída de la rama `Lisandro`. Va después de Mercados, con `id="testimonios"`.
- ⚠️ **Contenido ficticio** (`TODO: PLACEHOLDER FICTICIO` en `data/landing.ts`): solo iniciales y sectores genéricos, sin clientes reales. **Reemplazar por reseñas reales antes de publicar a producción.**

### 2.6 Estadísticas
- Se quitaron de la landing. `Stats.astro` y los datos `stats` siguen en el código por si se vuelven a usar.

### 2.7 Portafolio (`data/landing.ts`)
| Proyecto | Antes | Ahora |
|---|---|---|
| Ampliación Planta **Faenadora y** Cecinas Sopraval | 450 kVA · Quilpué | Industria · La Calera |
| Estación de Bombeo e Impulsión ESVAL | 800 kVA · Valparaíso | Sanitaria · Valparaíso |
| Línea de Envasado Alimentos Castaño | Control Siemens S7-1500 · Santiago | Agroindustria · Santiago |

### 2.8 Contacto y ubicación (`components/landing/QuoteSection.astro`, `#cotizar`)
- Una sola sección, "Hablemos de tu proyecto.": formulario a la izquierda; tarjeta de la oficina y mapa a la derecha (en celular se apilan).
- **Mapa bajo demanda:** Google Maps se carga solo al hacer clic en "Ver mapa". Así no se envían datos ni cookies a Google sin que la persona lo pida (Ley 21.719) y la página carga más rápido. Hay además un enlace "Abrir en Google Maps".
- Se eliminó la sección "Dónde estamos" separada (`LocationMap.astro`), porque quedaba duplicada.
- Nuevas opciones en "Servicio requerido": **Tableros eléctricos** (primera) y **Arriendo y mediciones**.

### 2.9 Aviso de emergencia (`components/site/EmergencyNotice.astro`, nuevo)
- Reemplaza la tarjeta grande "¿Emergencia en planta?" que estaba en la sección de contacto.
- Tarjeta flotante abajo a la izquierda. Aparece a los 2,5 s y, al cerrarla con la X, no vuelve en la sesión (`sessionStorage['bkb-emergency-closed']`).
- **Texto definido por el usuario:**
  - Etiqueta: "Equipo para servicios de emergencia"
  - Título: "¿Emergencia en planta?"
  - Viñetas: "Fallas en MT y BT" · "Fallas en sistemas de fuerza, control y/o instrumentación"
  - Botón: "Llamar +56 9 8249 1403"
- ⚠️ **No mencionar "24/7"** (pedido del usuario).
- Diseño suave: ícono con anillo que pulsa despacio y botón translúcido que se rellena al pasar el mouse. En oscuro, degradado carbón → cobrizo; en claro, crema.
- En celular solo muestra el título y el botón de llamada.
- Respeta `prefers-reduced-motion`.

### 2.10 WhatsApp (`components/site/WhatsAppButton.astro`, nuevo)
- Traído de la rama `Lisandro`. Botón verde flotante abajo a la derecha en todas las páginas.
- Abre `wa.me` con el número de `SITE.phoneHref` y el mensaje "Hola, quisiera cotizar un servicio con BKB.".

### 2.11 Dirección de la oficina (`config/site.ts` y `layouts/Layout.astro`)
- `office`: "La Calera, Región de Valparaíso" (antes Quilpué).
- Nuevo `officeAddress`: "El Parque 110, La Calera, Región de Valparaíso" (el mismo dato que usa la rama `Lisandro`).
- En el Schema.org de `Layout.astro`: `streetAddress` "El Parque 110" y `addressLocality` "La Calera".

---

## 3. Colores (`packages/tokens/src/themes.css` y `colors.css`)

| Variable | Oscuro antes → ahora | Claro antes → ahora |
|---|---|---|
| `--page-bg` | `#080C14` → `#18181A` (negro carbón) | `#FFF4EE` → `#FDF1E8` (durazno tenue) |
| `--page-gradient` (nueva) | Degradado `#2A2A2D` → `#1B1B1D` → `#131314` con brillo salmón tenue | `none` |
| `--card-bg` | `#0F172A` → `#232326` | `#FFFFFF` → `#FFFAF6` |
| `--card-border` | `rgba(255,255,255,0.09)` → `0.1` | `#F5D9C7` → `#E8DCD2` (neutro) |
| `--text-muted` | `#94A3B8` → `#A1A1AA` (gris neutro) | `#7D6F64` → `#6B5D52` |
| `--text-subtle` | `#8391A7` → `#8E8E96` | `#7D6F64` → `#6B5D52` |
| `--input-bg` | sin cambio | `#FAF6F2` → `#FFFDFB` |
| `--input-border` | sin cambio | `#F5D9C7` → `#DDCFC3` |
| `--accent-text` | sin cambio | `salmon-700` (sin cambio neto) |

- **Degradado:** `body` usa `background-image: var(--page-gradient)` con `background-attachment: fixed`. Por eso Portafolio y Contacto ya no llevan `bg-page` propio, que lo taparía.
- **Tonos de salmón:** se usan tres con rol fijo: `500` para botones y marca, `700` para texto, enlaces y hovers en tema claro, `300` para acentos sobre oscuro. Los hovers que usaban `salmon-600` pasaron a `700`.
- `--bkb-salmon-soft`: `#FFF4EE` → `#FDF1E8`.
- `--bkb-success`: verde `#10B981` → naranjo `#C2410C` (pedido del usuario). ⚠️ Si los tokens se copian al portal, "éxito" dejará de verse verde allí.
- Se registraron `danger` y `warning` en `@theme` de `global.css`. Antes no lo estaban, así que `text-danger` y `text-warning` no pintaban nada: por eso la etiqueta de urgencia y el aviso del formulario no se leían.
- Contraste revisado para AA en los textos nuevos de ambos temas.

---

## 4. Otros cambios técnicos
- **`overflow-x: clip` en `html` y `body`** (`global.css`): evita el scroll horizontal en celular, que causaba el panel del menú móvil escondido fuera de pantalla. Se usa `clip` y no `hidden` para no romper el header `sticky`.
- **`astro.config.mjs`:** `vite.server.allowedHosts` permite `.trycloudflare.com` y `.devtunnels.ms`, para compartir el servidor de desarrollo por un túnel. Solo afecta al modo desarrollo.
- `theme-color` del `<head>` actualizado al nuevo fondo oscuro (`#18181A`).

---

## 5. Revisión de seguridad (25-09-2026)
- **Bien:** no hay secretos en el repo (solo `.env.example`), no se publican source maps, los enlaces externos llevan `noopener noreferrer`, el sitio es estático y el formulario tiene honeypot y consentimiento.
- **`npm audit`:** 3 vulnerabilidades (Astro crítica, sharp alta, esbuild baja).
  - Para el sitio publicado el riesgo práctico es bajo: casi todas las de Astro afectan a SSR, y sharp solo procesa imágenes propias al compilar.
  - Corregirlas exige subir a **Astro 7** (cambio mayor): la versión instalada, 5.18.2, ya es la última de Astro 5. Coordinar con el equipo.
- ⚠️ **esbuild en Windows permite leer archivos del computador a través del servidor de desarrollo.**
  - Evitar exponer `npm run dev:web` a internet (túneles) más que unos minutos, y no usarlo en redes Wi-Fi públicas (el proyecto usa `host: true`).
  - En esta sesión se abrió un túnel de Cloudflare para mostrar el sitio y se cerró tras la revisión.
- **Recomendado:** agregar `Content-Security-Policy` y `Referrer-Policy` como etiquetas `<meta>` (GitHub Pages no permite cabeceras propias).

---

## 6. Pendientes antes de fusionar o publicar
1. **Testimonios reales:** reemplazar los ficticios (`data/landing.ts`).
2. **Teléfono:** `config/site.ts` usa `+56 9 8249 1403`, que según `02-sitio-web-astro.md` no coincide con los teléfonos confirmados (`+56 9 8975 3095` y `+56 9 6191 1593`). Lo usan WhatsApp, el aviso de emergencia y el contacto: **confirmar antes de publicar**.
3. **Formulario:** sigue deshabilitado hasta configurar `PUBLIC_QUOTE_ENDPOINT` (por ejemplo, Formspree con Cloudflare Turnstile).
4. **Footer:** aún dice "Mantención 24/7" y "Obras Civiles". Revisar, dado que el aviso de emergencia ya no menciona 24/7.
5. **Fotos:** las tarjetas de servicios (incluida "Tableros Eléctricos") usan fotos provisorias de faena.
6. **Título de "Arriendo de Equipos":** evaluar "Arriendo y Mediciones", porque ahora también ofrece servicios de medición.
7. **Seguridad:** planificar la migración a Astro 7 y agregar CSP y Referrer-Policy.
8. **Tono azulado restante en oscuro:** el overlay del hero y el footer siguen usando `--bkb-night-*` (azulados).
9. **`package-lock.json`:** `npm install` lo modificó localmente. No incluirlo en el commit salvo que sea intencional.

---

## 7. Cómo verificar
```bash
npm install
npm run build:web                          # debe terminar en "Complete!"
GITHUB_PAGES=true npm run build:web        # base /BKB para GitHub Pages
npm run dev:web                            # http://localhost:3000
```
Revisar en ambos temas (botón sol/luna) y en celular (375 px):
- Navbar legible y con la sección activa resaltada.
- Logos completos al entrar.
- Carrusel de servicios sin scroll horizontal de la página.
- Aviso de emergencia: aparece, se cierra y no vuelve en la sesión.
- Mapa: solo carga al hacer clic.
- Formulario, tarjeta de oficina y mapa juntos en "Contacto".
