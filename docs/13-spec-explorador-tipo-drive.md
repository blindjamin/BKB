# 13 · Spec: Explorador de archivos tipo Google Drive

> **Estado:** APROBADA v1.0 (19-10-2026). Las decisiones están en la sección "Decisiones".
> Parte de lo que ya existe (docs/12): árbol de carpetas, subir carpetas, mover y renombrar. **No cambia** el
> modelo de datos, el Space, los permisos ni el bloqueo del cliente (A8). Lo que se rehace es cómo se ve y cómo se
> usa la página `archivos.html`.

## Objetivo

Que moverse, ver, mover, copiar, renombrar y eliminar archivos y carpetas dentro de un proyecto se sienta como en
Google Drive: una sola lista, seleccionar y después actuar, un menú con clic derecho y un diálogo «Mover a» que
deja navegar por las carpetas.

## Diagnóstico (portal local, 19-10-2026, usuario jefe, proyecto «NV 28174 (prueba)»)

| # | Problema hoy | Cómo lo hace Drive |
|---|---|---|
| D1 | El explorador queda **enterrado**: arriba van los datos del proyecto (fechas, encargados) y tres botones de subida, y abajo Modificaciones e Hitos. Dentro de una carpeta se siguen viendo «Editar proyecto» y «Editar hitos». | Lo central es la lista de archivos. Los datos del proyecto van en un panel de detalles que se abre aparte. |
| D2 | Las **carpetas y los archivos son dos secciones distintas**, con estilos distintos (tarjetas y filas). Los filtros Todos/Documentos/Fotos solo afectan a los archivos. | Una sola lista: primero las carpetas y después los archivos, con las mismas columnas. |
| D3 | Cada fila muestra **siempre** Descargar, Renombrar y Eliminar: 3 botones × N filas, mucho ruido. | Las acciones salen al pasar el mouse, con clic derecho o en el menú ⋮. |
| D4 | Para renombrar, mover o eliminar una carpeta **hay que entrar a ella**. | Clic derecho sobre la carpeta, desde afuera. |
| D5 | Para mover archivos hay **casillas más un `<select>` fijo** («Mover los archivos marcados a»), visible aunque no haya nada marcado. Las carpetas no se pueden mover junto con los archivos. | Se selecciona (clic, Ctrl o Shift), aparece una barra con las acciones y «Mover a» abre un diálogo para navegar las carpetas. |
| D6 | Renombrar y Mover se abren con un `<details>` en la misma fila, lo que **descuadra la fila** y obliga a usar un `<select>` largo con caminos «A › B › C». | Un diálogo pequeño con el nombre ya seleccionado, sin la extensión. |
| D7 | «Nueva carpeta» es un **campo de texto que está siempre a la vista**, y además hay 3 botones de subida sueltos. | Un solo botón **«+ Nuevo»** con un menú: Carpeta, Subir archivos, Subir carpeta (y aquí, Tomar foto). |
| D8 | Están el botón «← Volver» **y además** las migas de pan, que dicen lo mismo. | Las migas son el título. El último tramo abre las acciones de la carpeta actual. |
| D9 | **No se puede copiar.** | «Hacer una copia» y «Copiar a». |
| D10 | **No se puede previsualizar**: hacer clic en un archivo no hace nada y solo queda descargarlo. | Doble clic abre una vista previa (imágenes y PDF). |
| D11 | No se puede **ordenar** por nombre, fecha o tamaño, no hay **búsqueda** dentro del proyecto ni vista **cuadrícula/lista**. | Hay orden por columna, búsqueda y cambio de vista. |
| D12 | No se puede **arrastrar** un archivo o una carpeta del portal a otra carpeta. Arrastrar solo sirve para subir. | Se arrastra a una carpeta o a un tramo de las migas. |
| D13 | **En el celular**, la cabecera ocupa casi toda la primera pantalla con unos 8 botones apilados antes de ver la primera carpeta. | Barra compacta y un botón flotante «+». |
| D14 | Las acciones no tienen **atajos de teclado** (Supr, F2, Enter, Ctrl+A). | Los tiene. |

Lo que **ya está bien** y se mantiene: la cola de subida con progreso y reintento, arrastrar archivos y carpetas
desde el computador, los tokens de color y tipografía, las confirmaciones con `confirmar.js` y que todo funcione
sin JS (los formularios POST siguen siendo la base).

## Diseño propuesto

### Estructura de la página

```
┌──────────────────────────────────────────────────────────────────────┐
│ ← Empresa de Prueba                                                  │
│ NV 28174 (prueba)  [Finalizado]                    [ⓘ Detalles] [⋯]  │  ⋯ = Editar proyecto, Editar hitos, ZIP
│ ─ Archivos ─  Hitos  Modificaciones                                  │  pestañas (P3)
├──────────────────────────────────────────────────────────────────────┤
│ [+ Nuevo]   NV 28174 › Rev A ▾        [🔍 Buscar en el proyecto] [≡|▦] │  ▾ = acciones de la carpeta actual
│ Todos · Documentos · Fotos                                           │
├──────────────────────────────────────────────────────────────────────┤
│ ☐  Nombre ↑                 Subido por       Fecha        Tamaño   ⋮ │
│ ☐  📁 Detalles              —                14 oct 2026  —        ⋮ │
│ ☐  📄 plano-general.pdf     Personal Prueba  14 oct 2026  2,0 KB   ⋮ │
└──────────────────────────────────────────────────────────────────────┘
 Con algo seleccionado, la barra de arriba cambia a:
│ ✕  2 seleccionados    ⬇ Descargar   ➜ Mover   ⧉ Copiar   ✎ Renombrar   🗑 │
```

### Interacción (Drive en escritorio y adaptada al tacto)

- **Clic** selecciona la fila (Ctrl/Cmd suma o quita, Shift selecciona un rango). **Doble clic o Enter** abre: si
  es una carpeta, entra; si es un archivo, abre la vista previa o lo descarga. En pantallas táctiles, un toque
  abre y la casilla (o mantener presionado) selecciona. (P1)
- **Menú contextual** (clic derecho y botón ⋮): Abrir · Descargar · Renombrar · Mover a… · Hacer una copia ·
  Copiar a… · Eliminar · Detalles. Solo aparece lo que el rol permite, con las mismas funciones de
  `permisos.py` que hoy.
- **Barra de selección:** reemplaza a la barra de herramientas mientras haya algo seleccionado. «Renombrar» solo
  se activa con 1 elemento seleccionado.
- **Diálogo «Mover a» / «Copiar a»:** un `<dialog>` que navega carpeta por carpeta (con «‹ atrás» y las
  subcarpetas del lugar), con el botón «Mover aquí». Las carpetas que no sirven como destino (la propia carpeta,
  sus subcarpetas o una que dejaría más de 8 niveles) aparecen deshabilitadas. El árbol viaja en un
  `<script type="application/json">` hecho con `Arbol`, sin pedidos extra.
- **Arrastrar** elementos del portal a una carpeta o a un tramo de las migas mueve; el destino se resalta (como
  hoy al subir).
- **Teclado:** flechas para moverse, Enter para abrir, F2 para renombrar, Supr para eliminar, Ctrl+A para
  seleccionar todo y Esc para soltar la selección. Foco visible siempre.
- **Vista lista/cuadrícula:** en cuadrícula, las fotos muestran miniatura (P5). La preferencia se guarda en
  `localStorage`.
- **Orden y búsqueda** en el servidor, con parámetros GET (`?orden=-fecha`, `?q=plano`). La búsqueda recorre todo
  el proyecto y muestra en qué carpeta está cada resultado.
- **Panel de detalles (ⓘ):** se desliza desde la derecha. Sin selección muestra los datos del proyecto (fechas y
  encargados, lo que hoy ocupa la cabecera); con un elemento seleccionado muestra su nombre, ubicación, quién lo
  subió y cuándo, y su tamaño.
- **Celular:** barra compacta, un botón flotante «+» con el menú Nuevo (incluye Tomar foto) y la lista sin las
  columnas «Subido por» ni «Tamaño».

### Cómo se construye (respetando lo que ya hay)

- **Sin framework nuevo.** Django sigue armando la página y se agrega un `static/js/explorador.js` en JS puro con
  CSP por nonce, como el resto. Todas las acciones siguen siendo formularios POST con redirección: el JS solo arma
  y envía el formulario (por ejemplo, el de mover con varios ids). **Sin JS**, el cliente sigue navegando y
  descargando con enlaces simples; las acciones del personal (mover, renombrar, eliminar, nueva carpeta) necesitan
  JS, igual que la subida, que ya lo necesitaba.
- **Backend, lo mínimo:**
  - `mover_archivos` (misma URL) ahora recibe `archivos` **y** `carpetas` en el mismo envío, con las validaciones
    de `mover_carpeta` (sin ciclos, 8 niveles, nombre repetido) por carpeta: una carpeta inválida no frena al resto.
  - Campo `desde` en crear, renombrar, mover y eliminar: después de la acción se vuelve a la carpeta donde se
    estaba, como en Drive. Sin `desde`, todo sigue como antes.
  - `copiar_elementos`: para cada archivo usa `storage.copiar` (ya existe, es `copy_object` del Space) y crea un
    `Archivo` nuevo con la clave nueva; las carpetas se copian recursivamente; los nombres repetidos llevan
    «Copia de …» o « (2)», con `nombre_libre`.
  - `eliminar_elementos`: manda varios a la vez a la Papelera (F3). Una carpeta se va con todo lo de adentro y
    `restaurar_elementos` la devuelve con lo que se fue junto con ella (misma hora). Migración 0012: `Carpeta`
    gana `eliminado_en`/`eliminado_por` y la regla de nombre único (C2) ya no cuenta las de la Papelera.
  - Copiar: hasta 200 archivos por vez (cada uno es un `copy_object` dentro del pedido).
  - En `detalle_proyecto`: los parámetros `orden` y `q`, y fecha y autor en las filas de carpeta (`creado_en` y
    `creado_por` ya existen).
- **Vista previa (fase 2):** imágenes y PDF se abren desde la URL prefirmada del Space en un `<dialog>`. Hay que
  sumar `space_host_url` a `img-src` y `frame-src` en la CSP (hoy solo permiten `'self'`) y registrar la vista
  previa en `DescargaLog`, igual que una descarga.
- **Pruebas:** una por endpoint nuevo en `documentos/tests/`, con los mismos casos de permisos que
  `mover_archivos` (cliente → 403, otro proyecto → 404).

## Fases

| Fase | Contenido | Backend |
|---|---|---|
| **F1 · Lista y selección** ✔ | D1, D2, D3, D4, D5, D6, D7, D8, D13: estructura nueva, «+ Nuevo», lista única, selección con barra, menú contextual y diálogos Mover a y Renombrar. Se adelantaron los atajos de teclado de D14. | `mover_archivos` con carpetas, `eliminar_elementos`, `desde` |
| **F2 · Fluidez** ✔ | D11, D12, D14: orden, búsqueda, cuadrícula/lista con miniaturas, arrastrar para mover, atajos de teclado y panel de detalles. | `orden` y `q` en la vista, `img-src` en la CSP |
| **F3 · Copiar y previsualizar** ✔ | D9, D10 y la Papelera con Restaurar (P2). | `copiar_elementos`, CSP y vista previa |

Cada fase va en su propia rama corta desde `origin/main` y con su PR (docs/05). F1 sola ya resuelve la mayor
parte de la queja de que es «enredado».

## Decisiones (19-10-2026)

- **P1. Clic simple → como Drive.** En el computador, un clic selecciona y el doble clic (o Enter) abre. En
  pantallas táctiles, un toque abre y la casilla o mantener presionado selecciona.
- **P2. Eliminar → Papelera (F3).** Lo eliminado (archivos y carpetas con todo su contenido) va a una Papelera del
  proyecto, donde se puede restaurar. Reemplaza a C4 de docs/12. Hasta que llegue F3 sigue valiendo C4.
- **P3. Hitos y Modificaciones → pestañas.** La página del proyecto queda con las pestañas Archivos · Hitos ·
  Modificaciones (con un enlace propio para cada una, `?vista=hitos`, para que funcione sin JS y se pueda
  compartir).
- **P4. Copiar → sí (F3).** «Hacer una copia» y «Copiar a…», con `storage.copiar`.
- **P5. Miniaturas → sí (F2).** En la cuadrícula, las fotos muestran miniatura con URL prefirmada y `loading="lazy"`,
  para pedir al Space solo las que se ven en pantalla. Requiere sumar `space_host_url` a `img-src` en la CSP (pasa
  a F2, antes que la vista previa).
