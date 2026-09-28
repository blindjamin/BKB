# 10 · Spec: Página de Arriendo de Equipos

> **Estado:** implementada (28-09-2026), pendiente de revisión del usuario. Plan: [`tasks/arriendo-plan.md`](../tasks/arriendo-plan.md) · Tareas: [`tasks/arriendo-todo.md`](../tasks/arriendo-todo.md).
> **Ámbito:** solo `apps/web` (Astro, estático). No toca el portal.

---

## Objetivo
Crear la página `/arriendo`. Muestra los equipos que BKB arrienda (siempre con un técnico de BKB) y permite elegir uno o varios para pedir la cotización de todos juntos en un solo mensaje de WhatsApp. Se llega desde el menú del header.

**Usuario:** jefe de mantención o contratista que necesita una medición o un generador por algunos días y quiere pedir todo de una vez. Fechas, lugar y condiciones se conversan por WhatsApp.

### Decisiones del usuario (28-09-2026)
| Tema | Decisión |
|---|---|
| Contenido | Lista de **tarjetas expandibles**. Cerradas muestran el nombre y un indicador (＋) a la derecha. Abiertas muestran el detalle y un botón para agregar el equipo |
| Selección | Se pueden **sumar varios equipos**. El mensaje de WhatsApp lleva la lista completa |
| Precios | **No** se muestran |
| Modalidad | **Solo con técnico BKB**. Nunca se arrienda solo el equipo |
| Solicitud | WhatsApp al teléfono principal, con el mensaje ya escrito. **Sin campos extra** (fecha, lugar): eso se habla por WhatsApp |
| Condiciones | No se muestra plazo mínimo ni zona de cobertura por ahora |
| Acceso | Link **"Arriendo"** en el menú del header y en `MobileNav` |
| Tarjeta en "Qué hacemos" | **Su texto no cambia** (sigue mencionando alineación láser). Solo se le agrega el enlace a `/arriendo` |

## Equipos
Fuente: tabla entregada por el usuario el 28-09-2026.

| Grupo | Equipo | Modelo |
|---|---|---|
| Instrumentos de medición | Comprobador de instalaciones RIC 19 | Fluke 1674 FC |
| | Analizador trifásico de calidad eléctrica clase A | Fluke 1775 |
| | Pinza de resistencia de tierra | Fluke 1630-2 FC |
| | Comprobador de puesta a tierra avanzado | Fluke 1625-2 |
| | Pinza amperimétrica de procesos | Fluke 773 |
| | Medidor de resistencia de aislamiento | Fluke 1507 |
| | Cámara termográfica | Fluke Ti400 |
| | Pinza amperimétrica | Fluke 376 |
| Generadores | Generador 200 kVA | — |
| | Generador 30 kVA | — |

No se arriendan: equipos de calibración ni de alineación láser.

## Comportamiento
1. **Encabezado:** eyebrow "Arriendo de equipos", título y un párrafo. Debe decir claro que **todo arriendo incluye un técnico BKB** que opera el equipo.
2. **Lista:** una tarjeta por equipo, en dos grupos: "Instrumentos de medición" y "Generadores".
   - **Cerrada:** nombre del equipo, el modelo en texto chico y un ícono ＋ a la derecha que rota a × al abrir.
   - **Abierta:** una línea que dice para qué sirve y un botón **"Agregar a la cotización"**. Si ya está agregado, cambia a **"✓ Agregado · Quitar"**.
   - Se hace con `<details>`/`<summary>` nativo, así que abre y cierra con teclado y sin JavaScript.
   - La tarjeta agregada queda marcada aunque esté cerrada (borde salmón y un ✓ junto al nombre).
3. **Barra de cotización:** fija abajo. Aparece cuando hay al menos un equipo agregado.
   - Muestra "N equipos seleccionados", la lista con opción de quitar cada uno y el botón **"Cotizar por WhatsApp"**.
   - Mensaje generado:
     ```
     Hola, quisiera cotizar el arriendo con técnico BKB de:
     - Analizador trifásico de calidad eléctrica clase A (Fluke 1775)
     - Generador 200 kVA
     ```
   - Cuando la barra está visible, el botón flotante de WhatsApp se oculta en esta página para que no se tapen.
4. **Sin JavaScript:** las tarjetas abren igual, los botones de agregar no se muestran (van bajo `html.js`) y un botón de WhatsApp general permite cotizar igual.
5. **Cierre:** "¿Necesitas otro equipo o servicio?", con WhatsApp general y un link a `/#cotizar`.
6. **La selección no se guarda:** si se recarga la página, se pierde. No hace falta guardarla para una lista de 10 equipos.

## Supuestos
1. La ruta es `/arriendo`, con `Layout` y `headerMode="solid"`.
2. El WhatsApp usa `SITE.phoneHref` y el mismo armado `wa.me` de `WhatsAppButton.astro`.
3. Las descripciones de uso las redacto yo a partir del tipo de equipo (p. ej. "Mide armónicos, factor de potencia y consumo en redes trifásicas"). Van con `TODO: validar con BKB`. No se inventan especificaciones técnicas.
4. No se muestran fotos por ahora.

## Tech Stack
Astro 5 (salida estática), Tailwind CSS v4 con `@bkb/tokens`, TypeScript y JavaScript vanilla en un `<script>` de la página. Sin dependencias nuevas.

## Commands
```bash
npm run dev:web                         # desde bkb-platform/, puerto 3000
npm run build:web
GITHUB_PAGES=true npm run build:web     # verifica la base /BKB
```

## Project Structure (archivos que se tocan)
```
apps/web/src/data/arriendo.ts                   NUEVO: grupos y equipos (id, nombre, modelo, uso)
apps/web/src/pages/arriendo.astro               NUEVO: página, tarjetas, barra y un <script> chico
apps/web/src/components/site/SiteHeader.astro   + link "Arriendo" en navLinks
apps/web/src/components/landing/Services.astro  la tarjeta Arriendo enlaza a /arriendo (texto sin cambios)
docs/02-sitio-web-astro.md                      + /arriendo en el mapa de rutas
docs/06-bitacora-avances.md                     + entrada; se quita "calibración" de la línea 143
```
`MobileNav` recibe `navLinks` por prop, así que hereda el link sin cambios. El script vive en la página porque solo se usa ahí.

## Code Style
```ts
// data/arriendo.ts
export interface EquipoArriendo { id: string; nombre: string; modelo?: string; uso: string; }
export const gruposArriendo: { titulo: string; equipos: EquipoArriendo[] }[] = [
  { titulo: 'Instrumentos de medición', equipos: [
    { id: 'fluke-1775', nombre: 'Analizador trifásico de calidad eléctrica clase A', modelo: 'Fluke 1775', uso: '…' },
  ]},
];
```
```astro
<details class="equipo" data-id={e.id} data-label={e.modelo ? `${e.nombre} (${e.modelo})` : e.nombre}>
  <summary>…nombre… <span aria-hidden="true">＋</span></summary>
  <p>{e.uso}</p>
  <button type="button" class="js-only" aria-pressed="false">Agregar a la cotización</button>
</details>
```
- El estado es un `Set` de ids en memoria. El `href` del botón se vuelve a armar con `encodeURIComponent` en cada cambio, mediante una función pura `mensajeWhatsApp(labels: string[])`.
- `getPath()` en todo enlace, solo utilidades de tokens, contraste AA (texto blanco sobre `salmon-700`).
- El botón de agregar usa `aria-pressed`. El contador de la barra va en `aria-live="polite"`.
- Se oculta el marcador nativo de `<summary>`. El ícono gira con `transform`, sin animación bajo `prefers-reduced-motion`.

## Testing Strategy
El sitio no tiene tests automáticos y no se monta un framework para una página estática. Verificación en el navegador y con build:
1. Ambos builds pasan y existe `dist/arriendo/index.html`.
2. Agregar 0, 1 y 3 equipos. Con 0, la barra no se ve. Con 1 y 3, el texto de `wa.me/56961911593?text=` decodificado lleva exactamente esos equipos, en el orden de la lista.
3. Quitar un equipo desde la tarjeta y desde la barra: el mensaje se actualiza.
4. Teclado: Tab llega a cada `summary`, Enter o Espacio la abre, y Tab llega al botón de agregar. Con JavaScript desactivado, las tarjetas abren y el WhatsApp general funciona.
5. Claro, oscuro, 375 px sin scroll horizontal, y la barra no tapa el último equipo ni choca con el aviso de emergencia.
6. Header a 1280 px: los 7 links caben. Si no caben, se propone quitar "Inicio" (el logo ya lleva al inicio) y se pregunta antes de hacerlo.

## Boundaries
- **Siempre:** `getPath()`, tokens, título y metadescripción propios, AA, que funcione con teclado.
- **Preguntar antes:** mostrar precios, agregar fotos, agregar campos (fecha, lugar), guardar la selección, cambiar el texto de la tarjeta de "Qué hacemos", quitar links del header, agregar un backend o una dependencia.
- **Nunca:** inventar especificaciones técnicas, ofrecer arriendo sin técnico, listar calibración o alineación láser en el arriendo, ni crear un `<form>` sin `method`.

## Success Criteria
- [ ] "Arriendo" está en el menú de escritorio y en el del celular, lleva a `/arriendo` y queda con `aria-current="page"` en esa página.
- [ ] Se ven los 10 equipos en 2 grupos, cada uno como tarjeta expandible con ＋ a la derecha.
- [ ] Se pueden agregar y quitar varios equipos, y el mensaje de WhatsApp lista exactamente los seleccionados.
- [ ] La página deja claro que el arriendo incluye técnico BKB y no muestra precios.
- [ ] La tarjeta "Arriendo de Equipos" de la landing enlaza a `/arriendo`, con su texto intacto.
- [ ] Sin JavaScript, la página sigue siendo útil.
- [ ] Ambos builds pasan. Se ve bien en claro, oscuro, 375 px y con teclado.

## Open Questions
Ninguna. Las respuestas del 28-09-2026 cerraron todas: el amarillo de la 1630-2 FC no significa nada, la tarjeta de la landing no se toca, no hay campos extra y no se muestran condiciones.
