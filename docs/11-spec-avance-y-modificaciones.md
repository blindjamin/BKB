# 11 · Spec: Avance del proyecto, encargados y modificaciones

> **Estado:** APROBADA v1.0 (29-09-2026). Reemplaza en el portal el flujo de
> "recepción conforme / no conforme" (docs/03 §12) y el acceso del cliente a los archivos durante el proyecto.
> El portal no está en producción ni tiene datos reales: el modelo se puede cambiar sin migrar datos.

## Objetivo

Hoy el cliente entra al portal a ver archivos. Con este cambio, **durante el proyecto el cliente solo ve el avance**:
el nombre del proyecto, las fechas de inicio y término, el encargado cliente, una lista fija de hitos con la fecha y
quién confirmó cada uno, y las modificaciones que BKB le propone. Los archivos pasan a ser internos hasta que el
cliente acepta la Revisión final.

La comunicación va por correo, siempre con copia a ingeniería:

- se avisa al crear el proyecto y al terminarlo;
- cada modificación llega con su texto y sus adjuntos, se aprueba o rechaza desde el mismo correo y se recuerda
  cada 2 días hasta que haya respuesta.

## Mapa de módulos

| Módulo | Qué hace | Depende de |
|---|---|---|
| `encargados` | Encargado de empresa, encargado cliente del proyecto y encargados BKB. Invitación con contraseña solo para personas nuevas. | — |
| `avance` | Hitos estándar editables, fechas, vista del cliente solo con el avance, Revisión aceptada o rechazada por el cliente, archivos ocultos hasta el final. | encargados |
| `avisos-proyecto` | Correos HTML de inicio, de término y de rechazo de la Revisión, con copia fija a ingeniería. | avance |
| `modificaciones` | BKB crea una modificación con texto y adjuntos. El cliente responde desde el correo o desde el portal. Recordatorios con tope y aviso a ingeniería. | avance, avisos-proyecto |

**Orden de construcción:** encargados → avance → avisos-proyecto → modificaciones. Cada módulo se entrega en su
propia rama y en su propio PR hacia `desarrollo`.

---

## Módulo `encargados`

### Reglas

- **E1.** Al crear una empresa se indica su **encargado** (nombre y correo), que es obligatorio. El encargado de la
  empresa **ve todos los proyectos de su empresa** y puede aprobar y rechazar en nombre del encargado del proyecto
  (la Revisión y las modificaciones).
- **E2.** Al crear un proyecto se indica **un encargado cliente** (nombre y correo), que es obligatorio. Puede ser el
  mismo encargado de la empresa o una persona distinta.
- **E3.** Al crear un proyecto se indican uno o más **encargados BKB** (usuarios del personal). Solo ellos y el jefe
  pueden confirmar y deshacer hitos, editar los hitos y las fechas del proyecto y crear modificaciones. El resto del
  personal ve el proyecto, pero no puede hacer cambios en él.
- **E4.** Si el correo indicado **no existe**, se crea un usuario cliente sin contraseña y se le envía la invitación
  actual (enlace de un solo uso que vence en 3 días, `gestion.views.enviar_invitacion`). Si **ya existe** como
  cliente, no se le envía la invitación porque ya tiene contraseña.
- **E5.** Si el correo pertenece a alguien del personal o al jefe, el formulario muestra un error: un encargado
  cliente tiene que ser un cliente.
- **E6.** Un cliente ve los proyectos de los que es encargado y todos los proyectos de las empresas de las que es
  encargado. `Membresia` desaparece y la reemplazan estas dos relaciones.

### Modelo

```python
class Empresa(models.Model):
    ...
    encargado = models.ForeignKey(AUTH_USER_MODEL, on_delete=PROTECT, related_name='empresas_a_cargo')

class Proyecto(models.Model):
    ...
    encargado = models.ForeignKey(AUTH_USER_MODEL, on_delete=PROTECT, related_name='proyectos_a_cargo')
    encargados_bkb = models.ManyToManyField(AUTH_USER_MODEL, related_name='proyectos_bkb')
```

`permisos.proyectos_visibles(cliente)` pasa a ser
`Proyecto.objects.filter(Q(encargado=u) | Q(empresa__encargado=u))`.

---

## Módulo `avance`

### Reglas

- **A1.** Al crearse, todo proyecto recibe los hitos estándar en este orden: **Compras, Armado, Cableado, Pruebas,
  Envío, Recepción, Revisión**. La lista vive en una constante (`HITOS_ESTANDAR`).
- **A2.** Un encargado BKB o el jefe puede cambiar el nombre de un hito, agregarlo, quitarlo o reordenarlo en su
  proyecto. **Revisión siempre es el último hito y no se puede quitar**, porque es el que acepta el cliente.
- **A3.** El proyecto tiene `fecha_inicio` y `fecha_termino`, obligatorias desde que se crea. Son informativas: no
  generan avisos, pero se muestran de forma destacada al cliente. Un encargado BKB o el jefe puede editarlas, y la
  validación exige que el término no sea anterior al inicio.
- **A4.** Los encargados BKB y el jefe confirman los hitos en orden. Cada hito guarda cuándo se confirmó y quién lo
  hizo (`cumplido_en`, `cumplido_por`, que ya existen).
- **A5.** El hito **Revisión** no lo confirma BKB, lo responde el cliente: el encargado del proyecto o el encargado
  de la empresa. Se puede responder recién cuando todos los hitos anteriores están confirmados.
  - Si el cliente **acepta**, el hito queda cumplido y a su nombre, y el proyecto pasa a **finalizado**, lo que
    dispara el correo de término.
  - Si el cliente **rechaza**, escribe un motivo obligatorio, se guarda el rechazo con fecha y usuario, y se avisa a
    ingeniería. El hito sigue pendiente y el cliente puede aceptarlo más adelante. Los rechazos no se borran y
    quedan en el historial.
- **A6.** Mientras el proyecto no esté finalizado, un encargado BKB o el jefe puede **deshacer el último hito
  confirmado**. Cuando el proyecto ya está finalizado, no se puede deshacer nada.
- **A7.** La vista del cliente muestra solo el nombre del proyecto, la empresa, las fechas de inicio y término, el
  nombre y el correo del encargado cliente, la línea de hitos (con fecha y quién confirmó cada uno), el botón para
  responder la Revisión cuando corresponde y la sección de **modificaciones** (módulo 4), separada de la línea de
  hitos.
- **A8.** Mientras el proyecto no esté finalizado, el cliente **no ve carpetas ni archivos**: ni en la vista, ni en
  los contadores, ni al descargar (404). Cuando el proyecto queda finalizado, ve los archivos como hoy. El personal
  siempre ve todo.
- **A9.** Se eliminan `RespuestaRecepcion`, `avisos.enviar_aviso_recepcion`, el estado `esperando_recepcion` y el
  aviso de bloqueo, porque la Revisión los reemplaza.

### Modelo

```python
class Proyecto(models.Model):
    ...
    fecha_inicio = models.DateField()
    fecha_termino = models.DateField()
    finalizado_en = models.DateTimeField(null=True, blank=True)  # se llena al aceptar la Revisión

class Hito(models.Model):
    ...
    es_revision = models.BooleanField(default=False)  # solo uno por proyecto, siempre el último

class RechazoRevision(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=CASCADE, related_name='rechazos_revision')
    usuario = models.ForeignKey(AUTH_USER_MODEL, on_delete=PROTECT)
    motivo = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
```

`EstadoProyecto` (activo o cerrado) se mantiene para el archivo interno del personal. "Finalizado" se deduce de
`finalizado_en`.

---

## Módulo `avisos-proyecto`

### Reglas

- **V1.** Todos los correos del portal salen en **HTML con respaldo de texto plano** (`EmailMultiAlternatives`) y
  con la marca de BKB. Los correos **del proyecto** (no la invitación, que lleva un enlace para crear contraseña)
  llevan siempre en **CC** las direcciones de `AVISO_INGENIERIA_CORREOS` (variable de entorno,
  por defecto `ingenieria@empresabkb.cl,proyectos.ingenieria@empresabkb.cl`). Esta variable reemplaza a
  `AVISO_RECEPCION_CORREOS`.
- **V2. Inicio:** se envía al crear el proyecto. Va al encargado cliente, con copia a ingeniería, e incluye el
  nombre del proyecto, la empresa, las fechas, la lista de hitos y un botón "Ver avance".
- **V3. Término:** se envía cuando el cliente acepta la Revisión. Va al encargado cliente y, si es otra persona, al
  encargado de la empresa, con copia a ingeniería. Asunto: *"Proyecto {nombre} finalizado y aprobado por
  {cliente}"*. El texto es provisional y se puede ajustar.
- **V4. Rechazo de la Revisión:** se envía a ingeniería con el nombre del proyecto, quién rechazó, la fecha y el
  motivo.
- **V5.** Confirmar o deshacer un hito intermedio **no envía correo**.
- **V6.** Un correo que falla nunca deshace la acción. Se registra en el log y se muestra un aviso en pantalla, igual
  que hoy en `avisos.py` y `enviar_invitacion`. Los correos se envían después del `transaction.atomic`.
- **V7.** Las plantillas de correo viven en `templates/correos/`. Existe un comando para verlas en el navegador antes
  de aprobarlas: `manage.py vista_correos` genera archivos HTML de muestra en una carpeta temporal.

---

## Módulo `modificaciones`

### Reglas

- **M1.** Un encargado BKB o el jefe crea una **modificación** desde el botón "Añadir modificación" del panel del
  proyecto. Lleva un título, una descripción y archivos opcionales (fotos o cualquiera de las extensiones permitidas,
  `EXTENSIONES_PERMITIDAS`). Pertenece al **proyecto**, no a un hito, y no bloquea el avance de los hitos.
  Nace como **borrador** (el cliente no la ve) para poder subir los adjuntos, y se envía con el botón "Enviar al
  cliente". Los recordatorios cuentan desde el envío.
- **M2.** Al crearla se envía un correo al **encargado del proyecto**, con copia a ingeniería. El correo incluye el
  texto completo, los adjuntos y dos botones: **Aprobar** y **Rechazar**.
  - Si los adjuntos suman **20 MB o menos**, van adjuntos al correo.
  - Si pasan de 20 MB, el correo lleva enlaces a la página de la modificación en lugar de los archivos.
- **M3.** Cada botón abre una página del portal con un **enlace firmado, único por modificación y destinatario**, que
  no pide iniciar sesión. Muestra la modificación y un botón para confirmar; rechazar pide un motivo obligatorio.
  **Abrir el enlace nunca aprueba ni rechaza**: la respuesta se registra solo con un POST, porque los antivirus de
  correo abren los enlaces por su cuenta.
- **M4.** El enlace deja de funcionar cuando la modificación ya fue respondida (muestra "ya respondida por X el
  dd-mm") o cuando pasan 30 días.
- **M5.** También se puede responder desde el portal, con sesión iniciada: el encargado del proyecto o el encargado
  de la empresa (E1).
- **M6.** Mientras esté pendiente, el encargado del proyecto recibe un **recordatorio cada 2 días**, con **tope de 5
  correos en total** (incluido el primero), es decir, los días 0, 2, 4, 6 y 8, dentro de los 10 días pedidos. Si no
  hay respuesta, la modificación sigue pendiente y respondible, y se envía **un aviso a ingeniería**: "Sin respuesta
  tras 5 correos".
- **M7.** Cuando alguien responde, se registra la respuesta (aprobada o rechazada), el motivo si se rechazó, quién
  respondió, la fecha y la IP. **Se avisa a ingeniería en los dos casos, al aprobar y al rechazar**, con el
  resultado (y el motivo si se rechazó), y se detienen los recordatorios.
  **Una respuesta es definitiva:** no se puede cambiar. Si hace falta, BKB crea una modificación nueva.
- **M8.** El panel del proyecto muestra la sección "Modificaciones", separada de los hitos, con cada modificación, su
  estado, sus adjuntos, la fecha y quién la respondió. El cliente descarga los adjuntos de las modificaciones aunque
  el proyecto no esté finalizado: son la excepción a A8.
- **M9.** Una modificación se puede repetir cuantas veces haga falta por proyecto, sin límite.

### Modelo

```python
class EstadoModificacion(models.TextChoices):
    PENDIENTE = 'pendiente'; APROBADA = 'aprobada'; RECHAZADA = 'rechazada'

class Modificacion(models.Model):
    proyecto = FK(Proyecto, CASCADE, related_name='modificaciones')
    titulo = CharField(200); descripcion = TextField()
    creada_por = FK(user, PROTECT); creada_en = DateTimeField(auto_now_add=True)
    enviada_en = DateTimeField(null=True)  # null = borrador
    estado = CharField(choices=EstadoModificacion, default=PENDIENTE)
    respondida_por = FK(user, PROTECT, null=True); respondida_en = DateTimeField(null=True)
    motivo_rechazo = TextField(blank=True); ip = GenericIPAddressField(null=True)
    correos_enviados = PositiveSmallIntegerField(default=0); ultimo_correo_en = DateTimeField(null=True)

class Archivo(models.Model):
    ...
    modificacion = FK(Modificacion, SET_NULL, null=True, blank=True, related_name='adjuntos')
```

Los adjuntos usan la subida directa al Space que ya existe (`iniciar_subida` y `confirmar_subida`, con un parámetro
`modificacion_id`). Para adjuntarlos al correo, el servidor los descarga del Space. Los archivos con `modificacion`
no aparecen en la lista general de archivos.

El enlace firmado usa `django.core.signing.TimestampSigner` sobre `(modificacion.pk, usuario.pk)` con
`max_age=30 días`. No se guarda un token en la base de datos: el estado de la modificación basta para que el enlace
sirva una sola vez.

### Recordatorios

- El comando `python manage.py enviar_recordatorios` se puede correr varias veces sin enviar correos de más. Toma las
  modificaciones pendientes con `correos_enviados < 5` y `ultimo_correo_en` de hace 2 días o más (por fecha, no por hora: el trabajo corre a hora fija y así salen los días 0, 2, 4, 6 y 8), envía el
  recordatorio y suma 1 al contador. Si el contador llega a 5, envía el aviso de M6 a ingeniería.
- Corre **una vez al día** como cron del Droplet. Hay que
  confirmar que la cuenta lo tiene disponible en la tarea de despliegue. Si no, la alternativa es un cron externo que
  llame al mismo comando.

---

## Stack y comandos

Django 5.2, Python 3.12, SQLite en local y PostgreSQL en producción, DigitalOcean Spaces (boto3) y SMTP de Google
Workspace. **Sin dependencias nuevas.**

```
cd apps/portal
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check
.\.venv\Scripts\python.exe manage.py enviar_recordatorios     # nuevo
.\.venv\Scripts\python.exe manage.py vista_correos            # nuevo
.\.venv\Scripts\python.exe manage.py runserver
```

## Estructura

```
documentos/models.py            Empresa.encargado, Proyecto (fechas, encargados), Hito.es_revision, RechazoRevision, Modificacion
documentos/permisos.py          única fuente de reglas (se mantiene): puede_editar_proyecto, puede_responder_cliente, ...
documentos/avisos.py            todos los correos del proyecto (inicio, término, rechazo, modificación, recordatorio)
documentos/modificaciones.py    vistas de modificaciones y del enlace firmado
documentos/management/commands/ enviar_recordatorios.py, vista_correos.py
templates/correos/              plantillas HTML y de texto de cada correo
documentos/tests/               una prueba por archivo de reglas: test_encargados, test_avance, test_avisos, test_modificaciones
```

## Estilo

El del repositorio: nombres en español, las reglas de acceso solo en `permisos.py`, vistas con
`get_object_or_404(<consulta de permisos>)` (lo que no se ve da 404), correos que nunca lanzan errores y comentarios
cortos que citan la regla (`# M3`).

```python
def responder_modificacion(request, token):
    modificacion, usuario = leer_enlace(token)  # 404 si la firma es inválida o venció
    if modificacion.estado != EstadoModificacion.PENDIENTE:
        return render(request, 'modificacion_respondida.html', {'m': modificacion})
    if request.method == 'GET':  # M3: abrir el enlace nunca responde
        return render(request, 'modificacion_responder.html', {'m': modificacion})
    ...
```

## Pruebas

`manage.py test` con `django.test.TestCase` y `locmem` como backend de correo (`mail.outbox`). Cada regla (E1…M9)
tiene al menos una prueba que falla si se rompe. Casos obligatorios:

- el cliente recibe 404 en archivos y descargas antes de finalizar el proyecto, y 200 después;
- un GET al enlace firmado no cambia el estado de la modificación; un enlace alterado o vencido da 404;
- el comando de recordatorios, corrido dos veces el mismo día, envía un solo correo, y se detiene en el quinto;
- todos los correos llevan en CC las direcciones de ingeniería;
- un correo que falla (`SMTPException`) no deshace la acción;
- una persona existente no recibe la invitación y una nueva sí.

## Límites

- **Siempre:** correr `manage.py test` antes de cada commit; hacer ramas cortas desde `desarrollo` con PR de vuelta;
  mantener las reglas de acceso solo en `permisos.py`; usar correos de prueba solo del `.env`.
- **Preguntar antes:** agregar dependencias (por ejemplo, un proveedor de correo con API si el Droplet tiene bloqueado el
  puerto 587); crear el editor global de hitos; cambiar la configuración del servidor fuera del cron.
- **Nunca:** poner en un correo un enlace que apruebe con un GET; enviar correos reales a clientes desde local;
  borrar archivos del Space.

## Criterios de éxito

1. Al crear una empresa con un correo nuevo, el encargado recibe la invitación. Con un correo existente, no recibe
   nada.
2. Al crear un proyecto, este tiene los 7 hitos estándar en orden. El encargado cliente recibe el correo de inicio,
   con copia a las 2 direcciones de ingeniería, y la invitación si es una persona nueva.
3. El cliente, en la vista del proyecto, ve solo el nombre, las fechas, el encargado, los hitos con fecha y quién
   los confirmó, y las modificaciones. No ve ni un archivo hasta que acepta la Revisión.
4. Solo los encargados BKB del proyecto y el jefe pueden confirmar, deshacer y editar hitos y fechas. El resto del
   personal recibe 403 al intentarlo.
5. Cuando el cliente acepta la Revisión, el proyecto queda finalizado, le llega el correo de término a él y a
   ingeniería, y ya no se puede deshacer ningún hito. Si la rechaza con un motivo, ingeniería recibe el aviso y el
   hito sigue pendiente.
6. Una modificación con adjuntos llega al encargado con los archivos (o con enlaces, si pasan de 20 MB) y con los
   botones Aprobar y Rechazar. Responder desde el enlace, sin iniciar sesión, registra la respuesta, avisa a
   ingeniería tanto si aprueba como si rechaza, y detiene los recordatorios.
7. Una modificación sin respuesta recibe como máximo 5 correos en 8 días, y después ingeniería recibe el aviso de
   "sin respuesta".
8. `manage.py test`, `check` y `makemigrations --check` pasan en verde.

## Decisiones cerradas (29-09-2026)

1. **A8:** el cliente no ve archivos mientras el proyecto está en curso; los ve después de aceptar la Revisión.
2. **E3:** solo los encargados BKB del proyecto y el jefe avanzan y editan; el resto del personal solo mira.
3. **Editor global de hitos:** fuera de esta versión, la lista estándar queda en el código. Se evalúa después del
   piloto (posible módulo 5, `HitoPlantilla`).
4. **M7:** se avisa a ingeniería al aprobar y al rechazar una modificación.

## Pendientes fuera de esta spec

- **Correos HTML:** revisar con el usuario las muestras de `vista_correos` antes de conectarlos.
- **SMTP:** conectar `instrumentacion@empresabkb.cl` y verificar el puerto 587 en el Droplet; sin eso no sale
  ningún correo en producción.
- **Trabajo programado:** cron diario en el Droplet (01-10-2026).
