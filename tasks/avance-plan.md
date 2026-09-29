# Plan: Avance del proyecto, encargados y modificaciones

> Spec: [`docs/11-spec-avance-y-modificaciones.md`](../docs/11-spec-avance-y-modificaciones.md) (v1.0 aprobada) ·
> Tareas: [`avance-todo.md`](avance-todo.md)
> Todos los comandos se corren desde `apps/portal/` con `.\.venv\Scripts\python.exe manage.py <comando>`.

## Enfoque

Hay cuatro módulos que se construyen en orden: **encargados → avance → avisos-proyecto → modificaciones**. Cada
módulo es un PR hacia `desarrollo` y termina con un checkpoint (pruebas en verde y una revisión en el navegador).
Cada tarea es una pieza vertical: modelo, permisos, vista, plantilla y prueba de una sola regla, y el portal sigue
funcionando al terminarla.

Como no hay datos reales, cada módulo agrega **una sola migración** con campos obligatorios sin valor por defecto.
Las migraciones anteriores no se tocan.

## Decisiones técnicas

| Tema | Decisión | Por qué |
|---|---|---|
| Personas | `Empresa.encargado` y `Proyecto.encargado` son FK a `Usuario`; `Proyecto.encargados_bkb` es M2M. `Membresia` se elimina. | E1, E2, E3 y E6. Dos relaciones directas son más simples que una tabla de asignaciones. |
| Crear o encontrar a una persona | Una sola función, `encargados.obtener_o_invitar(request, nombre, email)`, que usan la empresa y el proyecto. | E4 y E5 en un solo lugar. Reutiliza `gestion.views.enviar_invitacion`. |
| Quién edita | `permisos.puede_editar_proyecto(u, p)`: es el jefe o está en `encargados_bkb`. | E3. Subir archivos y crear carpetas sigue abierto a todo el personal (`puede_gestionar_estructura`). |
| Quién responde como cliente | `permisos.puede_responder_cliente(u, p)`: cliente activo que es el encargado del proyecto o el de su empresa. | A5 y M5. |
| Estado del proyecto | "Finalizado" es `finalizado_en IS NOT NULL`. `estado_proyecto` y `EstadoFlujoProyecto` se simplifican a `en_curso` y `finalizado`. | A5, A6 y A9. Sin estado duplicado. |
| Hitos estándar | Constante `HITOS_ESTANDAR` en `models.py`. Se crean en `Proyecto.crear_hitos_estandar()` al crear el proyecto. | A1. El editor global queda fuera de esta versión. |
| Editor de hitos | Formset de Django sobre `Hito` (nombre y orden, con opción de borrar). Revisión va fija al final y no se puede editar ni borrar. Un hito cumplido no se puede borrar. | A2. Sin JavaScript nuevo. |
| Correos | `documentos/correos.py` con `enviar(asunto, plantilla, contexto, para, cc=True, adjuntos=())`, que usa `EmailMultiAlternatives` con HTML y texto plano, nunca lanza errores y devuelve un booleano. | V1 y V6. Reemplaza a `avisos.py`. |
| Copia a ingeniería | `settings.AVISO_INGENIERIA_CORREOS` reemplaza a `AVISO_RECEPCION_CORREOS`. **Las invitaciones no llevan esa copia** (`cc=False`), porque tienen un enlace para crear contraseña. | V1. Ajuste a la spec (ver abajo). |
| Adjuntos de una modificación | Usan `Archivo` con la FK `modificacion` y la subida directa al Space que ya existe. La modificación nace como **borrador** y se envía con el botón "Enviar al cliente" cuando los adjuntos ya están arriba. | M1 y M2. La subida es asíncrona en el navegador, así que el correo no puede salir al crear la modificación. |
| Enlace del correo | `TimestampSigner(salt='modificacion')` sobre `"<mod_pk>:<user_pk>"`, con `max_age` de 30 días. GET muestra y POST responde. | M3 y M4. Sin tabla de tokens. |
| Recordatorios | Comando que se puede correr varias veces sin duplicar, con `UPDATE … WHERE correos_enviados = n` (bloqueo optimista) para que dos ejecuciones no envíen el mismo correo. | M6. |

### Ajustes a la spec (ya aplicados en docs/11)

1. **V1:** la copia a ingeniería va en los correos **del proyecto**, no en la invitación.
2. **M1:** la modificación tiene un paso de **borrador → enviada** (campo `enviada_en`). Los recordatorios cuentan
   desde el envío, no desde la creación.

## Orden y dependencias

```
encargados:      T1 modelo + permisos ─► T2 empresa ─► T3 proyecto ─► T4 quién edita
                                                                          │  ◆ Checkpoint 1
avance:          T5 fechas + hitos estándar ─► T6 editor de hitos
                 T7 avanzar/deshacer ─► T8 Revisión del cliente ─► T9 archivos ocultos ─► T10 vista del cliente
                                                                          │  ◆ Checkpoint 2
avisos-proyecto: T11 base de correos ─► T12 vista_correos ─► T13 inicio ─► T14 término y rechazo
                                                                          │  ◆ Checkpoint 3 (revisar correos con el usuario)
modificaciones:  T15 modelo ─► T16 crear y adjuntar ─► T17 enviar correo ─► T18 enlace y respuesta
                 ─► T19 aviso a ingeniería ─► T20 sección en el panel ─► T21 recordatorios ─► T22 despliegue y docs
                                                                          │  ◆ Checkpoint 4 (final)
```

Dentro de cada módulo el orden es estricto. T6 y T7 se pueden hacer en paralelo, igual que T12 y T13.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Quitar `Membresia` rompe muchas pruebas actuales (fixtures en 8 o más archivos). | Alto en T1 | T1 cambia primero los helpers de las pruebas. Las pruebas de recepción (`test_recepcion.py`) se borran en T8 junto con el modelo. |
| El puerto 587 está bloqueado en App Platform o el SMTP no está conectado. | Ningún correo sale en producción | Queda fuera de esta spec. Se verifica en la tarea 16 del portal. Mientras tanto, la consola en local y `locmem` en las pruebas. |
| App Platform no tiene trabajos programados en la cuenta. | No hay recordatorios | El comando no depende de App Platform: sirve igual con un cron externo. Se confirma en T22. |
| Un correo reenviado deja responder a otra persona. | Respuesta de alguien que no es el encargado | Se registran la IP y el usuario del enlace, y la página muestra "respondes como {nombre}". Se acepta este riesgo, avisándole al usuario. |
| Descargar adjuntos del Space para enviarlos pesa en memoria o demora. | Una request lenta en "Enviar" | Tope de 20 MB; si se pasa, van enlaces. Se descarga solo al enviar. Los recordatorios llevan enlaces, no adjuntos. |
| Los antivirus de correo abren los enlaces. | Aprobación accidental | Un GET nunca cambia el estado (M3), y hay una prueba que lo exige. |

## Checkpoints

1. **Encargados:** `test`, `check` y `makemigrations --check` en verde. En el navegador: crear una empresa con un
   correo nuevo (la invitación aparece en la consola) y un proyecto con el mismo encargado (sin invitación nueva).
2. **Avance:** entrar como cliente, ver solo el avance, aceptar la Revisión y ver aparecer los archivos. El
   personal que no está a cargo recibe 403 al avanzar un hito.
3. **Avisos:** revisar con el usuario las muestras de `vista_correos` antes de seguir.
4. **Final:** los 8 criterios de éxito de la spec quedan demostrados por pruebas. Se actualizan `docs/03` (§12 queda
   reemplazada), `docs/06` (bitácora) y el README del portal.
