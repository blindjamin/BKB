# Plan de implementación: Portal de Archivos BKB

> **Spec:** [`docs/03-portal-django.md`](../docs/03-portal-django.md) (aprobada v1.1, 21-09-2026)
> **Tareas con criterios y verificación:** [`tasks/todo.md`](todo.md)
> **Estado:** BORRADOR pendiente de revisión del usuario · 21-09-2026 (revisión 2)
> **Revisión 2 (21-09-2026):** contrastado con el código y git. Se agregó: fusionar la landing antes de la tarea 0, CSP con nonce (tareas 2, 8 y 12), cookies `__Host-` (tarea 2), estáticos de WhiteNoise (tarea 15), `docs/04` en la tarea 17 y la plantilla para darle cada tarea a un agente (inicio de `todo.md`).
> **Cambios de la v1.1:** el cliente solo ve y descarga (no sube) y el personal puede borrar lo que subió. Se eliminó "Compartir con el cliente" y se agregó "Borrar lo propio": **17 tareas**.

## Resumen

Se construye `apps/portal` (Django 5.2 LTS) en **17 tareas pequeñas** (más una de preparación) agrupadas en 4 fases. El orden pone primero lo más riesgoso: las reglas de permiso (que un cliente vea proyectos ajenos es el peor fallo posible) y la conexión real con el Space (CORS y URLs prefirmadas, que fallan por configuración y no por código). La interfaz viene después, sobre reglas ya probadas. El despliegue va al final, cuando todo funciona en tu PC.

## Decisiones de arquitectura

| Decisión | Razón |
|---|---|
| **Dos tipos de usuario: personal y cliente.** El administrador es el superusuario de Django, no un rol del portal | El personal sube y ve todo. El cliente solo lee. Menos casos que probar y menos código de permisos |
| **Sin marca interno/compartido:** todo archivo disponible se ve de inmediato para quien accede al proyecto | Lo sube solo personal capacitado. Se elimina un campo, una regla en cada consulta y una tarea completa |
| **`Membresia` solo para clientes.** El personal ve todos los proyectos | Cada proyecto nuevo no obliga a asignar al personal uno por uno |
| **Permisos en una sola función** (`permisos.py`) y vistas que usan `get_object_or_404` sobre su resultado | "No existe" y "no tienes permiso" se ven igual (404): el cliente no descubre proyectos ajenos. Si algún día el cliente pudiera subir, el cambio se concentra ahí |
| **Usuario personalizado antes del primer `migrate`** (tarea 3) | Cambiarlo después obliga a rehacer la base de datos |
| **Archivos van navegador ↔ Space**, Django solo firma URLs | El servidor no procesa contenido ajeno y una instancia chica alcanza. Un DWG de 50 MB subido a través del servidor bloquearía las descargas de los clientes |
| **Subida con POST prefirmado** y `content-length-range` | El límite de tamaño lo aplica el Space, no solo el portal |
| **Estado `pendiente` → `disponible`** al confirmar | Una subida cortada a medias nunca aparece en listados |
| **Borrado lógico, por su autor o por el administrador** | El personal borra lo que subió (corrige un error) y el administrador borra cualquiera. El archivo se oculta al instante para todos y se registra quién lo borró |
| **Claves del Space solo con UUID + prefijo** (`portal/`, `portal-dev/`) | Ninguna ruta viene del usuario y el portal no puede tocar lo antiguo |
| **CSS propio con tokens copiados** a `apps/portal/static/tokens/` | App Platform desplegará solo `apps/portal`, sin acceso a `packages/tokens`. Se copia con un comando documentado |
| **CSP estricta desde la tarea 2** (`django-csp`, sin `unsafe-inline`; nonce para el script del tema y solo el endpoint del Space en `connect-src`/`form-action`) | `docs/04` la exige, y agregarla al final rompería pantallas ya hechas. Se abre solo lo que cada tarea necesita |
| **`manage.py test`**, sin pytest | Sin dependencias nuevas. Reversible: pytest ejecuta esas mismas pruebas |
| **SQLite en local, PostgreSQL en producción** vía `DATABASE_URL` | Se conecta en la tarea 15, no bloquea el desarrollo |

## Grafo de dependencias

```
1 Entorno ─ 2 Settings ─ 3 Usuario ─ 4 Modelos ─┬─ 5 Permisos ────────────┐
                              │                 └─ 6 Space ───────────────┤
                              └─ 7 Login ─ 8 Base visual ─ 9 Proyectos ─ 10 Archivos ─┬─ 11 Subida (servidor) ─ 12 Subida (interfaz)
                                                                                       ├─ 13 Descarga
                                                                                       └─ 14 Borrar lo propio
                                            12, 13 y 14 ─ 15 Prod (código) ─ 16 Prod (DO) ─ 17 Piloto y docs
```

Se hace una tarea a la vez (una sola persona). Lo único paralelizable es la documentación.

## Lista de tareas (índice; el detalle está en `tasks/todo.md`)

### Fase 1 · Base
0. Rama de trabajo
1. Entorno y dependencias
2. Endurecer `settings.py`

### Fase 2 · Núcleo: datos, permisos y Space
3. Usuario con tipo (personal o cliente)
4. Modelos de dominio y panel de administración
5. Permisos y matriz de pruebas
6. Conexión con el Space

**Checkpoint A (tras 5) · Checkpoint B (tras 6)**

### Fase 3 · Lo que ve el usuario
7. Login, logout y bloqueo por intentos
8. Base visual y tema claro/oscuro
9. Lista de proyectos
10. Archivos de un proyecto
11. Subida: servidor
12. Subida: interfaz

**Checkpoint C (tras 12)**

13. Descarga con registro
14. Borrar lo propio

**Checkpoint D (tras 14)**

### Fase 4 · Producción
15. Código listo para producción
16. Puesta en marcha en DigitalOcean
17. Piloto y documentación

**Checkpoint E (tras 16) · Checkpoint F: v1 terminada**

## Acciones tuyas que desbloquean tareas

| Antes de la tarea | Qué necesito de ti | Dónde |
|---|---|---|
| **6** | Crear una **clave de acceso del Space solo para el portal** (no la personal) y pasarla por `.env`, no por el chat | Panel de DigitalOcean → Spaces → Access Keys |
| **6 y 12** | Agregar **CORS** en `bkb-space` para `http://localhost:8000` (yo te doy la configuración exacta) | Panel de DigitalOcean → Space → Settings |
| **16** | Aprobar el gasto del **PostgreSQL gestionado (≈ US$ 15/mes)** y de la instancia (≈ US$ 12/mes) | Panel de DigitalOcean |
| **16** | Saber quién administra el **DNS de `bkb.cl`** para crear `portal.bkb.cl` | Proveedor del dominio |
| **17** | Elegir un cliente de confianza y un proyecto de prueba para el piloto | — |

## Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Un cliente ve proyectos que no se le asignaron | **Alto** | Función única + matriz de pruebas (tarea 5) antes de construir cualquier pantalla + 404 uniforme |
| Se sube por error un archivo que el cliente no debía ver, y se ve de inmediato | Medio | Personal capacitado; el autor o el administrador lo borra y el borrado lógico lo oculta al instante; `subido_por` y `eliminado_por` dejan trazabilidad. Si resulta insuficiente, se agrega la marca de visibilidad más adelante |
| POST prefirmado o CORS mal configurados en el Space | Medio | Prueba manual contra el Space real en la tarea 6, antes de tocar la interfaz |
| La clave del Space tiene acceso al bucket completo, incluidos los archivos antiguos | Medio | El código solo construye claves con UUID + prefijo, no lista ni borra, y hay pruebas que lo verifican. Clave dedicada, guardada solo en variables de entorno |
| Una sola instancia y sin staging: un despliegue malo afecta a producción | Medio | Todo se prueba en local con `check --deploy`. Despliegue solo desde `main` y por PR. Respaldo diario del PostgreSQL gestionado |
| Una sola persona mantiene el sistema | Medio | Documentación al día en cada tarea (`docs/06`) y la spec (`docs/03`) marcada como implementada en la tarea 17 |
| Django 5.2 con `django-axes` 8 o `django-csp` 4 podría chocar | Bajo | Se comprueba con una instalación limpia en la tarea 1, antes de escribir código |
| Redirección infinita de HTTPS detrás del proxy de DigitalOcean | Bajo | Se corrige en la tarea 2 y se verifica en la 16 |
| Personal sube un archivo malicioso (sin antivirus en la v1) | Bajo | Lista de tipos permitidos, sin ejecutables ni `zip`, descarga siempre como adjunto. Quienes suben son personal de BKB, no el público |
| Subidas cortadas dejan registros `pendiente` huérfanos | Bajo | Nunca se listan. Limpieza periódica queda como seguimiento posterior |

## Seguimiento posterior a la v1 (fuera de este plan)

Subida o solicitud de documentos por parte del cliente (si lo piden), marca interno/compartido (si hace falta), ClamAV, miniaturas y previsualización de fotos, avisos por correo al subir archivos, limpieza automática de subidas pendientes, Google SSO y 2FA, panel de administración propio, y migración ordenada de los archivos antiguos.

## Preguntas abiertas

- **Dominio del portal:** en DigitalOcean el dominio es `empresabkb.cl` (con su DNS gestionado ahí), no `bkb.cl`. ¿El portal será `portal.empresabkb.cl`? Hoy la spec y el plan dicen `portal.bkb.cl`.

**Resueltas (21-09-2026):** `bkb-space` está en **NYC3** (`SPACES_REGION=nyc3`, `SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com`); la app y el PostgreSQL se crean en NYC3. La landing se fusionó en `desarrollo` (PR #2) y el portal parte de `benjamin/2026-09-21-portal-base`.
