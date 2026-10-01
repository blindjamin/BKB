# 06 · Bitácora de Avances

> Memoria de trabajo para el equipo y para cualquier IA que retome el proyecto. Cada sesión cierra con una entrada corta y el punto de partida. El detalle de las sesiones 1 a 13 se condensó el 01-10-2026; la versión completa está en el historial de git.

---

## Resumen de las sesiones 1 a 13 (14 al 29 de septiembre de 2026)

| Fecha | Qué se hizo |
|---|---|
| 14-09 | Monorepo (`npm workspaces`), tokens, documentación en `docs/` y flujo de ramas `main` → `desarrollo` → ramas de tarea. GitHub Pages desde `desarrollo`. |
| 15-09 | Rediseño de la landing según el handoff de Claude Design: tokens v2 y temas oscuro y claro. |
| 20 y 21-09 | Spec del portal (`docs/03`) v1 y v1.1: el cliente solo ve, el personal sube y borra lo propio. Ajustes de la landing: hero, logos, "Qué hacemos" en carrusel. Se confirmó que `empresabkb.cl` es la fuente verificada de contenido. |
| 22-09 | Portal v1.2 (hitos, recepción y jefe) y v1.3 (empresas → proyectos → carpetas). |
| 23 a 25-09 | Tareas 23 a 28 (carpetas, hitos, gestión con invitación, "olvidé mi contraseña"), diseño DS-1 a DS-7 y tarea 15 (código listo para App Platform). Se anotaron 3 alertas de seguridad por decidir. |
| 25-09 | Landing: piezas tomadas de la rama de Lisandro (header "Soy cliente", aviso de emergencia, testimonios provisorios, contacto con mapa, teléfonos confirmados). PR #9. |
| 28-09 | Página `/arriendo`: 10 equipos, cotización de varios por WhatsApp. |
| 29-09 | Spec `docs/11` y sus 4 módulos (encargados, avance, avisos y modificaciones), que reemplazan la recepción conforme. Tema claro grafito y naranjo en portal y landing. Formulario "Cotizar obra" de la landing → `/cotizar/` del portal → `ingenieria@empresabkb.cl`. Fotos reales en servicios. PR #15 a #20 a `desarrollo` y PR #21 a `main`. |

---

## Sesión 14 · 1 de Octubre de 2026 (limpieza de documentación)

### Resumen
- README principal, `docs/00`, `01`, `02`, `03`, READMEs del portal, de la web y de tokens al día con el estado actual.
- Se borraron los planes ya cumplidos: `docs/08` (rediseño de la landing), `docs/09` (diseño del portal), `docs/10` (arriendo), `docs/design/handoff-landing/`, `tasks/plan.md`, `tasks/avance-*` y `tasks/arriendo-*`. `docs/03` §12 apunta a `docs/11`.
- `tasks/todo.md` pasa a ser la lista única de pendientes.

### Punto de partida
`tasks/todo.md` §1: decidir las 3 alertas de seguridad; después, la verificación manual y la tarea 16.
