# 09 · Plan de diseño del portal (borrador para tu revisión)

> **Estado:** APROBADO por el usuario el 24-09-2026 (decisiones de la sección 9 con la propuesta por defecto, más los teléfonos de ayuda; ver sección 12). DS-0 quedó hecho como tarea 19 (22-09-2026). DS-1 a DS-7 se ejecutan agrupados en 4 pasos (sección 12.4), después del Checkpoint H.
> **Alcance:** solo la interfaz del portal (`apps/portal`: login, proyectos, archivos, subida, borrado y páginas de error). No cambia permisos, modelos ni URLs.
> **Cómo se hizo:** se revisó el código de las tareas 7 a 14, se levantó el portal en un navegador real con una base de datos de demostración aparte (con personal y cliente), y se contrastó con `docs/01`, el handoff de la landing y la maqueta `Mockup-Preliminar/BKB_Portal_-_Propuesta_de_interfaz.pptx`.

---

## 1. Resumen

**Por qué se ve feo: no es solo estética, es un fallo técnico.** El portal tiene una CSP estricta (correcta, y la exige `docs/04`), pero las plantillas usan **39 atributos `style="..."` en línea, 2 manejadores `onclick`/`onsubmit` y 2 scripts en línea**. La CSP bloquea todo eso. Por eso el navegador muestra la página casi sin estilos: enlaces azules subrayados, sin tarjetas, con el selector de archivos y la barra "Subiendo..." siempre a la vista.

Causa raíz: `settings.py` usa `CSP_INCLUDE_NONCE_IN`, que en django-csp 4.0 solo sirve para migrar configuraciones viejas y **no hace nada** con el formato nuevo (`CONTENT_SECURITY_POLICY`). La cabecera real es `script-src 'self'`, sin nonce. Las 89 pruebas automáticas pasan porque ninguna abre un navegador.

**Propuesta:** primero reparar la CSP y sacar los estilos de las plantillas (**DS-0**, es un arreglo, no un rediseño), y después construir el diseño sobre esa base sana en 7 pasos pequeños (**DS-1 a DS-7**). El diseño toma la estructura de la maqueta, pero con la paleta salmón v2 y el logo final. Se mantienen las reglas del kit: solo tokens, sin colores sueltos.

| Paso | Qué entrega | Tamaño |
|---|---|---|
| DS-0 | CSP con nonce, cero estilos ni manejadores en línea, prueba que lo vigila | M |
| DS-1 | Fundaciones: fuentes locales, tokens completos, íconos, logo, estructura común | M |
| DS-2 | Login | S |
| DS-3 | Lista de proyectos | S |
| DS-4 | Pantalla del proyecto y lista de archivos | M |
| DS-5 | Subida de archivos (celular incluido) | M |
| DS-6 | Confirmación de borrado, avisos y páginas de error | S |
| DS-7 | Pulido: tema oscuro, 320 px, accesibilidad y capturas antes/después | S |

---

## 2. Diagnóstico con evidencia

Cada punto se comprobó en el navegador (portal en `127.0.0.1`, usuario de personal con 6 archivos de ejemplo).

### 2.1 Fallos que rompen funciones (van en DS-0)

| # | Hallazgo | Evidencia | Gravedad |
|---|---|---|---|
| F1 | **La CSP bloquea los estilos en línea.** Proyectos y archivos se ven sin diseño | 19 errores de CSP en la consola (17 de estilo `style-src 'self'` y 2 de script). Estilos en línea en el código: `archivos.html` 19, `proyectos.html` 10, `archivo_item.html` 9, `base.html` 1 | Alta |
| F2 | **Las pestañas Documentos/Fotos no funcionan.** Se ven las dos listas a la vez | El script en línea de `archivos.html` está bloqueado y el `display:none` inicial también | Alta |
| F3 | **El botón "Eliminar" borra sin pedir confirmación.** El `onsubmit="return confirm(...)"` está bloqueado | `form.onsubmit` es `null` en el navegador. El aviso "El archivo dejará de verse para todos" nunca aparece. Un clic se lleva el archivo de la vista de los clientes | **Alta** |
| F4 | **El botón "Subir Archivo" no hace nada** (`onclick` bloqueado). El selector nativo quedó a la vista por F1 y su lógica está en un archivo externo, así que debería seguir funcionando (no se probó una subida real desde el navegador) | `button.onclick` es `null`. `#archivo-input` se ve con `display: inline-block` | Alta |
| F5 | **La preferencia de tema no se recuerda.** Se guarda en `localStorage` pero nunca se lee al cargar | El script del `<head>` está bloqueado: tras recargar, `data-theme` vuelve a `light` aunque `bkb-theme` sea `dark`. El modo oscuro del sistema tampoco se respeta | Media |
| F6 | **`capture="environment"` en el selector de archivos.** En celulares suele abrir solo la cámara e impide elegir un PDF o un DWG | Comportamiento habitual de los navegadores móviles. **Sin verificar en un teléfono real** | Media |

### 2.2 Problemas de diseño

| # | Hallazgo | Evidencia |
|---|---|---|
| D1 | **No se cargan las fuentes de marca.** `portal.css` fuerza `system-ui` y no hay `@font-face`. Space Grotesk e IBM Plex nunca aparecen | La landing las trae de Google Fonts; el portal no podría (la CSP lo bloquearía) y `plan.md` pide fuentes locales |
| D2 | **El logo es texto.** El encabezado dibuja "BKB" con `<text>` en `sans-serif`. Existe el logo aprobado (`bkb-logo-final.png`, medallón con fondo transparente) | `base.html` líneas 24-28 |
| D3 | **Los tokens se importan a medias.** `portal.css` carga `colors`, `themes` y `typography`, pero no `index.css`: faltan el foco visible de 3 px, los radios y los espaciados | `docs/01` exige foco de 3 px; hoy hay `outline: 2px` suelto en cada botón |
| D4 | **Sin jerarquía ni ritmo.** Un solo peso de título, sin espaciado consistente, sin agrupar información (quién subió, cuándo, tamaño) | Lista de archivos: cuatro líneas de texto con el mismo peso |
| D5 | **Emojis como íconos** (🏢 ⬇ 🗑). Cambian según el sistema operativo y no se ajustan al tema | `proyectos.html`, `archivos.html`, `archivo_item.html` |
| D6 | **Colores fuera de los tokens.** El botón Eliminar usa `#dc3545` fijo | `archivo_item.html` línea 17 |
| D7 | **Objetivos táctiles pequeños.** "Descargar" y "Eliminar" miden 12 px; la maqueta pide texto de 19 px y botones de 56 px "para usar con guantes" | `archivo_item.html` |
| D8 | **Contraste al límite.** `--text-muted` sobre `--page-bg` da **4,49:1** (AA pide 4,5:1) y sobre `--input-bg` 4,51:1 | Cálculo WCAG con los valores de `packages/tokens` |
| D9 | **Login sin ayuda.** Sin "mostrar contraseña", sin teléfono de BKB ni salida para quien no puede entrar; el mensaje de error es un texto rojo suelto | La maqueta pone el teléfono "en cada punto de bloqueo" |
| D10 | **Sin páginas de error.** No hay 403, 404 ni 500 propias. Tras 5 intentos fallidos, axes responde con texto plano (`AXES_LOCKOUT_TEMPLATE = None`). Un archivo ajeno responde JSON (`{"error": ...}`) dentro de un formulario | `templates/` solo tiene 5 archivos |
| D11 | **Estados vacíos y de carga pobres.** Cuadro de texto plano; la subida usa `alert()` y recarga toda la página al terminar | `subir.js` líneas 43 y 49 |

Lo que sí está bien y se conserva: el semáforo de colores por tema (`data-theme`), la paleta salmón con `salmon-700` en botones (blanco sobre él da 5,18:1), el mensaje de login que no revela si el correo existe, y la estructura de rutas.

---

## 3. Principios (salen de la maqueta y de `docs/01`)

1. **Lectura sin esfuerzo.** Texto de lista de 18 px (`--bkb-text-body-lg`), botones principales de 56 px en celular y de 48 px en escritorio, y todo ícono con su etiqueta escrita.
2. **Una acción principal por pantalla.** El color salmón significa "aquí se hace clic": un solo botón salmón lleno por vista.
3. **Salida telefónica.** En el login, en los errores y en los estados vacíos aparece el teléfono de BKB.
4. **Solo tokens.** Ningún hexadecimal ni tamaño suelto en plantillas ni en CSS de página.
5. **Compatible con la CSP, sin excepciones.** Sin `style="..."`, sin `on*="..."`, sin `<style>` ni `<script>` en línea salvo el del tema (con nonce).
6. **Funciona sin JavaScript** lo que se pueda: filtros, navegación, borrado (con `<dialog>` se mejora, pero el formulario es normal).
7. **Cliente y personal ven la misma estructura.** Al personal solo se le suman acciones (subir, eliminar); no es otra interfaz.

**Qué se rechaza** (patrones típicos de interfaz genérica): degradados llamativos, efecto vidrio, sombras marcadas, tarjetas idénticas sin jerarquía, bordes redondeados máximos, morado, emojis como íconos, y relleno enorme en todos lados.

---

## 4. Fundaciones (DS-1)

### 4.1 Tokens y tipografía
- Importar `tokens/index.css` completo (trae el foco de 3 px y los radios) y no solo tres de sus archivos.
- **Fuentes locales** en `static/fonts/` (`.woff2`, subconjunto latino, licencia OFL): Space Grotesk 600/700, IBM Plex Sans 400/500/600/700, IBM Plex Mono 500/600. `@font-face` con `font-display: swap`. Se sirven desde el mismo origen, así que la CSP actual las permite.
- **Escala:** título de página 1.75–2.25rem (display, 700) · título de sección 1.25rem · cuerpo 1.125rem (18 px) · secundario 0.9375rem (15 px) · etiqueta mono 0.75rem (12 px, mayúsculas, con `letter-spacing`).
- **Espaciado:** múltiplos de 4 px (`--space-1` a `--space-8`), definidos una sola vez en `portal.css`.
- **Contenedor:** máximo 1120 px, márgenes de 16 px (celular), 24 px (tablet) y 40 px (escritorio).
- **Radios:** los del kit (campo 10 px, tarjeta 16 px, pastilla 999 px). **Sombras:** ninguna en reposo; una sola muy suave al pasar el cursor.

### 4.2 Ajuste de contraste (a confirmar contigo)
`--text-muted` claro (`#7D6F64`) da 4,49:1 sobre el fondo de página. Propongo, solo para el portal, `#72645A` (5,27:1 sobre `--page-bg` y 5,30:1 sobre `--input-bg`). Como los tokens son fuente oficial (`docs/01`), la decisión de cambiarlos en el paquete o solo en el portal es tuya.

### 4.3 Íconos y logo
- **Íconos:** un solo archivo `static/icons.svg` (sprite) con unos 12 trazos de 1.75 px dibujados a mano: carpeta, archivo, imagen, descargar, subir, cámara, papelera, buscar, flecha, sol, luna, ayuda. Se usan con `<svg><use href="...#nombre"/></svg>` y `aria-hidden` cuando el texto ya explica la acción. Sin librerías nuevas.
- **Tipo de archivo:** en vez de íconos de colores, una pastilla con la extensión en IBM Plex Mono (`PDF`, `DWG`, `XLSX`, `JPG`). Da identidad de marca, no agrega colores y se entiende sin ver el ícono.
- **Logo:** `bkb-logo-final.png` recortado a cuadrado (hoy 658×379 con márgenes vacíos), a 44 px de alto en el encabezado y 88 px en el login. Al tener fondo transparente y disco oscuro, sirve igual en ambos temas. **Pendiente:** hoy solo existe en formato de imagen; conviene una versión vectorial (ver preguntas).

### 4.4 Estructura de archivos

```
static/
  portal.css          un solo archivo, con secciones: base, layout, componentes, páginas
  fonts/*.woff2
  icons.svg
  img/logo-bkb.png
  js/tema.js          alterna y recuerda el tema
  js/subir.js         subida (rehecha en DS-5)
  js/confirmar.js     diálogo de confirmación de borrado
```

El script del tema que evita el parpadeo es el único en línea, con `nonce`. El resto de la lógica va en archivos, activada por atributos `data-*`.

### 4.5 Estructura común (`base.html`)
Encabezado: logo · nombre del portal · a la derecha, correo del usuario con una etiqueta "Personal" o "Cliente", conmutador de tema (sol/luna) y "Salir". Contenedor central. Pie con el teléfono de BKB y el aviso de privacidad. Zona de avisos (mensajes de Django) bajo el encabezado, con `role="status"`. Enlace "Saltar al contenido" como primer elemento enfocable.

---

## 5. Pantallas

En cada una: para qué sirve, acción principal, estados y comportamiento en celular. Los esquemas son de estructura, no de estilo final.

### 5.1 Login (DS-2)

**Sirve para:** entrar con correo y contraseña. **Acción principal:** "Entrar al portal".

```
Escritorio (≥ 900 px)                          Celular (375 px)
┌──────────────────┬────────────────────┐      ┌───────────────────────┐
│  panel de marca  │  Ingresar          │      │ [logo]                │
│  (night-900)     │  Correo            │      │ Ingresar              │
│  [logo 88px]     │  [_______________] │      │ Correo                │
│  Sus documentos, │  Contraseña        │      │ [___________________] │
│  siempre a mano. │  [__________][Ver] │      │ Contraseña            │
│                  │  [ Entrar al portal ]     │ [_____________][Ver]  │
│  ¿Problemas?     │  ¿Problemas para   │      │ [   Entrar al portal ]│
│  +56 9 8249 1403 │  entrar? Llame...  │      │ ¿Problemas? Llame...  │
└──────────────────┴────────────────────┘      └───────────────────────┘
```

- Panel de marca a la izquierda solo en escritorio; en celular desaparece y queda el formulario.
- "Mostrar" contraseña con botón de texto (no un ojo sin etiqueta).
- **Estados:** error de credenciales (aviso con ícono y texto, `role="alert"`, sin revelar si el correo existe) · cuenta bloqueada tras 5 intentos (página propia con el teléfono, ver 5.6) · cargando (botón deshabilitado con "Entrando...").
- Sin "Soy cliente / Soy BKB": la maqueta tenía dos perfiles, pero la v1 usa un solo formulario para los dos tipos (spec, sección 2). Si quieres los dos accesos visibles, es un texto distinto, no una lógica distinta.
- No se agrega "Mantener la sesión iniciada" ni "Olvidé mi contraseña": están fuera del alcance de la v1.

### 5.2 Lista de proyectos (DS-3)

**Sirve para:** elegir un proyecto. **Acción principal:** abrir un proyecto (toda la tarjeta es el enlace).

```
Proyectos                                             (H1)
Tienes acceso a 3 proyectos                           (texto secundario)

┌──────────────────────────────────────────────────┐
│ ESVAL S.A.                          [ ACTIVO ]   │  ← empresa en mono, estado como pastilla
│ Automatización planta Concón — sala de bombas    │  ← nombre (display, 700)
│ 6 archivos · última carga 21 sep 2026            │  ← dato secundario
└──────────────────────────────────────────────────┘
```

- Una columna en celular; dos columnas desde 900 px. Los proyectos cerrados van al final y con menor énfasis.
- Al pasar el cursor: borde `salmon-300` y una sombra muy suave. Foco visible de 3 px.
- **Estado vacío del cliente:** "Aún no tienes proyectos asignados." + "Si esperabas ver alguno, llámanos: +56 9 8249 1403" (salida telefónica).
- **Estado vacío del personal:** "Todavía no hay proyectos. Créalos desde el panel de administración."
- Requiere agregar en la vista un conteo de archivos y la fecha de la última carga (dos anotaciones en la consulta, sin cambiar permisos). Si prefieres no tocar la vista, la tarjeta solo muestra empresa, nombre y estado.

### 5.3 Proyecto y archivos (DS-4)

**Sirve para:** ver y descargar archivos. **Acción principal:** "Descargar" en cada fila (para el personal, además "Subir archivos" en la cabecera).

```
Proyectos › Automatización planta Concón — sala de bombas
ESVAL S.A. · Activo                          [ Subir archivos ]  ← solo personal (salmón lleno)

[ Documentos 4 ]  [ Fotos 2 ]      ← filtro como enlaces (?tipo=), sin JavaScript

┌─────────────────────────────────────────────────────────────┐
│ NOMBRE                        SUBIDO POR       TAMAÑO       │
├─────────────────────────────────────────────────────────────┤
│ [PDF] Certificado SEC TE1...  ana@bkb.cl       1,2 MB       │
│       21 sep 2026 · 14:28              [⬇ Descargar] [🗑]   │
└─────────────────────────────────────────────────────────────┘
```

- **Filtro Documentos/Fotos** como dos enlaces (`?tipo=documentos|fotos`) con `aria-current`, resueltos en el servidor. Se eliminan las pestañas con JavaScript (F2) y el filtro se puede compartir por enlace.
- **Fila de archivo:** pastilla de extensión · nombre (hasta dos líneas, sin cortar) · quién y cuándo · tamaño · "Descargar" (botón secundario con ícono y texto). "Eliminar" (personal) es un botón discreto con ícono y texto, en el color de peligro del kit, que abre el diálogo de 5.5.
- **Escritorio:** tabla con columnas alineadas. **Celular:** cada fila pasa a tarjeta apilada, con "Descargar" a todo el ancho y 48 px de alto.
- **Fotos:** en la v1 no hay miniaturas ni vista previa (están fuera del alcance en la spec), así que van como filas con pastilla `JPG`. Las miniaturas serían una mejora posterior.
- **Estados vacíos:** "Aún no hay documentos en este proyecto" (con "Subir archivos" para el personal, y para el cliente "Tu ejecutivo de BKB los cargará aquí"). Igual para fotos.
- **Sin buscador y sin barra lateral** en la v1: la maqueta los tenía, pero con carpetas por tipo de documento y solicitudes que hoy no existen. Con 6 a 30 archivos por proyecto, el filtro basta. Un buscador por nombre en el navegador es una opción barata si la lista crece (ver preguntas).

### 5.4 Subida de archivos (DS-5)

**Sirve para:** que el personal suba varios archivos desde el celular en terreno. **Acción principal:** "Subir archivos".

- Dos botones de 56 px: **"Subir archivos"** (sin `capture`, permite elegir PDF, planos y fotos de la galería) y **"Tomar foto"** (`accept="image/*"` con `capture`). Corrige F6.
- **Cola de subida** bajo la cabecera: una fila por archivo con nombre, tamaño, barra de progreso (`<progress>` con etiqueta) y estado: *En cola → Subiendo 45 % → Confirmando → Listo* o *Error* con motivo en español ("Supera los 50 MB", "Tipo no permitido: .zip", "Sin conexión, reintenta") y botón "Reintentar".
- Una región `aria-live="polite"` anuncia los cambios.
- Al terminar todos, el botón "Ver archivos nuevos" recarga la lista. Si un archivo falla, los demás siguen (hoy un error corta todo con `alert()`).
- Validación previa en el navegador (extensión y tamaño) con los mismos límites del servidor; el servidor sigue siendo la autoridad.
- Escritorio: además, zona para arrastrar y soltar (opcional, ~10 líneas más de JS).
- El cliente no ve nada de esto (ya está resuelto en el servidor).

### 5.5 Eliminar archivo y avisos (DS-6)

- `<dialog>` nativo: **"¿Eliminar «nombre»?"** · "El archivo dejará de verse para todos, incluidos los clientes." · botones **Cancelar** (principal, con foco inicial) y **Eliminar** (peligro). Se abre con JS externo; sin JS, el formulario cae en una página de confirmación normal. Corrige F3.
- Tras eliminar, aviso arriba: "Se eliminó «nombre»" (mensajes de Django).
- Un rechazo (403) deja de responder JSON dentro de un formulario: redirige con un aviso legible.

### 5.6 Páginas de error (DS-6)

Plantillas `403.html`, `404.html`, `500.html` y la de bloqueo de axes (`AXES_LOCKOUT_TEMPLATE`), todas con el mismo esquema: título claro, una frase, un botón "Volver a proyectos" y el teléfono de BKB.

| Página | Mensaje |
|---|---|
| 404 | "No encontramos esa página." No debe revelar si un proyecto existe pero no está asignado. |
| 403 | "No tienes permiso para hacer esto." |
| 500 | "Algo falló de nuestro lado. Ya quedó registrado." |
| Bloqueo | "Por seguridad bloqueamos el acceso tras varios intentos. Llámanos y lo resolvemos." |

---

## 6. Componentes

| Componente | Variantes y estados |
|---|---|
| **Botón** | Principal (salmón-700 lleno, texto blanco) · secundario (borde) · peligro (texto `danger` sobre transparente, relleno al pasar el cursor) · enlace. Tamaños 48 px y 56 px. Estados: reposo, hover, foco (3 px), deshabilitado, cargando |
| **Campo** | Etiqueta siempre visible, radio 10 px, error con texto e ícono (no solo color), ayuda opcional |
| **Pastilla** | Estado (Activo / Cerrado), extensión (mono), rol (Personal / Cliente) |
| **Fila de archivo** | Tabla en escritorio, tarjeta apilada en celular |
| **Tarjeta de proyecto** | Enlace completo, con hover y foco |
| **Filtro** | Dos enlaces con `aria-current="page"` |
| **Diálogo** | `<dialog>` nativo, foco inicial en Cancelar, se cierra con Escape |
| **Aviso** | Éxito, error, información; `role="status"` o `role="alert"`; ícono + texto |
| **Progreso** | `<progress>` con etiqueta y porcentaje en texto |
| **Estado vacío** | Ícono, frase, acción o teléfono |

---

## 7. Criterios de calidad (los mismos de `plan.md`, sección 6)

- **WCAG 2.2 AA:** contraste 4,5:1 en texto normal y 3:1 en texto grande e íconos; toda la interfaz por teclado; foco de 3 px; etiquetas en todos los campos; jerarquía de títulos sin saltos.
- **Consola limpia:** cero errores de CSP en todas las pantallas, en ambos temas y en ambos tipos de usuario. **Este es el criterio que hoy falla.**
- **Anchos:** 320, 375, 768, 1024 y 1440 px, sin scroll horizontal.
- **Tema:** claro por defecto, oscuro completo (no solo el fondo), preferencia recordada sin parpadeo.
- **Movimiento:** solo transiciones cortas (≤ 150 ms) de color y borde, y `prefers-reduced-motion` respetado.
- **Rendimiento:** CSS único y fuentes con `font-display: swap`; LCP < 2,5 s en celular; sin librerías nuevas.
- **Seguridad no se debilita:** la CSP queda igual o más estricta, sin `unsafe-inline`.

---

## 8. Plan de ejecución

Un paso por sesión, con su commit, en una rama nueva (`benjamin/AAAA-MM-DD-portal-diseno`). Cada paso deja las pruebas en verde.

### DS-0 · Reparar la CSP y lo roto (bloqueante)
**Qué:** en `settings.py`, `'script-src': [SELF, NONCE]` (con `from csp.constants import NONCE`) y quitar `CSP_INCLUDE_NONCE_IN`. Mover los 39 estilos en línea a clases de `portal.css` (con el aspecto actual, sin rediseñar todavía), sustituir `onclick` y `onsubmit` por escuchas en archivos JS con `data-*`, reemplazar las pestañas por el filtro `?tipo=` (F2), y reparar el tema (F5). Añadir el diálogo de confirmación mínimo de F3.
**Criterios:**
- [ ] Cabecera `script-src 'self' 'nonce-...'`; ningún `style="` ni `on*=` en las plantillas
- [ ] Consola sin errores de CSP en login, proyectos, archivos (personal y cliente)
- [ ] "Eliminar" pide confirmación; "Subir Archivo" abre el selector; el tema se recuerda tras recargar
**Verificación:**
- [ ] Prueba automática nueva: cada página responde con nonce en `script-src` y su HTML no contiene `style="` ni `on\w+="` (así F1 a F4 no vuelven a pasar desapercibidos)
- [ ] `python manage.py test` en verde y comprobación manual con capturas
**Nota:** toca configuración de seguridad (CSP), que la spec pide preguntar antes. Es una corrección de algo que ya se pidió en las tareas 2, 8 y 12.

### DS-1 · Fundaciones
**Qué:** fuentes locales, `tokens/index.css` completo, variables de espacio, sprite de íconos, logo recortado, `base.html` nuevo (encabezado, contenedor, pie, avisos, enlace "saltar").
**Criterios:** tipografía de marca visible; foco de 3 px en todo; logo real en ambos temas; sin errores de CSP.
**Verificación:** capturas a 375 y 1280 px en ambos temas; contraste de los tokens nuevos revisado.

### DS-2 · Login
Panel de marca, formulario con "Mostrar", ayuda telefónica y aviso de error accesible. **Verificación:** teclado completo, 375/1280 px, ambos temas, error con credenciales falsas.

### DS-3 · Lista de proyectos
Tarjetas, estado, conteo y última carga (si se aprueba tocar la vista), estados vacíos para cliente y personal. **Verificación:** con personal, con cliente con y sin proyectos; pruebas `test_vistas_proyectos` siguen en verde.

### DS-4 · Proyecto y archivos
Cabecera con migas, filtro por enlaces, filas con pastilla de extensión, tabla y versión en tarjetas, estados vacíos. **Verificación:** `test_vistas_archivos` en verde (el cliente sigue sin ver nada ajeno); revisión visual con nombres largos (100+ caracteres) y 30 archivos.

### DS-5 · Subida
Dos botones, cola con progreso por archivo, errores en español, reintento, región `aria-live`. **Verificación:** manual como personal contra el Space (una foto y un PDF reales), un archivo de más de 50 MB, una extensión no permitida y, si es posible, desde un celular.

### DS-6 · Diálogo de borrado, avisos y páginas de error
Diálogo definitivo, mensajes de Django, plantillas 403/404/500 y de bloqueo. **Verificación:** pruebas de que un cliente sigue recibiendo 403 al borrar y de que el 404 no revela proyectos ajenos.

### DS-7 · Pulido y cierre
Paridad del tema oscuro, 320 px, `prefers-reduced-motion`, Lighthouse (accesibilidad ≥ 95) y revisión con teclado, y un documento de capturas antes/después. **Verificación:** lista de la sección 7 completa.

**Orden y dependencias:** DS-0 → DS-1 → DS-2, DS-3 → DS-4 → DS-5 → DS-6 → DS-7. DS-2 y DS-3 son independientes entre sí.

---

## 9. Decisiones que necesito de ti

| # | Decisión | Mi propuesta |
|---|---|---|
| 1 | ¿Texto de lista de 18 px (token `body-lg`) o los 19 px de la maqueta? | 18 px: ya existe en los tokens y no obliga a un valor nuevo |
| 2 | ¿Botones de 56 px solo en celular y 48 px en escritorio, o 56 px en todos lados? | 56 px en celular y 48 px en escritorio |
| 3 | ¿Ajustar `--text-muted` a `#72645A` en el paquete de tokens (afecta también a la landing) o solo en el portal? | Solo en el portal por ahora |
| 4 | Logo: hoy solo hay imagen (658×379). ¿Puedes conseguir la versión vectorial o un PNG cuadrado a mayor resolución? | Recortar el PNG actual y pedir el vectorial para después |
| 5 | Teléfono de BKB para los mensajes de ayuda: en la landing figura `+56 9 8249 1403`. ¿Es el correcto para soporte del portal? | Usar ese |
| 6 | ¿Agregar conteo de archivos y última carga en la lista de proyectos? (toca la vista, no los permisos) | Sí |
| 7 | ¿Buscador por nombre dentro de un proyecto (filtro en el navegador)? Está en la maqueta, no en la spec | No en la v1; se agrega si las listas crecen |
| 8 | El usuario solo tiene correo (no hay nombre). ¿Mostramos el correo, o agregamos un campo "nombre" al modelo para "Subido por María Bustos"? | Correo por ahora; el nombre es una mejora posterior (cambia el modelo) |
| 9 | ¿Autorizas tocar la CSP en DS-0 (nonce en `script-src`)? | Sí, es corregir un ajuste que no estaba funcionando |

---

## 10. Fuera de este plan

Miniaturas y vista previa de fotos, carpetas por tipo de documento, barra lateral, solicitudes de documento, semáforo de vigencia SEC, recuperación de contraseña, "mantener sesión iniciada", aspecto propio del panel `/admin/` y un tema para el sitio público. Todos están fuera de la v1 según `docs/03`.

---

## 11. Observaciones técnicas fuera del diseño (no se tocaron)

Vistas al leer el código para este plan. **No están corregidas ni verificadas a fondo**; las dejo anotadas para decidir si van a tareas aparte.

- **La regla de borrado está copiada en tres sitios.** `eliminar_archivo` (`views.py`) y `archivo_item.html` repiten la lógica en vez de llamar a `permisos.puede_borrar`, que es la "única fuente de reglas" según la spec (sección 6). Hoy coinciden, pero pueden divergir.
- **La IP de la descarga toma el primer valor de `X-Forwarded-For`** (`get_client_ip`). Si el proxy agrega la IP al final de la cadena, ese primer valor lo controla quien hace la petición y el registro de auditoría podría falsearse. Revisar con el proxy real en la tarea 16.
- **`iniciar_subida` acepta el `tipo` que declara el navegador** sin cruzarlo con la extensión. El riesgo es bajo (siempre se descarga como adjunto y la extensión sí se valida), pero el objeto queda guardado con el tipo declarado.
- **La comprobación de `MAX_UPLOAD_MB` y del tipo permitido está duplicada** entre `subidas.py` y la política del POST; lo importante es que el Space también la aplica (se verificó en la tarea 6).
- **Las 89 pruebas no abren un navegador**, por eso F1 a F5 pasaron desapercibidos. La prueba de contrato de DS-0 cubre lo más importante; una revisión visual por hito sigue siendo necesaria.

---

## 12. Aprobación y ampliación v1.3 (24-09-2026)

### 12.1 Decisiones aprobadas por el usuario

| # (sección 9) | Decisión |
|---|---|
| 1 | Texto de lista de 18 px (`--bkb-text-body-lg`) |
| 2 | Botones principales de 56 px en celular y 48 px en escritorio |
| 3 | `--text-muted` claro = `#72645A`, **solo en el portal** (se sobreescribe en `portal.css`; `static/tokens/` no se edita) |
| 4 | Logo recortado del PNG final de `apps/web` (`bkb-logo-final.png`). La versión vectorial queda pendiente |
| 5 | Teléfonos de ayuda: **+56 9 8975 3095** y **+56 9 6191 1593** (los dos). No se usa +56 9 8249 1403 |
| 6 | Conteo de archivos y fecha de la última carga en las tarjetas de proyecto |
| 7 | Sin buscador en la v1 |
| 8 | Resuelta por la tarea 20: el usuario tiene `nombre`; "Subido por" muestra el nombre (o el correo si está vacío) |
| 9 | Resuelta: DS-0 se hizo como tarea 19 |
| — | Fuentes: `.woff2` descargados de Google Fonts (subconjunto latino) con su licencia OFL en `static/fonts/` |

### 12.2 Cambios respecto del borrador del 21-09

- **Login (5.1):** ahora sí existe "¿Olvidaste tu contraseña?" (tarea 28). Se muestra como enlace bajo el botón.
- **Inicio (5.2):** el personal y el jefe ven **empresas** con proyectos vigentes (tarea 22), con "+ Nueva empresa" como acción principal. El cliente ve sus proyectos. El estado vacío del personal ya no remite al panel de administración.
- **Proyecto (5.3):** suma el estado del flujo (En curso, Esperando recepción, Recibido), el panel de hitos (personal y jefe), las carpetas y las migas *Empresa › Proyecto › Carpeta*.
- **Fuera de alcance (sección 10):** "recuperación de contraseña" y "carpetas" ya no están fuera: se implementaron (tareas 28 y 23). Las carpetas son de un solo nivel y solo existen en la base de datos.
- **Pestañas Documentos/Fotos:** DS-0 las dejó funcionando con JS externo. En el paso C pasan al filtro por enlaces `?tipo=` que propone 5.3.
- **Filtro de archivos (paso C):** además de Documentos y Fotos hay un enlace "Todos", que es la opción por defecto (sin `?tipo=`): una sola página muestra todo lo que el usuario puede ver.

### 12.3 Pantallas nuevas

**Empresas y formularios (paso B).** La lista de empresas usa tarjetas iguales a las de proyecto: nombre, RUT en mono y cantidad de proyectos activos. En la empresa, el historial de proyectos va con la pastilla Activo/Cerrado y "+ Nuevo proyecto" como acción principal. Los formularios de empresa y de proyecto llevan una etiqueta siempre visible, error con texto (no solo color) y los hitos en un área de texto, uno por línea, con su ayuda. Los clientes asignados van como lista de casillas con nombre y correo.

**Gestión de usuarios (paso B, solo el jefe).**
- Tabla en escritorio y tarjetas en celular: nombre, correo, pastilla de tipo, pastilla Activo/Inactivo y si ya creó su contraseña.
- Filtros por tipo y por estado como enlaces que **se combinan** (`?rol=cliente&activo=1`), con `aria-current`.
- "+ Nuevo usuario" como acción principal.
- En la ficha: Guardar (principal), "Reenviar invitación" **solo si el usuario aún no creó su contraseña**, y Desactivar (peligro, con confirmación) o Reactivar.

**Contraseña (paso B).** Crear la contraseña (invitación o recuperación), pedir el enlace, "enlace enviado" y "enlace inválido o vencido" usan el mismo esquema de tarjeta centrada del login, con el logo, una frase y los dos teléfonos. El rechazo por exceso de pedidos (429) usa el mismo esquema.

**Proyecto: hitos (paso C, personal y jefe).**
- Lista vertical tipo "pasos": ícono de cumplido o pendiente, nombre, y fecha y nombre de quien lo marcó.
- "Marcar siguiente hito" es un botón secundario, porque la acción principal de la pantalla sigue siendo subir.
- "Deshacer último" es un botón de enlace con confirmación.
- La pastilla del estado del flujo va en la cabecera del proyecto.

**Proyecto: carpetas (paso C).**
- Fila de pastillas o tarjetas compactas con el ícono de carpeta y la cantidad de archivos; en celular se desplazan en horizontal o pasan a dos columnas.
- "Nueva carpeta" es un formulario en línea (campo y botón secundario).
- Dentro de una carpeta: el título de la carpeta, "← Volver a <proyecto>" y "Eliminar carpeta" (peligro, con confirmación).

**Aviso al cliente (paso C).**
- `<dialog>` con la misma lista de pasos (cumplido, actual y pendiente) y un mensaje por estado.
- En "Esperando recepción": el formulario con nombre del revisor, la casilla "Recepcionado y revisado", "Confirmar" (principal) y "No conforme" (secundario), más los dos teléfonos.
- Sin JS se ve arriba de la página. El diálogo debe verse bien a 320 px, sin scroll horizontal.

### 12.4 Ejecución agrupada

| Paso | Incluye | Rama |
|---|---|---|
| A | DS-1 (fundaciones) | `benjamin/2026-09-24-portal-diseno` |
| B | DS-2 y DS-3, más empresas, formularios, Gestión y contraseña | la misma |
| C | DS-4 y DS-5, más hitos, carpetas y aviso | la misma |
| D | DS-6 y DS-7, más la página 429 | la misma |

### 12.5 Cierre del diseño (25-09-2026)
- Pasos A a D hechos (DS-0 a DS-7). Diálogo de confirmación único (`static/js/confirmar.js`) para borrar archivos y carpetas, deshacer hitos y desactivar usuarios; sin JS, borrar un archivo pasa por una página de confirmación.
- Páginas propias 403, 404, 500 y de bloqueo (axes), con los dos teléfonos.
- Filtro de archivos con "Todos" por defecto, más Documentos y Fotos (decisión del paso C).
- Verificado: con pruebas automáticas (contrato CSP en todas las pantallas nuevas, un solo `<h1>` en login, inicio, proyecto y Gestión, avisos con `role="alert"`/`role="status"`, `prefers-reduced-motion` y transiciones de 150 ms o menos solo en color y borde). Pendiente del usuario: capturas de login, inicio, proyecto y Gestión a 320, 375 y 1280 px en ambos temas (revisión visual del tema oscuro y del ancho de 320 px), foco de 3 px con teclado y Lighthouse (accesibilidad ≥ 95).
- Los JS siguen en `static/` salvo `js/login.js` y `js/confirmar.js`: moverlos es cosmético.
