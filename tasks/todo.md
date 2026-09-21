# Tareas: Portal de Archivos BKB

> Plan: [`tasks/plan.md`](plan.md) · Spec: [`docs/03-portal-django.md`](../docs/03-portal-django.md) (v1.1)
> Los comandos se ejecutan desde `apps/portal/` con el entorno virtual activo. Prueba: `python manage.py test`.
> Cada tarea termina con un commit en la rama de la fase (`benjamin/AAAA-MM-DD-portal-<fase>`). El PR hacia `desarrollo` lo fusionas tú en cada checkpoint.
> **Modelo de acceso:** dos tipos de usuario (`personal` y `cliente`). El personal ve todo, sube y borra lo que subió. El cliente solo ve y descarga, y solo los proyectos asignados. Sin marca interno/compartido.

## Cómo darle una tarea a un agente

Una tarea por sesión. Copia este mensaje y cambia el número:

```text
Implementa la Tarea N de bkb-platform/tasks/todo.md.

Antes de escribir código lee: tasks/todo.md (la Tarea N completa), tasks/plan.md
(decisiones de arquitectura) y docs/03-portal-django.md (secciones 5 a 8).
Reglas:
- Solo el alcance de la Tarea N. Si algo de otra tarea hace falta, avísame y no lo hagas.
- Cumple cada criterio y ejecuta cada verificación; muéstrame la salida de las pruebas.
- Respeta la sección 8 de la spec ("Siempre / Preguntar primero / Nunca").
- Si una verificación falla, busca la causa: no desactives pruebas ni controles de seguridad.
- Al terminar: marca [x] la tarea y sus criterios en tasks/todo.md, y haz un commit
  en la rama de la fase con un mensaje convencional en español (feat(portal): ...).
- Si la tarea dice "Requiere de ti", detente y pídeme eso antes de empezar.
```

En cada **Checkpoint** no se sigue a la tarea siguiente: el agente corre todas las pruebas, te muestra el resultado y tú revisas y fusionas el PR hacia `desarrollo`.

---

## Fase 1 · Base

### [x] Tarea 0: Rama de trabajo
**Descripción:** Crear la rama del portal desde `desarrollo` y llevar la spec, el plan y la limpieza de documentación del 20-09 y del 21-09 (hoy son cambios sin confirmar **encima de la rama de la landing**).
**Criterios:**
- [x] Rama `benjamin/2026-09-21-portal-base` creada desde `desarrollo` actualizado (con la landing ya fusionada, PR #2)
- [x] Los cambios sin confirmar se llevan con `git stash` → `git switch` → `git stash pop`, sin conflictos
- [x] `docs/03-portal-django.md` (spec), `tasks/` y la limpieza y actualización de `docs/`, `README.md` y `apps/portal/README.md` quedan en un solo commit
- [x] `.mcp.json`, `graphify-out/` y `.graphifyignore` quedan fuera del commit (se agregan a `.gitignore`: son de tu equipo local)
**Verificación:** `git status` limpio y `git log` muestra el commit `docs: spec, plan y limpieza de documentación`
**Dependencias:** ninguna · **Alcance:** XS · **Archivos:** `docs/*`, `README.md`, `apps/portal/README.md`, `tasks/*`, `.gitignore`

### [x] Tarea 1: Entorno y dependencias
**Descripción:** Fijar Django 5.2 LTS, quitar dependencias que la v1 no usa y recrear el entorno virtual limpio.
**Criterios:**
- [x] `requirements.txt`: `django>=5.2,<5.3`; se quitan `django-htmx`, `rules` y `django-allauth`
- [x] `pyproject.toml`: mismas dependencias y sin `[tool.pytest.ini_options]`
- [x] `.env.example` con todas las variables de la sección 4 de la spec, con `SPACES_REGION=nyc3` y `SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com`
**Verificación:**
- [x] Entorno nuevo (`python -m venv .venv`) e `pip install -r requirements.txt` sin errores
- [x] `python -c "import django; print(django.VERSION)"` muestra 5.2.x
- [x] `python manage.py check` sin errores
**Dependencias:** 0 · **Alcance:** S · **Archivos:** `requirements.txt`, `pyproject.toml`, `.env.example`

### [x] Tarea 2: Endurecer `settings.py`
**Descripción:** Cerrar las brechas de seguridad de la configuración antes de agregar código.
**Criterios:**
- [x] `settings.py` lee `.env` con `load_dotenv()`
- [x] `DEBUG` es `False` por defecto
- [x] Sin `SECRET_KEY` real y con `DEBUG=False`, el servidor se niega a arrancar; con `DEBUG=True` usa una clave de desarrollo
- [x] `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` configurado
- [x] `ALLOWED_HOSTS` sale del entorno, sin `portal-staging.bkb.cl` (dominio que no existe) por defecto
- [x] `django-csp` activo con política estricta: `default-src 'self'`, sin `unsafe-inline`, `frame-ancestors 'none'` (las tareas 8 y 12 le agregan el nonce y el dominio del Space)
- [x] Con `DEBUG=False`, cookies con prefijo `__Host-` (`SESSION_COOKIE_NAME`, `CSRF_COOKIE_NAME`), como pide `docs/04`
**Verificación:**
- [x] `DJANGO_DEBUG=False` sin clave: `python manage.py check` falla con un mensaje claro
- [x] Con clave y hosts de producción: `python manage.py check --deploy` sin advertencias
- [x] `.env` local con `DJANGO_DEBUG=True`: `runserver` arranca y `/health/` responde con la cabecera `Content-Security-Policy`
**Dependencias:** 1 · **Alcance:** S · **Archivos:** `config/settings.py`, `.env.example`

---

## Fase 2 · Núcleo: datos, permisos y Space

### [x] Tarea 3: Usuario con tipo (personal o cliente)
**Descripción:** Usuario personalizado que entra con correo y es de tipo personal o cliente. **Debe hacerse antes del primer `migrate`.**
**Criterios:**
- [x] App `accounts` con `Usuario` (correo único como login, `rol`: `personal` o `cliente`) y su gestor
- [x] `AUTH_USER_MODEL = 'accounts.Usuario'`
- [x] `createsuperuser` crea un usuario de tipo `personal` con permisos de superusuario; solo el superusuario entra a `/admin/`
- [x] Registrado en el panel de administración, con el tipo visible
- [x] Se elimina el `db.sqlite3` local antes de migrar
**Verificación:**
- [x] `python manage.py test accounts`: crear usuarios de los 2 tipos, correo duplicado rechazado, superusuario de tipo personal
- [x] `python manage.py migrate` desde cero sin errores
**Dependencias:** 2 · **Alcance:** M · **Archivos:** `accounts/{apps,models,admin}.py`, `accounts/migrations/0001_initial.py`, `accounts/tests/test_usuario.py`, `config/settings.py`

### [x] Tarea 4: Modelos de dominio y panel de administración
**Descripción:** Empresa, proyecto, asignaciones de clientes, archivos y registro de descargas, administrables desde el panel de Django.
**Criterios:**
- [x] Modelos `Empresa`, `Proyecto`, `Membresia` (único por usuario y proyecto), `Archivo` (sin campo de visibilidad; con `eliminado_en` y `eliminado_por`) y `DescargaLog`, con UUID como clave, según la spec
- [x] `Membresia` solo admite usuarios de tipo `cliente`: asignar personal se rechaza con un mensaje claro
- [x] Panel: `Membresia` como inline de `Proyecto`, mostrando la empresa del proyecto
- [x] Panel: acción "Marcar como eliminado" (borrado lógico que registra quién lo hizo); `Archivo` se puede crear a mano para pruebas
**Verificación:**
- [x] `python manage.py makemigrations --check` sin cambios pendientes
- [x] `python manage.py test documentos.tests.test_modelos` (par único, asignar personal rechazado, UUID)
- [x] Manual: en `/admin/` crear empresa, proyecto, usuario cliente y asignarlo (hecho con el cliente de pruebas sobre `/admin/`: `test_flujo_empresa_cliente_proyecto_y_asignacion`; falta tu vistazo en el navegador)
**Dependencias:** 3 · **Alcance:** M · **Archivos:** `documentos/{apps,models,admin}.py`, `documentos/migrations/0001_initial.py`, `documentos/tests/test_modelos.py`

### [x] Tarea 5: Permisos y matriz de pruebas
**Descripción:** La función única que decide todo acceso, con la prueba más importante del proyecto.
**Criterios:**
- [x] `permisos.py` con `proyectos_visibles` (personal: todos; cliente: los asignados), `archivos_visibles`, `puede_subir` (solo personal) y `puede_borrar` (personal: solo lo que subió; superusuario: cualquiera; cliente: nunca)
- [x] Un archivo `pendiente` o eliminado nunca es visible, para nadie
- [x] Un cliente con proyectos de dos empresas ve ambos y ningún otro
**Verificación:**
- [x] `python manage.py test documentos.tests.test_permisos`: matriz tipo de usuario (2) × proyecto (asignado, no asignado) × archivo (disponible, pendiente, eliminado), cada caso con su resultado esperado; `puede_borrar` con autor, otro personal, superusuario y cliente
- [x] Toda rama de `permisos.py` tiene al menos una prueba
**Dependencias:** 4 · **Alcance:** S · **Archivos:** `documentos/permisos.py`, `documentos/tests/test_permisos.py`

### [x] Tarea 6: Conexión con el Space
**Descripción:** Módulo que firma URLs y confirma objetos en el Space, sin salir nunca del prefijo del portal.
**Criterios:**
- [x] `storage.py`: `clave_para(proyecto, archivo)` (prefijo + UUID), URL de descarga de 60 s como adjunto con el nombre original, POST prefirmado con límite de tamaño y de tipo, y `tamano_en_space(clave)`
- [x] No existen funciones para listar ni borrar
- [x] Variables `SPACES_*` leídas de `settings.py` (el prefijo se valida al arrancar: vacío, sin `/` final o con `..` impide iniciar)
- [x] Prueba manual contra el Space real con prefijo `portal-dev/`
**Verificación:**
- [x] `python manage.py test documentos.tests.test_storage` (firma real offline con claves falsas, y cliente simulado para `head_object`): toda clave empieza con el prefijo, la URL expira en 60 s, el POST incluye `content-length-range`
- [x] Manual (`python manage.py shell`): subir un archivo con el POST prefirmado desde un script, ver el objeto bajo `portal-dev/` en el panel de DigitalOcean y descargarlo con la URL prefirmada (hecho el 21-09-2026: subida 204, tamaño confirmado, descarga idéntica como adjunto; el Space rechazó 2 MB con límite de 1 MB, 0 bytes, `Content-Type` alterado o ausente y clave cambiada de carpeta; falta tu vistazo a los objetos en el panel)
**Dependencias:** 4 · **Requiere de ti:** clave dedicada y CORS para `localhost` (ver plan) · **Alcance:** M · **Archivos:** `documentos/storage.py`, `documentos/tests/test_storage.py`, `config/settings.py`, `.env.example`

### Checkpoint A (tras 5) y B (tras 6)
- [x] Todas las pruebas pasan y `check` sin errores (61 pruebas)
- [ ] La matriz de permisos cubre los dos tipos de usuario y no deja casos sin probar
- [x] Un archivo subido al Space real con la URL prefirmada se descarga bien
- [ ] **Revisión contigo antes de seguir**

---

## Fase 3 · Lo que ve el usuario

### [x] Tarea 7: Login, logout y bloqueo por intentos
**Descripción:** El usuario entra con correo y contraseña, y el sistema bloquea la fuerza bruta.
**Criterios:**
- [x] `django-axes` activo (aplicación, middleware y backend); bloqueo tras 5 intentos fallidos
- [x] El mensaje de error no revela si el correo existe
- [x] `/` exige sesión y redirige a `/login/`; el logout es por POST
- [x] Plantilla simple provisional del login (el diseño va en la tarea 8)
**Verificación:**
- [x] `python manage.py test accounts.tests.test_login`: entrada correcta, error genérico, bloqueo al 5.º fallo, rutas protegidas
- [x] Manual: entrar y salir con un usuario creado en `/admin/`
**Dependencias:** 3 · **Alcance:** M · **Archivos:** `config/settings.py`, `config/urls.py`, `templates/login.html`, `accounts/tests/test_login.py`

### [ ] Tarea 8: Base visual y tema claro/oscuro
**Descripción:** Diseño del login y de la estructura común del portal, con los tokens de BKB.
**Criterios:**
- [ ] Tokens copiados a `static/tokens/` con el comando documentado
- [ ] `base.html` con encabezado (logo, usuario, salir) y `portal.css`
- [ ] Tema claro por defecto, con conmutador a oscuro que se recuerda sin parpadeo (`localStorage` dentro de `try/catch`). El script corto del `<head>` usa el nonce de `django-csp`, sin abrir `unsafe-inline`
- [ ] La consola del navegador no muestra bloqueos de CSP
- [ ] Login rediseñado; funciona con teclado, con foco visible y a 375 px
- [ ] Botones y textos pequeños con contraste AA (usar los tokens `salmon-700`, `text-muted` de la landing)
**Verificación:**
- [ ] Manual a 375 y 1280 px, en ambos temas, y navegación con Tab
- [ ] **Revisión visual contigo** (referencias: `Mockup-Preliminar/BKB_Portal_-_Propuesta_de_interfaz.pptx` y la landing)
**Dependencias:** 7 · **Alcance:** M · **Archivos:** `templates/base.html`, `templates/login.html`, `static/portal.css`, `static/tema.js`, `static/tokens/*`

### [ ] Tarea 9: Lista de proyectos
**Descripción:** Al entrar, el personal ve todos los proyectos y cada cliente solo los suyos.
**Criterios:**
- [ ] `/` lista `proyectos_visibles(usuario)` con empresa y estado
- [ ] Mensaje claro cuando un cliente no tiene proyectos asignados
- [ ] El personal ve todos y el cliente no ve los ajenos
**Verificación:**
- [ ] `python manage.py test documentos.tests.test_vistas_proyectos`
- [ ] Manual con un usuario personal y uno cliente
**Dependencias:** 5, 8 · **Alcance:** S · **Archivos:** `documentos/views.py`, `documentos/urls.py`, `templates/proyectos.html`, `documentos/tests/test_vistas_proyectos.py`

### [ ] Tarea 10: Archivos de un proyecto
**Descripción:** Detalle de un proyecto con su lista de archivos.
**Criterios:**
- [ ] `/proyectos/<uuid>/` lista `archivos_visibles` con nombre, tamaño, fecha y quién lo subió
- [ ] Filtro Fotos/Documentos según el tipo del archivo
- [ ] Un proyecto no asignado a un cliente responde 404
**Verificación:**
- [ ] `python manage.py test documentos.tests.test_vistas_archivos`: el HTML entregado a un cliente **no contiene** proyectos ni archivos de proyectos no asignados, ni archivos eliminados o pendientes
- [ ] Manual: crear un `Archivo` de prueba desde `/admin/` con la clave del objeto subido en la tarea 6, y verlo como personal y como cliente asignado
**Dependencias:** 9 · **Alcance:** M · **Archivos:** `documentos/views.py`, `documentos/urls.py`, `templates/archivos.html`, `documentos/tests/test_vistas_archivos.py`

### [ ] Tarea 11: Subida: servidor
**Descripción:** Iniciar y confirmar subidas, solo para personal, con todas las validaciones.
**Criterios:**
- [ ] `POST /proyectos/<uuid>/subir/` valida que el usuario sea personal (un cliente recibe 403), extensión permitida y tamaño ≤ `MAX_UPLOAD_MB`; crea el `Archivo` como `pendiente` y devuelve el POST prefirmado
- [ ] `POST /archivos/<uuid>/confirmar/`: solo quien lo subió; verifica en el Space que el objeto existe y que el tamaño coincide; recién ahí pasa a `disponible`
- [ ] Una vez `disponible`, el archivo lo ven de inmediato los clientes asignados
**Verificación:**
- [ ] `python manage.py test documentos.tests.test_subida`: cliente 403, personal correcto, tipo o tamaño no permitido, confirmar sin haber subido, confirmar ajeno, visibilidad inmediata para un cliente asignado
**Dependencias:** 5, 6 · **Alcance:** M · **Archivos:** `documentos/views.py`, `documentos/urls.py`, `documentos/subidas.py`, `documentos/tests/test_subida.py`

### [ ] Tarea 12: Subida: interfaz
**Descripción:** Pantalla para subir fotos y documentos con avance visible, pensada para celular. Solo la ve el personal.
**Criterios:**
- [ ] Botón "Subir archivo" en el proyecto, visible solo para el personal; acepta selección múltiple y fotos de la cámara
- [ ] Barra de avance y mensajes en español (archivo muy grande, tipo no permitido, error de red)
- [ ] Al terminar, el archivo aparece en la lista
- [ ] JS de unas 40 líneas, sin librerías
- [ ] CSP: `connect-src` y `form-action` admiten solo el endpoint del Space (sale de `SPACES_ENDPOINT`), nada más. Ojo (tarea 6): el POST prefirmado va a `https://{SPACES_BUCKET}.nyc3.digitaloceanspaces.com`, no a `SPACES_ENDPOINT` a secas; el origen de la CSP debe ser ese host
**Verificación:**
- [ ] Manual como personal: subir una foto y un PDF reales a `portal-dev/`
- [ ] Manual como cliente de prueba: no hay botón y un POST directo a la ruta da 403
- [ ] Manual a 375 px: funciona con el navegador del celular
**Dependencias:** 10, 11 · **Requiere de ti:** CORS del Space para `localhost` · **Alcance:** M · **Archivos:** `templates/archivos.html`, `static/subir.js`, `static/portal.css`

### Checkpoint C (tras 12)
- [ ] El personal entra, ve todos los proyectos y sube archivos que aparecen en la lista
- [ ] Un cliente de prueba asignado a un solo proyecto ve ese proyecto y sus archivos, y no ve los demás
- [ ] Las pruebas pasan y `check` sin errores
- [ ] **Revisión contigo**

### [ ] Tarea 13: Descarga con registro
**Descripción:** Descargar un archivo autorizado y dejar constancia.
**Criterios:**
- [ ] `/archivos/<uuid>/descargar/` responde 302 a la URL prefirmada de 60 s como adjunto, para personal y para clientes asignados
- [ ] Se crea un `DescargaLog` (usuario, archivo, fecha e IP, tomando la IP real detrás del proxy)
- [ ] Sin permiso o archivo inexistente: 404 y sin registro
**Verificación:**
- [ ] `python manage.py test documentos.tests.test_descarga` (cliente S3 simulado)
- [ ] Manual: descargar una foto real del Space con `portal-dev/` como personal y como cliente asignado
**Dependencias:** 6, 10 · **Alcance:** S · **Archivos:** `documentos/views.py`, `documentos/urls.py`, `documentos/tests/test_descarga.py`

### [ ] Tarea 14: Borrar lo propio
**Descripción:** El personal borra los archivos que subió y el administrador cualquiera. Es un borrado lógico: el archivo desaparece al instante para todos.
**Criterios:**
- [ ] `POST /archivos/<uuid>/eliminar/` marca `eliminado_en` y `eliminado_por`; el objeto queda en el Space
- [ ] El personal solo borra lo que él subió (lo ajeno responde 403); el superusuario borra cualquiera; el cliente recibe 403
- [ ] Botón "Eliminar" con confirmación ("El archivo dejará de verse para todos"), visible solo para quien puede borrar
- [ ] Un archivo eliminado desaparece de la lista de inmediato y su descarga responde 404
**Verificación:**
- [ ] `python manage.py test documentos.tests.test_borrar`: autor, otro personal, superusuario, cliente, archivo ya eliminado y descarga posterior
- [ ] Manual: subir como personal, borrarlo, y comprobar que un cliente asignado ya no lo ve
**Dependencias:** 5, 10, 12 · **Alcance:** S · **Archivos:** `documentos/views.py`, `documentos/urls.py`, `templates/archivos.html`, `documentos/tests/test_borrar.py`

### Checkpoint D (tras 14): la v1 funciona en local
- [ ] Todas las pruebas pasan
- [ ] El flujo completo funciona con los dos tipos de usuario: login, proyectos, subir (personal), ver y descargar (personal y cliente), y borrar lo propio (personal)
- [ ] `python manage.py check --deploy` sin advertencias con variables de producción
- [ ] **Revisión contigo antes de gastar en infraestructura**

---

## Fase 4 · Producción

### [ ] Tarea 15: Código listo para producción
**Descripción:** Conectar PostgreSQL y describir la aplicación para App Platform.
**Criterios:**
- [ ] `DATABASE_URL` configura la base con `dj-database-url`, y SQLite queda solo como respaldo local
- [ ] Estáticos: `STORAGES` con el almacenamiento comprimido de WhiteNoise y `collectstatic` en el comando de build
- [ ] `.do/app.yaml` versionado (instancia única, comando de `gunicorn`, `migrate` antes de cada despliegue, verificación en `/health/`, variables sin valores secretos)
- [ ] Pasos de despliegue y sincronización de tokens documentados
**Verificación:**
- [ ] `python manage.py check --deploy` sin advertencias
- [ ] `python manage.py test` sigue pasando
**Dependencias:** 12, 13, 14 · **Alcance:** S · **Archivos:** `config/settings.py`, `.do/app.yaml`, `apps/portal/README.md`

### [ ] Tarea 16: Puesta en marcha en DigitalOcean
**Descripción:** Crear los recursos y publicar en `portal.empresabkb.cl`. Sin código: yo te guío y tú apruebas cada paso.
**Criterios:**
- [ ] PostgreSQL gestionado y la aplicación creados en **NYC3**, la región del Space
- [ ] Variables de entorno cargadas en App Platform, con prefijo `portal/` y una clave del Space **nueva para producción** (distinta de la de desarrollo; Limited, solo `bkb-space`, Read/Write/Delete, que es lo único que ofrece DigitalOcean)
- [ ] Dominio `portal.empresabkb.cl` con HTTPS
- [ ] CORS del Space actualizado con `https://portal.empresabkb.cl`
- [ ] Primer administrador creado desde la consola de la app
**Verificación:**
- [ ] `https://portal.empresabkb.cl/health/` responde
- [ ] Sin redirecciones infinitas y con cookies seguras
**Dependencias:** 15 · **Requiere de ti:** aprobar gasto (el DNS de `empresabkb.cl` ya está en DigitalOcean) · **Alcance:** M

### Checkpoint E (tras 16)
- [ ] El login funciona en `portal.empresabkb.cl` con HTTPS
- [ ] Una subida y una descarga reales funcionan en producción

### [ ] Tarea 17: Piloto y documentación
**Descripción:** Probar con un caso real y dejar la documentación al día.
**Criterios:**
- [ ] Piloto con un proyecto de prueba, un usuario del personal y un cliente de confianza: login → el personal sube → el cliente ve y descarga → el personal borra
- [ ] `docs/03-portal-django.md`: marcar la spec como implementada y anotar las desviaciones que hayan surgido
- [ ] `docs/00-contexto-proyecto.md` con el nuevo estado y `docs/06-bitacora-avances.md` con la entrada de la sesión
- [ ] `docs/04-seguridad-y-cumplimiento.md`: marcar como hechos los controles implementados (criterio 10 de la spec)
- [ ] Lista de seguimiento posterior escrita
**Verificación:**
- [ ] Los 10 criterios de éxito de la spec (sección 9) marcados uno a uno
**Dependencias:** 16 · **Alcance:** M · **Archivos:** `docs/03-portal-django.md`, `docs/00-contexto-proyecto.md`, `docs/04-seguridad-y-cumplimiento.md`, `docs/06-bitacora-avances.md`

### Checkpoint F: v1 terminada
- [ ] Los 10 criterios de la sección 9 de la spec se cumplen
- [ ] Documentación al día
