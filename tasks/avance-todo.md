# Tareas: Avance del proyecto, encargados y modificaciones

> Spec: [`docs/11-spec-avance-y-modificaciones.md`](../docs/11-spec-avance-y-modificaciones.md) · Plan: [`avance-plan.md`](avance-plan.md)
> Rama: una por módulo, corta desde `desarrollo` (p. ej. `benjamin/AAAA-MM-DD-portal-encargados`), con PR a `desarrollo`.
> Comandos (desde `apps/portal/`): `.\.venv\Scripts\python.exe manage.py test` · `check` · `makemigrations --check`
> Cada tarea cierra con `test` en verde. Las reglas (E1…M9) son las de la spec.

---

## Módulo 1 · `encargados`

### Tarea 1: Modelo de encargados y visibilidad del cliente
**Descripción:** agregar `Empresa.encargado` (FK, PROTECT), `Proyecto.encargado` (FK, PROTECT) y
`Proyecto.encargados_bkb` (M2M a personal). Eliminar `Membresia` y su inline en el admin. `proyectos_visibles`,
`empresas_visibles`, `puede_ver_empresa` y `proyectos_de_empresa` pasan a usar
`Q(encargado=u) | Q(empresa__encargado=u)`. Adaptar los helpers de las pruebas que creaban membresías.

**Criterios de aceptación:**
- [ ] El encargado de un proyecto lo ve; el encargado de la empresa ve todos los proyectos de su empresa (E1, E6).
- [ ] Un cliente que no es encargado de nada recibe 404 en el proyecto y en la empresa.
- [ ] `Membresia` ya no existe en el modelo, el admin ni las plantillas.

**Verificación:** `test`, `makemigrations --check`. Pruebas nuevas en `documentos/tests/test_encargados.py`.
**Archivos:** `documentos/models.py`, `documentos/permisos.py`, `documentos/admin.py`, migración `0004`, pruebas.

### Tarea 2: Crear empresa con encargado
**Descripción:** nuevo `documentos/encargados.py` con `obtener_o_invitar(request, nombre, email)`, que devuelve
`(usuario, invitado)`. Si el correo no existe, crea un cliente sin contraseña y le envía `enviar_invitacion`. Si
existe y es cliente, lo devuelve sin enviar nada. Si es personal o jefe, lanza `ValidationError` (E5).
`EmpresaForm` suma `encargado_nombre` y `encargado_email`, ambos obligatorios.

**Criterios de aceptación:**
- [ ] Con un correo nuevo se crea un cliente y sale 1 invitación (`mail.outbox`).
- [ ] Con un correo de cliente existente no sale ninguna invitación.
- [ ] Con un correo de personal el formulario muestra un error y no se crea la empresa.
- [ ] Si el correo falla, la empresa queda creada y se muestra un aviso (V6).

**Verificación:** `test` (`test_encargados.py`); en el navegador, crear una empresa y ver la invitación en la consola.
**Archivos:** `documentos/encargados.py`, `documentos/forms.py`, `documentos/views.py`, `templates/empresa_form.html`.

### Tarea 3: Crear proyecto con encargado cliente y encargados BKB
**Descripción:** `ProyectoForm` reemplaza el campo `clientes` por `encargado_nombre`, `encargado_email` (y un botón
"usar el encargado de la empresa" que rellena los dos campos) y `encargados_bkb` (selección múltiple de personal
activo, al menos uno). Usa `obtener_o_invitar`.

**Criterios de aceptación:**
- [ ] El proyecto guarda su encargado y al menos un encargado BKB (E2 y E3).
- [ ] Si el encargado es el mismo de la empresa, no sale otra invitación (E4).
- [ ] Al editar el proyecto, cambiar el encargado por una persona nueva envía la invitación.

**Verificación:** `test`; en el navegador, crear un proyecto.
**Archivos:** `documentos/forms.py`, `documentos/views.py`, `templates/proyecto_form.html`, pruebas.

### Tarea 4: Solo los encargados BKB y el jefe editan
**Descripción:** `permisos.puede_editar_proyecto(u, p)`. Aplicarlo en `editar_proyecto`, `avanzar_hito` y
`retroceder_hito`, y ocultar los botones en la plantilla cuando es falso.

**Criterios de aceptación:**
- [ ] El personal que no está a cargo del proyecto recibe 403 al avanzar, deshacer o editar, y no ve los botones.
- [ ] El jefe puede hacerlo aunque no esté asignado.
- [ ] Todo el personal puede seguir subiendo archivos y creando carpetas.

**Verificación:** `test` (casos en `test_permisos.py`).
**Archivos:** `documentos/permisos.py`, `documentos/views.py`, `templates/archivos.html`, pruebas.

### ◆ Checkpoint 1
- [ ] `test`, `check` y `makemigrations --check` en verde.
- [ ] En el navegador: una empresa y un proyecto nuevos, con las invitaciones correctas en la consola.
- [ ] PR `encargados` → `desarrollo`.

---

## Módulo 2 · `avance`

### Tarea 5: Fechas del proyecto e hitos estándar
**Descripción:** agregar `Proyecto.fecha_inicio`, `fecha_termino` y `finalizado_en`, y `Hito.es_revision`, junto con
`HITOS_ESTANDAR` y `Proyecto.crear_hitos_estandar()`. `ProyectoForm` reemplaza `hitos_texto` por las dos fechas
(`<input type="date">`), y valida que el término no sea anterior al inicio.

**Criterios de aceptación:**
- [ ] Un proyecto nuevo tiene 7 hitos en orden: Compras, Armado, Cableado, Pruebas, Envío, Recepción, Revisión; el
  último con `es_revision=True` (A1).
- [ ] Si la fecha de término es anterior a la de inicio, el formulario muestra un error (A3).

**Verificación:** `test` (`test_avance.py`).
**Archivos:** `documentos/models.py`, migración `0005`, `documentos/forms.py`, `templates/proyecto_form.html`, pruebas.

### Tarea 6: Editar los hitos de un proyecto
**Descripción:** página "Editar hitos" con un formset (nombre, orden y borrar), a la que solo acceden quienes pasan
`puede_editar_proyecto`. Revisión no aparece como editable y siempre queda al final. Un hito cumplido no se puede
borrar. Se puede agregar un hito nuevo.

**Criterios de aceptación:**
- [ ] Se puede cambiar el nombre, reordenar, agregar y quitar hitos pendientes (A2).
- [ ] Revisión no se puede quitar ni mover (sigue siendo el último).
- [ ] Borrar un hito cumplido da error; el personal que no está a cargo recibe 403.

**Verificación:** `test`; en el navegador, editar los hitos.
**Archivos:** `documentos/forms.py`, `documentos/views.py`, `documentos/urls.py`, `templates/hitos_form.html`, pruebas.

### Tarea 7: Avanzar y deshacer con Revisión
**Descripción:** `avanzar_hito` nunca confirma el hito de Revisión (eso lo hace el cliente). `retroceder_hito` queda
bloqueado si el proyecto está finalizado.

**Criterios de aceptación:**
- [ ] Con solo Revisión pendiente, "Avanzar" no hace nada y el botón no aparece (A4 y A5).
- [ ] Se puede deshacer mientras el proyecto no esté finalizado, y nunca después (A6).
- [ ] Cada hito confirmado guarda la fecha y quién lo confirmó.

**Verificación:** `test` (adaptar `test_hitos.py`).
**Archivos:** `documentos/views.py`, `documentos/permisos.py`, `templates/archivos.html`, pruebas.

### Tarea 8: El cliente acepta o rechaza la Revisión
**Descripción:** agregar el modelo `RechazoRevision` y `permisos.puede_responder_cliente`. La vista
`responder_revision` (POST) recibe `aceptar` o `rechazar` más un motivo. Al aceptar, cumple la Revisión a nombre del
cliente y fija `finalizado_en`. Al rechazar, crea un `RechazoRevision`. Eliminar `RespuestaRecepcion`,
`responder_recepcion`, `avisos.enviar_aviso_recepcion`, `ESPERANDO_RECEPCION` y `test_recepcion.py`. Simplificar
`estado_proyecto`.

**Criterios de aceptación:**
- [ ] El encargado del proyecto o el de la empresa puede responder solo cuando los hitos anteriores están cumplidos
  (A5).
- [ ] Al aceptar, el proyecto queda finalizado; al rechazar sin motivo, se muestra un error; al rechazar con motivo,
  queda en el historial y la Revisión sigue pendiente.
- [ ] El personal y los clientes que no son encargados reciben 403.
- [ ] No queda ninguna referencia a `RespuestaRecepcion` (`grep`).

**Verificación:** `test` (`test_avance.py`).
**Archivos:** `documentos/models.py`, migración `0006`, `documentos/permisos.py`, `documentos/views.py`, `documentos/urls.py` (y se borran `avisos.py` y `test_recepcion.py`).

### Tarea 9: Archivos ocultos para el cliente hasta finalizar
**Descripción:** `archivos_visibles` y `archivos_visibles_para` no devuelven nada al cliente mientras
`finalizado_en` sea nulo. Los contadores de las tarjetas usan la misma regla (`_ocultar_conteo_bloqueados` pasa a
basarse en `finalizado_en`).

**Criterios de aceptación:**
- [ ] Antes de finalizar, el cliente recibe 404 al descargar y ve 0 archivos en los contadores; después, 200 (A8).
- [ ] El personal ve siempre todo.

**Verificación:** `test` (adaptar `test_permisos.py` y `test_descarga.py`).
**Archivos:** `documentos/permisos.py`, `documentos/views.py`, pruebas.

### Tarea 10: Vista del cliente: solo el avance
**Descripción:** plantilla `avance.html` para el cliente, con el nombre, la empresa, las fechas destacadas, el
encargado (nombre y correo), la línea de hitos con fecha y quién confirmó cada uno, el formulario de Revisión cuando
corresponde, el historial de rechazos y un espacio vacío para Modificaciones (se llena en T20). Cuando el proyecto
está finalizado, muestra además el acceso a los archivos. El personal sigue en `archivos.html`, con las fechas y los
encargados en la cabecera. Se eliminan `includes/aviso_hitos.html` y el aviso de bloqueo.

**Criterios de aceptación:**
- [ ] El cliente no ve carpetas, filtros ni el botón de subir antes de finalizar (A7).
- [ ] Cumple el diseño del portal (tokens, tema claro y oscuro, móvil de 375 px, WCAG AA).

**Verificación:** `test`; en el navegador (cliente y personal, en móvil y escritorio).
**Archivos:** `templates/avance.html`, `templates/archivos.html`, `documentos/views.py`, estáticos del portal.

### ◆ Checkpoint 2
- [ ] Todo en verde; el recorrido completo como cliente (ver avance → aceptar Revisión → ver archivos).
- [ ] PR `avance` → `desarrollo`.

---

## Módulo 3 · `avisos-proyecto`

### Tarea 11: Base de correos HTML
**Descripción:** `documentos/correos.py` con `enviar(asunto, plantilla, contexto, para, cc=True, adjuntos=())`,
que arma el HTML desde `templates/correos/<plantilla>.html` y el texto desde `.txt`. Nunca lanza errores y devuelve
un booleano. `templates/correos/base.html` lleva la marca de BKB con estilos en línea. Agregar
`AVISO_INGENIERIA_CORREOS` (por defecto con las 2 direcciones de ingeniería) y quitar `AVISO_RECEPCION_CORREOS` de
settings, `.env.example` y `.do/app.yaml`. Pasar la invitación a esta base con `cc=False`.

**Criterios de aceptación:**
- [x] Un correo del proyecto lleva la copia a las 2 direcciones; la invitación no la lleva.
- [x] Una `SMTPException` devuelve False y queda en el log.
- [x] El correo trae la versión HTML y la de texto plano.

**Verificación:** `test` (`test_avisos.py`).
**Archivos:** `documentos/correos.py`, `templates/correos/base.html`, `config/settings.py`, `.env.example`, `gestion/views.py`.

### Tarea 12: Comando `vista_correos`
**Descripción:** `manage.py vista_correos [--dir RUTA]` genera un archivo HTML por plantilla con datos de ejemplo
(sin tocar la base de datos) y muestra las rutas.

**Criterios de aceptación:**
- [x] Genera una muestra de cada correo existente y funciona en una base de datos vacía.

**Verificación:** correrlo y abrir las muestras.
**Archivos:** `documentos/management/commands/vista_correos.py`.

### Tarea 13: Correo de inicio
**Descripción:** al crear el proyecto (después del `atomic`), enviar `inicio` al encargado con copia a ingeniería,
con el nombre, la empresa, las fechas, los hitos y un botón "Ver avance" con la URL absoluta.

**Criterios de aceptación:**
- [x] Crear un proyecto envía 1 correo de inicio (y la invitación, si la persona es nueva) (V2).
- [x] Editar el proyecto no reenvía el correo de inicio.

**Verificación:** `test`.
**Archivos:** `documentos/views.py`, `templates/correos/inicio.html` y `.txt`, pruebas.

### Tarea 14: Correos de término y de rechazo de la Revisión
**Descripción:** al aceptar, enviar `termino` al encargado del proyecto y al de la empresa (sin repetir), con copia
a ingeniería. Asunto: *"Proyecto {nombre} finalizado y aprobado por {cliente}"*. Al rechazar, enviar
`revision_rechazada` a ingeniería con el motivo. Confirmar un hito intermedio no envía nada.

**Criterios de aceptación:**
- [x] Hay 1 correo en cada caso, con los destinatarios correctos (V3, V4 y V5).
- [x] Si el correo falla, la respuesta queda guardada igual.

**Verificación:** `test`.
**Archivos:** `documentos/views.py`, 2 plantillas `.html` y `.txt`, pruebas.

### ◆ Checkpoint 3
- [ ] Correr `vista_correos` y **revisar las muestras con el usuario** antes del módulo 4.
- [ ] PR `avisos-proyecto` → `desarrollo`.

---

## Módulo 4 · `modificaciones`

### Tarea 15: Modelo de modificaciones
**Descripción:** agregar `Modificacion` (con el estado, `enviada_en`, `correos_enviados` y `ultimo_correo_en`) y
`Archivo.modificacion`. Los archivos que pertenecen a una modificación no aparecen en la lista general.
`permisos.modificaciones_visibles(u, p)`: el personal ve todas; el cliente, solo las enviadas.

**Criterios de aceptación:**
- [ ] Los adjuntos de una modificación no se cuentan ni se listan en la sección de archivos.
- [ ] El cliente no ve los borradores.

**Verificación:** `test`, `makemigrations --check` (`test_modificaciones.py`).
**Archivos:** `documentos/models.py`, migración `0007`, `documentos/permisos.py`, `documentos/admin.py`, pruebas.

### Tarea 16: Crear una modificación y adjuntar archivos
**Descripción:** el botón "Añadir modificación" (solo con `puede_editar_proyecto`) abre un formulario con título y
descripción que crea un borrador. En la página del borrador se suben los adjuntos con el flujo actual
(`iniciar_subida` recibe `modificacion_id`) y se pueden quitar mientras siga en borrador.

**Criterios de aceptación:**
- [ ] Solo un encargado BKB o el jefe puede crearla (M1); valen las extensiones de `EXTENSIONES_PERMITIDAS`.
- [ ] No se pueden agregar adjuntos a una modificación ya enviada.

**Verificación:** `test`; en el navegador, subir 2 fotos y un PDF.
**Archivos:** `documentos/modificaciones.py`, `documentos/subidas.py`, `documentos/urls.py`, `templates/modificacion_form.html`, pruebas.

### Tarea 17: Enviar la modificación al cliente
**Descripción:** el botón "Enviar al cliente" fija `enviada_en`, `correos_enviados=1` y `ultimo_correo_en`, y envía
`modificacion` al encargado con copia a ingeniería. Lleva los adjuntos si suman 20 MB o menos (se descargan del
Space con `storage.leer(clave)`) y enlaces si pasan de ese tamaño, más los botones Aprobar y Rechazar con los
enlaces firmados (`firmar_enlace`).

**Criterios de aceptación:**
- [ ] Con 20 MB o menos, el correo trae los archivos; con más, trae enlaces (M2).
- [ ] Los botones apuntan a URLs firmadas distintas para aprobar y para rechazar.
- [ ] Una modificación no se puede enviar dos veces.

**Verificación:** `test` (con el Space simulado, igual que en `test_storage.py`).
**Archivos:** `documentos/modificaciones.py`, `documentos/storage.py`, `templates/correos/modificacion.html` y `.txt`, pruebas.

### Tarea 18: Responder desde el enlace o desde el portal
**Descripción:** `responder_modificacion(token)`. Un GET muestra la modificación con sus adjuntos y un botón para
confirmar ("respondes como {nombre}"). Un POST registra la respuesta (el motivo es obligatorio al rechazar) con el
usuario, la fecha y la IP. Si ya estaba respondida, muestra "ya respondida por X el dd-mm". Si el enlace está
alterado o vencido (30 días), da 404. La misma lógica funciona con sesión iniciada para el encargado del proyecto o
el de la empresa (M5).

**Criterios de aceptación:**
- [ ] **Un GET nunca cambia el estado** (M3).
- [ ] Un enlace alterado, vencido o de otra modificación da 404 (M4).
- [ ] La respuesta es definitiva: un segundo POST no la cambia (M7).
- [ ] La página funciona sin sesión y la protección CSRF sigue activa.

**Verificación:** `test`.
**Archivos:** `documentos/modificaciones.py`, `documentos/urls.py`, `templates/modificacion_responder.html`, `templates/modificacion_respondida.html`, pruebas.

### Tarea 19: Aviso a ingeniería al aprobar y al rechazar
**Descripción:** después de la respuesta, enviar `modificacion_respondida` a ingeniería con el resultado, quién
respondió, la fecha y el motivo si se rechazó.

**Criterios de aceptación:**
- [ ] Hay 1 correo al aprobar y 1 al rechazar (M7).
- [ ] Si el correo falla, la respuesta queda guardada igual.

**Verificación:** `test`.
**Archivos:** `documentos/modificaciones.py`, plantillas `.html` y `.txt`, pruebas.

### Tarea 20: Sección Modificaciones en el panel
**Descripción:** en `avance.html` (cliente) y `archivos.html` (personal), una sección separada de los hitos con cada
modificación: título, estado, fechas, adjuntos descargables y quién respondió. El cliente puede responder ahí mismo
y descargar los adjuntos aunque el proyecto no esté finalizado (excepción a A8, M8).

**Criterios de aceptación:**
- [ ] El cliente descarga los adjuntos de las modificaciones enviadas, pero no los demás archivos.
- [ ] Los borradores solo los ve el personal.

**Verificación:** `test`; en el navegador (cliente y personal).
**Archivos:** `templates/avance.html`, `templates/archivos.html`, `documentos/permisos.py`, `documentos/views.py`, pruebas.

### Tarea 21: Comando `enviar_recordatorios`
**Descripción:** toma las modificaciones pendientes y enviadas con `correos_enviados < 5` y
`ultimo_correo_en <= ahora - 2 días`. Para cada una, reserva el envío con un `UPDATE … WHERE correos_enviados = n`
y manda `modificacion_recordatorio` (con enlaces, sin adjuntos). Si la cuenta llega a 5, envía
`modificacion_sin_respuesta` a ingeniería.

**Criterios de aceptación:**
- [ ] Los correos salen los días 0, 2, 4, 6 y 8, y nunca un sexto (M6).
- [ ] Correr el comando dos veces seguidas envía un solo correo.
- [ ] Una modificación respondida no recibe más correos.

**Verificación:** `test` (con el tiempo simulado).
**Archivos:** `documentos/management/commands/enviar_recordatorios.py`, 2 plantillas, pruebas.

### Tarea 22: Despliegue y documentación
**Descripción:** agregar a `.do/app.yaml` un job `kind: SCHEDULED` diario con `python manage.py enviar_recordatorios`
(confirmar que la cuenta lo tiene disponible; si no, dejar documentado el cron externo). Actualizar el README del
portal, `docs/03` (§12 queda reemplazada por `docs/11`) y `docs/06` (bitácora).

**Criterios de aceptación:**
- [ ] `doctl apps spec validate` aprueba el archivo, o queda anotado como pendiente de la tarea 16.
- [ ] La documentación no menciona la recepción conforme / no conforme como algo vigente.

**Verificación:** revisión de la documentación.
**Archivos:** `.do/app.yaml`, `apps/portal/README.md`, `docs/03-portal-django.md`, `docs/06-bitacora-avances.md`.

### ◆ Checkpoint 4 (final)
- [ ] Los 8 criterios de éxito de la spec quedan demostrados por pruebas.
- [ ] `test`, `check` y `makemigrations --check` en verde.
- [ ] PR `modificaciones` → `desarrollo`.
