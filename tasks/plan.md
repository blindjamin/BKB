# Plan de implementación: Portal de Archivos BKB

> **Spec:** [`docs/03-portal-django.md`](../docs/03-portal-django.md) (aprobada v1.2, 22-09-2026)
> **Tareas con criterios y verificación:** [`tasks/todo.md`](todo.md)
> **Estado:** revisión 3 (22-09-2026), ampliación v1.2 **APROBADA por el usuario (22-09-2026)**. El orden de ejecución está al inicio de `tasks/todo.md`. Ver la sección "Ampliación v1.2" justo abajo; el resto del documento es el plan v1.1, que sigue vigente.
> **Revisión 2 (21-09-2026):** contrastado con el código y git. Se agregó: fusionar la landing antes de la tarea 0, CSP con nonce (tareas 2, 8 y 12), cookies `__Host-` (tarea 2), estáticos de WhiteNoise (tarea 15), `docs/04` en la tarea 17 y la plantilla para darle cada tarea a un agente (inicio de `todo.md`).
> **Cambios de la v1.1:** el cliente solo ve y descarga (no sube) y el personal puede borrar lo que subió. Se eliminó "Compartir con el cliente" y se agregó "Borrar lo propio": **17 tareas**.

## Resumen

Se construye `apps/portal` (Django 5.2 LTS) en **17 tareas pequeñas** (más una de preparación) agrupadas en 4 fases. El orden pone primero lo más riesgoso: las reglas de permiso (que un cliente vea proyectos ajenos es el peor fallo posible) y la conexión real con el Space (CORS y URLs prefirmadas, que fallan por configuración y no por código). La interfaz viene después, sobre reglas ya probadas. El despliegue va al final, cuando todo funciona en tu PC.

## Ampliación v1.2 (22-09-2026)

La spec v1.2 agrega **hitos con aviso y recepción obligatoria** (sección 12) y el **perfil jefe con pantalla de Gestión** (sección 13). Esto suma **11 tareas (18 a 28)**, que se hacen **antes** de la Fase 4 (producción). Las tareas 15 a 17 se mantienen, con criterios ampliados.

### Estado real del código (revisado el 22-09-2026)

| Hallazgo | Consecuencia en el plan |
|---|---|
| La tarea 11 está implementada (`subidas.py`, `test_subida.py`, commit `8cc48af`) pero sin marcar | La tarea 18 la verifica y la marca |
| La tarea 12 tiene `subir.js`, pero la CSP bloquea el botón (hallazgo F4 de `docs/09`) | Se cierra después de la tarea 19 (DS-0) |
| `descargar_archivo` y `eliminar_archivo` deciden con ifs propios, **sin pasar por `permisos.py`** | **Bloqueante:** el bloqueo por recepción vive en `archivos_visibles`; si la descarga no lo usa, el cliente descarga igual por enlace directo. Se corrige en la tarea 18, antes de todo lo demás |
| La CSP no aplica el nonce (`docs/09`, F1 a F5): el aviso emergente, la confirmación de borrado y el botón de subida no funcionan | La tarea 19 es DS-0 de `docs/09` y es requisito de toda interfaz nueva |

### Decisiones de arquitectura (v1.2)

| Decisión | Razón |
|---|---|
| **Estado del proyecto calculado** (`permisos.estado_proyecto`) a partir de `Hito` y `RespuestaRecepcion`, sin campo guardado | Una sola fuente de verdad: no puede quedar "recibido" con hitos sin marcar |
| **El bloqueo se aplica en `archivos_visibles`**, y todas las vistas de archivo lo usan | Listado, descarga y enlace directo quedan cubiertos con un solo cambio, y la matriz de permisos lo prueba |
| **El aviso es un `<dialog>` nativo con JS externo** y el mismo contenido se imprime en la página | Funciona sin JS; la seguridad no depende del aviso |
| **`jefe` es un valor más de `rol`**, y `_es_personal` lo incluye | Todas las reglas del personal se heredan sin copiar código; "un solo jefe activo" se valida en el modelo |
| **Gestión con vistas y formularios de Django** (`ModelForm`), sin librerías | Son 2 listados y 2 formularios; no justifican dependencias |
| **Contraseñas por enlace** con `default_token_generator` y `PasswordResetConfirmView` | Viene con Django, está probado y el jefe nunca conoce contraseñas |
| **Correo por consola** mientras no haya SMTP (`EMAIL_HOST` vacío) | Se prueba el flujo completo sin credenciales; en las pruebas, `mail.outbox` |
| **Un fallo de correo no deshace la acción** (`fail_silently=False` dentro de `try` y registro en el log) | La recepción del cliente o la cuenta nueva no se pierden por un problema de SMTP |
| **Hitos editables con un campo de texto, uno por línea** | Sin JS de "agregar fila" ni formsets; cabe en un solo formulario |

### Grafo de dependencias (v1.2)

```
18 Permisos en todas las vistas ─┬─ 20 Rol jefe ─┬─ 21 Hitos y bloqueo (núcleo) ─┬─ 22 Crear/editar proyecto ─ 23 Marcar hitos ─┐
19 DS-0 CSP ─ (cierra 12) ───────┤               │                               └─ 24 Aviso al cliente ──────────────┤
                                 │               │                                                                    25 Recepción + correo
                                 │               └─ 26 Gestión empresas ─ 27 Gestión usuarios + invitación ─ 28 Olvidé mi contraseña
                                 └─ (19 es requisito de 22 a 28, que tienen interfaz)
                       Checkpoints G (tras 25) y H (tras 28) → Fase 4: 15 → 16 → 17
```

**Orden de trabajo:** 18 → 19 → 12 (cierre) → 20 → 21 → 22 → 23 → 24 → 25 → **G** → 26 → 27 → 28 → **H** → 15 → 16 → 17.
Las tareas 22 a 25 (hitos) y 26 a 28 (gestión) solo comparten la 20 y la 21, así que los bloques podrían ir en otro orden. Se hacen primero los hitos porque son el pedido principal de BKB.

**Diseño (DS-1 a DS-7 de `docs/09`):** no bloquea. Se hace después del checkpoint H y antes de la tarea 16. `docs/09` debe sumar las pantallas nuevas: formulario de proyecto, panel de hitos, aviso, Gestión y creación de contraseña.

### Riesgos nuevos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El cliente descarga archivos bloqueados por enlace directo | **Alto** | Tarea 18 (todas las vistas por `permisos.py`) y matriz con el eje de estado en la 21 |
| El jefe se da privilegios o crea otro jefe o un superusuario | **Alto** | Los formularios de Gestión solo ofrecen `personal` y `cliente`, el servidor lo valida otra vez y las pruebas lo cubren (tarea 27) |
| El correo no llega (sin SMTP o con el puerto 587 bloqueado en App Platform) y no se pueden dar de alta usuarios | Medio | Por consola en local. Antes de la tarea 16 se prueba el SMTP real; si falla, el superusuario puede generar el enlace desde la consola (`manage.py`) |
| El personal marca el último hito por error y el cliente queda bloqueado | Medio | "Retroceder" deshace el último hito mientras no haya recepción conforme |
| Envío repetido de "olvidé mi contraseña" o de "no conforme" como spam | Bajo | Límite simple por IP y correo en la caché (tarea 28). "No conforme" solo lo puede usar un cliente asignado |

### Acciones tuyas (v1.2)

| Antes de | Qué necesito | Dónde |
|---|---|---|
| 25 y 27 (prueba manual) | Nada: el correo sale por consola | — |
| 16 | Contraseña de aplicación de `instrumentacion@empresabkb.cl`, y el correo real del jefe y de los avisos | Google Workspace y el `.env` o App Platform |
| 16 | Designar al jefe en `/admin/` de producción (o que yo te guíe) | Consola de la app |

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
| **6** | Crear una **clave de acceso del Space solo para el portal** (no la personal) y pasarla por `.env`, no por el chat. Hecho el 21-09-2026: tipo Limited, solo `bkb-space`, permiso **Read/Write/Delete** (DigitalOcean no ofrece Read/Write a secas) | Panel de DigitalOcean → Spaces → Access Keys |
| **16** | Crear una **clave distinta** para producción (no reutilizar la de desarrollo), con los mismos ajustes, y cargarla solo en App Platform. Así una filtración se revoca sin afectar a la otra | Panel de DigitalOcean → Spaces → Access Keys |
| **6 y 12** | Agregar **CORS** en `bkb-space` para `http://localhost:8000` (yo te doy la configuración exacta) | Panel de DigitalOcean → Space → Settings |
| **16** | Aprobar el gasto del **PostgreSQL gestionado (≈ US$ 15/mes)** y de la instancia (≈ US$ 12/mes) | Panel de DigitalOcean |
| **17** | Elegir un cliente de confianza y un proyecto de prueba para el piloto | — |

## Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Un cliente ve proyectos que no se le asignaron | **Alto** | Función única + matriz de pruebas (tarea 5) antes de construir cualquier pantalla + 404 uniforme |
| Se sube por error un archivo que el cliente no debía ver, y se ve de inmediato | Medio | Personal capacitado; el autor o el administrador lo borra y el borrado lógico lo oculta al instante; `subido_por` y `eliminado_por` dejan trazabilidad. Si resulta insuficiente, se agrega la marca de visibilidad más adelante |
| POST prefirmado o CORS mal configurados en el Space | Medio | Prueba manual contra el Space real en la tarea 6, antes de tocar la interfaz |
| La clave del Space tiene acceso al bucket completo, incluidos los archivos antiguos, y puede **leer, escribir y borrar** (DigitalOcean no permite quitarle el borrado ni limitarla a un prefijo) | Medio | La protección es solo el código: `storage.py` no tiene funciones para listar ni borrar, valida toda clave contra el prefijo (con pruebas que lo verifican) y el borrado del portal es siempre lógico. Una clave por entorno (desarrollo y producción), guardadas solo en `.env` y en variables de App Platform. Si se sospecha una filtración, se revoca de inmediato en el panel |
| Una sola instancia y sin staging: un despliegue malo afecta a producción | Medio | Todo se prueba en local con `check --deploy`. Despliegue solo desde `main` y por PR. Respaldo diario del PostgreSQL gestionado |
| Una sola persona mantiene el sistema | Medio | Documentación al día en cada tarea (`docs/06`) y la spec (`docs/03`) marcada como implementada en la tarea 17 |
| Django 5.2 con `django-axes` 8 o `django-csp` 4 podría chocar | Bajo | Se comprueba con una instalación limpia en la tarea 1, antes de escribir código |
| Redirección infinita de HTTPS detrás del proxy de DigitalOcean | Bajo | Se corrige en la tarea 2 y se verifica en la 16 |
| Personal sube un archivo malicioso (sin antivirus en la v1) | Bajo | Lista de tipos permitidos, sin ejecutables ni `zip`, descarga siempre como adjunto. Quienes suben son personal de BKB, no el público |
| Subidas cortadas dejan registros `pendiente` huérfanos | Bajo | Nunca se listan. Limpieza periódica queda como seguimiento posterior |

## Seguimiento posterior a la v1 (fuera de este plan)

Subida o solicitud de documentos por parte del cliente (si lo piden), marca interno/compartido (si hace falta), ClamAV, miniaturas y previsualización de fotos, avisos por correo al subir archivos, limpieza automática de subidas pendientes, Google SSO y 2FA, panel de administración propio, y migración ordenada de los archivos antiguos.

## Preguntas abiertas

**Resueltas (21-09-2026):** el único dominio es `empresabkb.cl`, con DNS en DigitalOcean: el portal será `portal.empresabkb.cl` y el registro se crea en la tarea 16 sin depender de terceros. `bkb-space` está en **NYC3** (`SPACES_REGION=nyc3`, `SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com`); la app y el PostgreSQL se crean en NYC3. La landing se fusionó en `desarrollo` (PR #2) y el portal parte de `benjamin/2026-09-21-portal-base`.
