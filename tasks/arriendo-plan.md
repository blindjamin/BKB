# Plan de implementación: Página de Arriendo de Equipos

> **Spec:** [`docs/10-plan-arriendo-equipos.md`](../docs/10-plan-arriendo-equipos.md) (v3, 28-09-2026)
> **Tareas:** [`tasks/arriendo-todo.md`](arriendo-todo.md)
> `tasks/plan.md` y `tasks/todo.md` son del portal y siguen vigentes. No se mezclan.

## Resumen
La página `/arriendo` es estática: lista 10 equipos en tarjetas `<details>` y usa un script chico para sumar equipos y armar un solo mensaje de WhatsApp. Después se enlaza desde el header y desde la tarjeta de "Qué hacemos".

## Decisiones de arquitectura
- **Datos aparte (`data/arriendo.ts`)**, igual que `data/landing.ts`. La página solo arma el HTML.
- **`<details>`/`<summary>` nativo** en vez de un acordeón en JavaScript: el teclado y el funcionamiento sin JavaScript vienen incluidos.
- **El script va dentro de `arriendo.astro`**, porque solo se usa en esa página. No se crea un componente para un solo uso.
- **Selección en un `Set` en memoria**, sin guardar nada: la spec dice que no se guarda.
- **`mensajeWhatsApp(labels)` es una función pura** dentro del script. Es la única lógica que puede fallar y se verifica mirando el `href`.
- **Para ocultar el botón flotante de WhatsApp**, la página pone una clase en `<html>` (p. ej. `has-cotizacion`) mientras la barra está visible, y una regla CSS oculta `.whatsapp-fab`. No se toca `WhatsAppButton.astro`.

## Orden y dependencias
```
T1 datos ──► T2 página (sin JS) ──► T3 selección + WhatsApp
                                          │
                        T4 link en header ◄┘   (la ruta ya existe: nunca un 404)
                        T5 link en tarjeta "Qué hacemos"
                                          │
                                   T6 documentación
```
T4 y T5 son independientes entre sí y pueden ir en paralelo.

## Riesgos y mitigaciones
| Riesgo | Impacto | Mitigación |
|---|---|---|
| El 7º link no cabe en el header a 1280 px | Medio | Medir en T4. Si no cabe, **preguntar** antes de quitar "Inicio" |
| El carrusel de Servicios clona las tarjetas con `aria-hidden`, pero un `<a>` dentro de un clon sigue recibiendo el foco del teclado | Medio | En T5, poner `inert` a los clones (o `tabindex="-1"` a sus links) |
| `initActiveNav` usa `href.replace(/^.*#/, '')`: con `/arriendo` busca un id que no existe y lo ignora | Bajo | Confirmar que no marca nada por error, y usar `aria-current="page"` en `/arriendo` |
| La barra fija choca con el aviso de emergencia (abajo a la izquierda) | Medio | Revisar a 375 px en T3. Si chocan, la barra sube por encima del aviso o el aviso se oculta con la misma clase |
| Descripciones de uso inventadas | Bajo | Una línea genérica por equipo con `TODO: validar con BKB` |

## Preguntas abiertas
Ninguna.
