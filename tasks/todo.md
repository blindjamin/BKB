# Tareas: Portal de Archivos BKB

> Plan: [`tasks/plan.md`](plan.md) · Spec: [`docs/03-portal-django.md`](../docs/03-portal-django.md) (v1.3)
> Los comandos se ejecutan desde `apps/portal/` con el entorno virtual activo. Prueba: `python manage.py test`.
> Cada tarea termina con un commit en la rama de la fase (`benjamin/AAAA-MM-DD-portal-<fase>`). El PR hacia `desarrollo` lo fusionas tú en cada checkpoint.
> **Modelo de acceso (v1.3):** tres tipos de usuario (`personal`, `cliente` y `jefe`). Jerarquía: Empresa activa → Proyectos históricos → Carpetas y Archivos. El personal y el jefe crean empresas, proyectos y carpetas con botones de acceso rápido. El cliente solo ve y descarga en sus proyectos asignados, y se queda sin archivos mientras el proyecto espera su recepción.

## ▶ Orden de ejecución (v1.3, plan aprobado el 22-09-2026)

**Los números NO son el orden.** Se sigue esta secuencia, una tarea por sesión, y se detiene en cada checkpoint:

| Paso | Tarea | Rama |
|---|---|---|
| 1 | [x] **Tarea 18:** todas las vistas de archivo pasan por `permisos.py` (y se marca la 11) | `benjamin/AAAA-MM-DD-portal-hitos` |
| 2 | [x] **Tarea 19:** DS-0, la CSP con nonce | la misma |
| 3 | [x] **Cierre de la tarea 12** (subida en el navegador) | la misma |
| 4 | [x] **Tarea 20:** rol jefe y nombre | la misma |
| 5 | [x] **Tarea 21:** hitos, recepción y bloqueo (núcleo) | la misma |
| 6 | [x] **Tarea 22:** estructura: Empresas activas y proyectos por empresa | la misma |
| 7 | [x] **Tarea 23:** carpetas por proyecto y organización de archivos | la misma |
| 8 | [x] **Tarea 24:** marcar hitos en proyecto | la misma |
| 9 | [x] **Tarea 25:** aviso al cliente | la misma |
| 10 | [x] **Tarea 26:** recepción obligatoria y correo | la misma |
| ⏸ | [x] **Checkpoint G** (parte automática, 24-09-2026): pruebas y `check` en verde. **Pendiente del usuario:** flujo manual y PR hacia `desarrollo` | — |
| 11 | [x] **Tarea 27:** Gestión de usuarios e invitación | `benjamin/2026-09-24-portal-gestion` (creada desde `benjamin/2026-09-22-avance-portal`, que aún no está fusionada) |
| 12 | [x] **Tarea 28:** "¿Olvidaste tu contraseña?" | la misma |
| ⏸ | [x] **Checkpoint H** (parte automática, 24-09-2026): pruebas y `check --deploy` en verde. **Pendiente del usuario:** flujo manual y PR hacia `desarrollo` | — |
| 13 | Diseño (`docs/09` §12.4): [x] DS-1 hecho · [x] **Paso B (DS-2 y DS-3)** hecho (24-09-2026, commit `8a1ffda`; brechas corregidas en el commit siguiente) · **Paso C (DS-4 y DS-5)** ← **empezar aquí** · Paso D (DS-6 y DS-7). Ojo: las líneas antiguas de `docs/09` §5 todavía citan +56 9 8249 1403; vale la §12.1. **Pendiente del usuario:** login revisado por el auditor a 1280 px claro y 375 px oscuro; falta revisar inicio, empresa, formularios, Gestión y las pantallas de contraseña a 375 y 1280 px en ambos temas, y el foco de 3 px con teclado | `benjamin/2026-09-24-portal-diseno` |
| 14 | Tarea 15: código listo para producción | `benjamin/AAAA-MM-DD-portal-prod` |
| 15 | Tarea 16: puesta en marcha en DigitalOcean (requiere al usuario) | la misma |
| 16 | Tarea 17: piloto y documentación | la misma |

Al terminar cada tarea, el agente marca `[x]` aquí y en su detalle, y actualiza la flecha **← empezar aquí** a la siguiente.

## Cómo darle una tarea a un agente

Una tarea por sesión. Copia este mensaje y cambia el número:

```text
Implementa la Tarea N de bkb-platform/tasks/todo.md (la que marca "← empezar aquí"
en la tabla "Orden de ejecución"; los números no son el orden).

Antes de escribir código lee: tasks/todo.md (la Tarea N completa), tasks/plan.md
(decisiones de arquitectura) y docs/03-portal-django.md (secciones 5 a 8, y 12 y 13 para las tareas 18 a 28).
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

### [x] Tarea 8: Base visual y tema claro/oscuro
**Descripción:** Diseño del login y de la estructura común del portal, con los tokens de BKB.
**Criterios:**
- [x] Tokens copiados a `static/tokens/` con el comando documentado
- [x] `base.html` con encabezado (logo, usuario, salir) y `portal.css`
- [x] Tema claro por defecto, con conmutador a oscuro que se recuerda sin parpadeo (`localStorage` dentro de `try/catch`). El script corto del `<head>` usa el nonce de `django-csp`, sin abrir `unsafe-inline`
- [x] La consola del navegador no muestra bloqueos de CSP
- [x] Login rediseñado; funciona con teclado, con foco visible y a 375 px
- [x] Botones y textos pequeños con contraste AA (usar los tokens `salmon-700`, `text-muted` de la landing)
**Verificación:**
- [x] Manual a 375 y 1280 px, en ambos temas, y navegación con Tab
- [x] **Revisión visual contigo** (referencias: `Mockup-Preliminar/BKB_Portal_-_Propuesta_de_interfaz.pptx` y la landing)
**Dependencias:** 7 · **Alcance:** M · **Archivos:** `templates/base.html`, `templates/login.html`, `static/portal.css`, `static/tema.js`, `static/tokens/*`

### [x] Tarea 9: Lista de proyectos
**Descripción:** Al entrar, el personal ve todos los proyectos y cada cliente solo los suyos.
**Criterios:**
- [x] `/` lista `proyectos_visibles(usuario)` con empresa y estado
- [x] Mensaje claro cuando un cliente no tiene proyectos asignados
- [x] El personal ve todos y el cliente no ve los ajenos
**Verificación:**
- [x] `python manage.py test documentos.tests.test_vistas_proyectos`
- [x] Manual con un usuario personal y uno cliente
**Dependencias:** 5, 8 · **Alcance:** S · **Archivos:** `documentos/views.py`, `documentos/urls.py`, `templates/proyectos.html`, `documentos/tests/test_vistas_proyectos.py`

### [x] Tarea 10: Archivos de un proyecto
**Descripción:** Detalle de un proyecto con su lista de archivos.
**Criterios:**
- [x] `/proyectos/<uuid>/` lista `archivos_visibles` con nombre, tamaño, fecha y quién lo subió
- [x] Filtro Fotos/Documentos según el tipo del archivo
- [x] Un proyecto no asignado a un cliente responde 404
**Verificación:**
- [x] `python manage.py test documentos.tests.test_vistas_archivos`: el HTML entregado a un cliente **no contiene** proyectos ni archivos de proyectos no asignados, ni archivos eliminados o pendientes
- [x] Manual: crear un `Archivo` de prueba desde `/admin/` con la clave del objeto subido en la tarea 6, y verlo como personal y como cliente asignado
**Dependencias:** 9 · **Alcance:** M · **Archivos:** `documentos/views.py`, `documentos/urls.py`, `templates/archivos.html`, `documentos/tests/test_vistas_archivos.py`

### [x] Tarea 11: Subida: servidor
**Descripción:** Iniciar y confirmar subidas, solo para personal, con todas las validaciones.
**Criterios:**
- [x] `POST /proyectos/<uuid>/subir/` valida que el usuario sea personal (un cliente recibe 403), extensión permitida y tamaño ≤ `MAX_UPLOAD_MB`; crea el `Archivo` como `pendiente` y devuelve el POST prefirmado
- [x] `POST /archivos/<uuid>/confirmar/`: solo quien lo subió; verifica en el Space que el objeto existe y que el tamaño coincide; recién ahí pasa a `disponible`
- [x] Una vez `disponible`, el archivo lo ven de inmediato los clientes asignados
**Verificación:**
- [x] `python manage.py test documentos.tests.test_subida`: cliente 403, personal correcto, tipo o tamaño no permitido, confirmar sin haber subido, confirmar ajeno, visibilidad inmediata para un cliente asignado
**Dependencias:** 5, 6 · **Alcance:** M · **Archivos:** `documentos/views.py`, `documentos/urls.py`, `documentos/subidas.py`, `documentos/tests/test_subida.py`

### [x] Tarea 12: Subida: interfaz
**Descripción:** Pantalla para subir fotos y documentos con avance visible, pensada para celular. Solo la ve el personal.
**Criterios:**
- [x] Botón "Subir archivo" en el proyecto, visible solo para el personal; acepta selección múltiple y fotos de la cámara
- [x] Barra de avance y mensajes en español (archivo muy grande, tipo no permitido, error de red)
- [x] Al terminar, el archivo aparece en la lista
- [x] JS de unas 40 líneas, sin librerías
- [x] CSP: `connect-src` y `form-action` admiten solo el endpoint del Space (sale de `SPACES_ENDPOINT`), nada más. Ojo (tarea 6): el POST prefirmado va a `https://{SPACES_BUCKET}.nyc3.digitaloceanspaces.com`, no a `SPACES_ENDPOINT` a secas; el origen de la CSP debe ser ese host
**Verificación:**
- [x] Manual como personal: subir una foto y un PDF reales a `portal-dev/`
- [x] Manual como cliente de prueba: no hay botón y un POST directo a la ruta da 403
- [x] Manual a 375 px: funciona con el navegador del celular
**Dependencias:** 10, 11 · **Requiere de ti:** CORS del Space para `localhost` · **Alcance:** M · **Archivos:** `templates/archivos.html`, `static/subir.js`, `static/portal.css`

### Checkpoint C (tras 12)
- [x] El personal entra, ve todos los proyectos y sube archivos que aparecen en la lista
- [x] Un cliente de prueba asignado a un solo proyecto ve ese proyecto y sus archivos, y no ve los demás
- [x] Las pruebas pasan y `check` sin errores
- [x] **Revisión contigo**

### [x] Tarea 13: Descarga con registro
**Descripción:** Descargar un archivo autorizado y dejar constancia.
**Criterios:**
- [x] `/archivos/<uuid>/descargar/` responde 302 a la URL prefirmada de 60 s como adjunto, para personal y para clientes asignados
- [x] Se crea un `DescargaLog` (usuario, archivo, fecha e IP, tomando la IP real detrás del proxy)
- [x] Sin permiso o archivo inexistente: 404 y sin registro
**Verificación:**
- [x] `python manage.py test documentos.tests.test_descarga` (cliente S3 simulado)
- [x] Manual: descargar una foto real del Space con `portal-dev/` como personal y como cliente asignado
**Dependencias:** 6, 10 · **Alcance:** S · **Archivos:** `documentos/views.py`, `documentos/urls.py`, `documentos/tests/test_descarga.py`

### [x] Tarea 14: Borrar lo propio
**Descripción:** El personal borra los archivos que subió y el administrador cualquiera. Es un borrado lógico: el archivo desaparece al instante para todos.
**Criterios:**
- [x] `POST /archivos/<uuid>/eliminar/` marca `eliminado_en` y `eliminado_por`; el objeto queda en el Space
- [x] El personal solo borra lo que él subió (lo ajeno responde 403); el superusuario borra cualquiera; el cliente recibe 403
- [x] Botón "Eliminar" con confirmación ("El archivo dejará de verse para todos"), visible solo para quien puede borrar
- [x] Un archivo eliminado desaparece de la lista de inmediato y su descarga responde 404
**Verificación:**
- [x] `python manage.py test documentos.tests.test_borrar`: autor, otro personal, superusuario, cliente, archivo ya eliminado y descarga posterior
- [x] Manual: subir como personal, borrarlo, y comprobar que un cliente asignado ya no lo ve
**Dependencias:** 12, 13 · **Alcance:** S · **Archivos:** `documentos/views.py`, `documentos/urls.py`, `templates/includes/archivo_item.html`, `documentos/tests/test_borrar.py`

### Checkpoint D (tras 14): la v1 funciona en local
- [ ] Todas las pruebas pasan
- [ ] El flujo completo funciona con los dos tipos de usuario: login, proyectos, subir (personal), ver y descargar (personal y cliente), y borrar lo propio (personal)
- [ ] `python manage.py check --deploy` sin advertencias con variables de producción
- [ ] **Revisión contigo antes de gastar en infraestructura**

---

## Fase 3b · Hitos, recepción y jefe (spec v1.2)

> Se hace **antes** de la Fase 4. Orden: 18 → 19 → cierre de 12 → 20 → 21 → 22 → 23 → 24 → 25 → **G** → 26 → 27 → 28 → **H**.
> Leer también `docs/03` secciones 12 y 13. Rama por bloque: `benjamin/AAAA-MM-DD-portal-hitos` (18 a 25) y `benjamin/AAAA-MM-DD-portal-gestion` (26 a 28).

### [x] Tarea 18: Todas las vistas de archivo pasan por `permisos.py`
**Descripción:** Hoy `descargar_archivo` y `eliminar_archivo` deciden con ifs propios. El bloqueo de la v1.2 vive en `archivos_visibles`, así que sin este cambio el cliente podría descargar un archivo bloqueado por enlace directo. También se verifica y se marca la tarea 11, que ya está hecha.
**Criterios:**
- [x] `descargar_archivo` obtiene el archivo con `get_object_or_404` sobre una consulta nueva de `permisos.py`, `archivos_visibles_para(usuario)`, que cubre todos los proyectos visibles (sin ifs propios)
- [x] `eliminar_archivo` decide con `permisos.puede_borrar`, y `archivo_item.html` recibe ese resultado desde la vista en vez de repetir la regla
- [x] `get_client_ip` usa la última IP de `X-Forwarded-For` que agrega el proxy, no la primera (observación de `docs/09` §11)
- [x] Tarea 11: sus criterios se marcan [x] después de correr `test_subida`
**Verificación:**
- [x] `python manage.py test` pasa sin cambiar el resultado esperado de ninguna prueba existente
- [x] `grep -n "is_superuser\|Rol\." documentos/views.py` no encuentra reglas de acceso
**Dependencias:** ninguna · **Alcance:** S · **Archivos:** `documentos/views.py`, `documentos/permisos.py`, `templates/includes/archivo_item.html`, `documentos/tests/test_descarga.py`

### [x] Tarea 19: DS-0 — CSP con nonce y sin estilos ni manejadores en línea
**Descripción:** Es la tarea DS-0 de `docs/09-plan-diseno-portal.md`, sin cambios de alcance. Sin ella no funcionan el aviso, la confirmación de borrado ni el botón de subida.
**Criterios:** los de DS-0 en `docs/09`. En resumen: nonce real en `script-src`, cero `style="..."`, `onclick` y `onsubmit` en las plantillas, pestañas y confirmación de borrado con JS externo, y una prueba que falle si vuelve a aparecer algo en línea.
**Verificación:**
- [x] `python manage.py test` pasa, incluida la prueba de contrato nueva
- [x] Manual: la consola del navegador no muestra errores de CSP en login, proyectos y archivos; "Eliminar" pide confirmación
**Dependencias:** ninguna · **Alcance:** M · **Archivos:** los de DS-0 en `docs/09`

> **Cierre de la tarea 12** (entre la 19 y la 20): con la CSP reparada, completar los criterios pendientes de la tarea 12 (subida real de una foto y un PDF, cliente sin botón, 375 px).

### [x] Tarea 20: Rol jefe y nombre de usuario
**Descripción:** Agregar el tercer valor de `rol` y el campo `nombre`, y actualizar las reglas.
**Criterios:**
- [x] `Rol.JEFE = 'jefe'` y `Usuario.nombre` (texto, opcional en la base y obligatorio en los formularios de Gestión); migración nueva
- [x] Solo puede existir un jefe activo: `clean()` lo rechaza con un mensaje claro, también al guardar desde `/admin/`
- [x] `permisos.py`: `_es_personal` incluye al jefe, se agrega `es_jefe` y `puede_borrar` permite al jefe borrar cualquier archivo
- [x] `Membresia` sigue rechazando todo lo que no sea cliente (también al jefe)
**Verificación:**
- [x] `python manage.py test accounts documentos.tests.test_permisos`: el jefe ve todo, sube y borra cualquier archivo; un segundo jefe activo se rechaza; un jefe desactivado no ve nada
- [x] `python manage.py makemigrations --check` sin cambios pendientes
**Dependencias:** 18 · **Alcance:** S · **Archivos:** `accounts/models.py`, `accounts/admin.py`, `accounts/migrations/`, `documentos/permisos.py`, `documentos/tests/test_permisos.py`

### [x] Tarea 21: Hitos, recepción y bloqueo (núcleo, sin pantallas)
**Descripción:** Modelos y reglas del estado del proyecto. Es la tarea de mayor riesgo: va antes de cualquier pantalla.
**Criterios:**
- [x] Modelos `Hito` (`proyecto`, `orden`, `nombre`, `cumplido_en`, `cumplido_por`; único por proyecto y orden) y `RespuestaRecepcion` (`proyecto`, `usuario`, `nombre_revisor`, `conforme`, `fecha`, `ip`), con UUID
- [x] `permisos.estado_proyecto(proyecto)` devuelve `en_curso`, `esperando_recepcion` o `recibido` según la sección 12.2 de la spec
- [x] `archivos_visibles` y `archivos_visibles_para` devuelven vacío para un **cliente** cuando el proyecto está en `esperando_recepcion`; para el personal y el jefe no cambian
- [x] `puede_gestionar_hitos(usuario)` (personal y jefe) y `puede_responder_recepcion(usuario, proyecto)` (cliente asignado y proyecto esperando recepción)
- [x] Solo lectura en `/admin/` para el superusuario (inline de hitos en `Proyecto` y listado de respuestas)
**Verificación:**
- [x] `python manage.py test documentos.tests.test_permisos`: la matriz suma el eje de estado (en curso, esperando, recibido) × tipo de usuario, en **listado, descarga y UUID directo**. Casos: "no conforme" no desbloquea; una conforme desbloquea a todos los clientes del proyecto; un proyecto sin hitos queda en curso
- [x] Toda rama nueva de `permisos.py` tiene al menos una prueba
**Dependencias:** 20 · **Alcance:** M · **Archivos:** `documentos/models.py`, `documentos/migrations/`, `documentos/permisos.py`, `documentos/admin.py`, `documentos/tests/test_permisos.py`

### [x] Tarea 22: Estructura: Empresas activas y proyectos por empresa
**Descripción:** Implementar la jerarquía de 3 niveles. El personal y el jefe ven en `/` las empresas con proyectos vigentes (con botón `+ Nueva Empresa`), acceden al historial de proyectos de cada una (con botón `+ Nuevo Proyecto`) y crean proyectos. El cliente accede directamente a sus proyectos asignados.
**Criterios:**
- [x] `/`: si es personal o jefe, lista empresas con proyectos vigentes (`permisos.empresas_visibles`) con cantidad de proyectos activos y botón destacado "Nueva empresa"; si es cliente, muestra directamente sus proyectos asignados (o selector de empresas si tiene varias asignadas)
- [x] `/empresas/nueva/`: formulario rápido `EmpresaForm` (nombre y RUT) accesible para personal y jefe; clientes reciben 403
- [x] `/empresas/<uuid>/`: listado histórico de proyectos de esa empresa (activos y cerrados) con badge de estado y botón destacado "Nuevo proyecto" (con empresa preseleccionada)
- [x] `/proyectos/nuevo/` y `/proyectos/<uuid>/editar/`: `ModelForm` de proyecto con empresa, nombre, hitos (uno por línea, al menos uno) y clientes asignados (activos). Clientes reciben 403
**Verificación:**
- [x] `python manage.py test documentos.tests.test_vistas_empresas`: personal y jefe ven empresas activas e histórico de proyectos; cliente solo ve lo asignado y no ve empresas ni proyectos ajenos; cliente recibe 403 al intentar crear empresa o proyecto; formulario de empresa y proyecto validan campos obligatorios
- [ ] Manual: entrar como personal → crear empresa rápida → crear proyecto en ella → verificar que un cliente asignado ve el proyecto
**Dependencias:** 19, 20, 21 · **Alcance:** M · **Archivos:** `documentos/forms.py` (nuevo), `documentos/views.py`, `documentos/urls.py`, `documentos/permisos.py`, `templates/empresas.html` (nuevo), `templates/empresa_detalle.html` (nuevo), `templates/empresa_form.html` (nuevo), `templates/proyecto_form.html` (nuevo), `documentos/tests/test_vistas_empresas.py` (nuevo)

### [x] Tarea 23: Carpetas por proyecto y organización de archivos
**Descripción:** Permitir al personal y al jefe crear carpetas dentro de un proyecto para organizar fotos y documentos de forma ordenada, con acceso rápido y sin alterar las claves del Space.
**Criterios:**
- [x] Modelo `Carpeta` (`id`, `proyecto`, `nombre`, `creado_en`, `creado_por`; único por `proyecto` y `nombre`) y relación `Archivo.carpeta` (`ForeignKey`, opcional `null=True, blank=True, on_delete=models.SET_NULL`). Migración nueva
- [x] En la pantalla del proyecto (`templates/archivos.html`): listado de carpetas (tarjetas/pastillas), botón destacado "Nueva carpeta", migas de pan (*Empresa > Proyecto > Carpeta*) y visualización de archivos (raíz o dentro de la carpeta activa `?carpeta=<uuid>`)
- [x] `POST /proyectos/<uuid>/carpetas/nueva/`: solo personal y jefe; valida nombre no vacío y que no exista en el proyecto
- [x] `POST /carpetas/<uuid>/eliminar/`: solo personal y jefe; elimina carpeta vacía o devuelve sus archivos a la raíz (`SET_NULL`)
- [x] Subida (`subir.js` / `iniciar_subida`): acepta opcionalmente `carpeta_id` para subir directamente a la carpeta activa
- [x] El cliente ve carpetas y archivos en modo solo lectura (sin botones de crear carpeta, subir ni eliminar)
**Verificación:**
- [x] `python manage.py test documentos.tests.test_carpetas`: personal y jefe crean y eliminan carpetas; cliente recibe 403; subida asocia `carpeta_id`; borrar carpeta no borra objetos en el Space; clave en el Space sigue inmutable (`{prefix}{proyecto_id}/{archivo_id}`)
- [ ] Manual en el navegador a 375 y 1280 px: crear carpeta "Informes", subir un archivo dentro de ella, navegar entre carpetas y verificar que el cliente solo lee
**Dependencias:** 22 · **Alcance:** M · **Archivos:** `documentos/models.py`, `documentos/migrations/`, `documentos/views.py`, `documentos/urls.py`, `documentos/subidas.py`, `static/subir.js`, `templates/archivos.html`, `documentos/tests/test_carpetas.py` (nuevo)

### [x] Tarea 24: Marcar hitos en proyecto (personal y jefe)
**Descripción:** Panel de hitos con casillas en la pantalla del proyecto.
**Criterios:**
- [x] `POST /proyectos/<uuid>/hitos/avanzar/` marca el siguiente hito sin cumplir y registra quién y cuándo; `.../retroceder/` desmarca el último cumplido
- [x] Retroceder se rechaza si ya hay una recepción conforme; avanzar sin hitos pendientes no hace nada
- [x] En la pantalla del proyecto, el personal y el jefe ven la lista con el estado de cada hito y solo los botones que aplican
**Verificación:**
- [x] `python manage.py test documentos.tests.test_hitos`: avanza en orden, retrocede solo el último, cliente 403, no retrocede tras una conforme, dos avances seguidos dejan dos hitos marcados (sin saltos)
**Dependencias:** 23 · **Alcance:** S · **Archivos:** `documentos/views.py`, `documentos/urls.py`, `templates/archivos.html`, `documentos/tests/test_hitos.py` (nuevo)

### [x] Tarea 25: Aviso al cliente
**Descripción:** El cliente ve el avance cada vez que abre un proyecto.
**Criterios:**
- [x] `templates/includes/aviso_hitos.html` con la lista de hitos (cumplidos, actual y pendientes) y un mensaje por estado
- [x] Un `<dialog>` que se abre al cargar con `static/aviso.js` (externo, sin nada en línea). En `en_curso` y `recibido` se cierra con "Cerrar"; en `esperando_recepcion` no se cierra (tampoco con Esc) y muestra el formulario de recepción (probado en el HTML; falta verificar Esc en el navegador en el Checkpoint G)
- [x] Sin JS, el mismo contenido se ve arriba de la página
- [x] El bloqueo en `esperando_recepcion` oculta los archivos de todas las carpetas y de la raíz para el cliente
**Verificación:**
- [x] `python manage.py test documentos.tests.test_vistas_archivos`: el cliente recibe el aviso en los tres estados; en `esperando_recepcion` la respuesta no contiene archivos (ni en raíz ni en carpetas); el personal no recibe el aviso
- [ ] Manual en el navegador a 375 y 1280 px: se abre, se cierra cuando corresponde y la consola no muestra errores de CSP
**Dependencias:** 19, 21, 24 · **Alcance:** M · **Archivos:** `templates/includes/aviso_hitos.html` (nuevo), `static/aviso.js` (nuevo), `static/portal.css`, `templates/archivos.html`

### [x] Tarea 26: Recepción obligatoria y correo
**Descripción:** Confirmar o marcar "No conforme", con aviso por correo a direcciones fijas.
**Criterios:**
- [x] `settings.py`: si `EMAIL_HOST` está vacío se usa `console.EmailBackend`; `AVISO_RECEPCION_CORREOS` sale del entorno como lista
- [x] `POST /proyectos/<uuid>/recepcion/` exige `puede_responder_recepcion` (si no, 403; un proyecto no visible da 404), `nombre_revisor` no vacío y, para "conforme", la casilla marcada
- [x] "Conforme" crea `RespuestaRecepcion(conforme=True)` con IP y desbloquea. "No conforme" crea `conforme=False` y mantiene el bloqueo
- [x] Ambos mandan un correo a `AVISO_RECEPCION_CORREOS` con el proyecto, la empresa, el resultado, el revisor, el correo del cliente y la fecha. Si el envío falla, la respuesta se guarda igual y el error queda en el log
**Verificación:**
- [x] `python manage.py test documentos.tests.test_recepcion`: conforme desbloquea y deja 1 correo en `mail.outbox`; no conforme no desbloquea y deja 1 correo; sin nombre se rechaza; personal 403; cliente de otro proyecto 404; proyecto en curso 403; un fallo de correo simulado no pierde la respuesta
- [ ] Manual: el correo aparece en la consola de `runserver`
**Dependencias:** 25 · **Alcance:** M · **Archivos:** `config/settings.py`, `documentos/views.py`, `documentos/urls.py`, `documentos/avisos.py` (nuevo), `documentos/tests/test_recepcion.py` (nuevo)

### Checkpoint G (tras 26): flujo completo en local
- [x] Todas las pruebas pasan y `check` sin errores (24-09-2026: 212 pruebas OK, `check` y `makemigrations --check` sin cambios, en `ce426a3`)
- [ ] **Pendiente del usuario.** Flujo manual: el personal entra a `/` → crea empresa → entra a la empresa → crea proyecto con 3 hitos → crea carpetas y sube archivos en ellas → el cliente ve sus proyectos, carpetas y archivos → el personal marca los 3 hitos → el cliente queda bloqueado → "No conforme" (correo en consola, sigue bloqueado) → confirma (correo, desbloqueado)
- [ ] **Pendiente del usuario.** En el mismo recorrido, las verificaciones manuales que quedaron abiertas: tarea 22 (crear empresa y proyecto, y que el cliente asignado lo vea), tarea 23 (carpeta "Informes" a 375 y 1280 px), tarea 25 (el aviso se abre y se cierra cuando corresponde, **Esc no lo cierra** en `esperando_recepcion`, sin errores de CSP) y tarea 26 (los correos aparecen en la consola de `runserver`; requiere `AVISO_RECEPCION_CORREOS` en el `.env` local)
- [ ] **Pendiente del usuario.** **Revisión contigo** y PR hacia `desarrollo` (los agentes no hacen push ni abren el PR)

### [x] Tarea 27: Gestión de usuarios con invitación por correo (jefe)
**Descripción:** El jefe da de alta al personal y a los clientes; cada uno crea su contraseña con un enlace.
**Criterios:**
- [x] `/gestion/usuarios/` (listado con filtro por tipo y activo), `/gestion/usuarios/nuevo/` y `/gestion/usuarios/<uuid>/`: nombre, correo y tipo (**solo** `personal` o `cliente`). Se crea con `set_unusable_password()`
- [x] Al crear se envía la invitación con el enlace `/contrasena/crear/<uidb64>/<token>/` (`default_token_generator` y `PasswordResetConfirmView`, `PASSWORD_RESET_TIMEOUT` de 3 días). Botón "Reenviar invitación"
- [x] Desactivar y reactivar (sin borrar). El jefe no puede editar jefes ni superusuarios, cambiarse el tipo ni desactivarse (se valida en el servidor, no solo se ocultan opciones)
- [x] La pantalla de crear contraseña usa los validadores de Django y, al terminar, lleva al login
**Verificación:**
- [x] `python manage.py test gestion`: crear un cliente deja 1 correo con un enlace válido; el enlace fija la contraseña y no sirve una segunda vez; un POST con `rol=jefe` se rechaza; editar un superusuario da 404; desactivarse se rechaza; un usuario desactivado no entra
- [ ] Manual: crear un cliente, abrir el enlace desde la consola, crear la contraseña y entrar
**Dependencias:** 20, 26 · **Alcance:** M · **Archivos:** `gestion/` (app nueva: `views.py`, `forms.py`, `urls.py`, `tests.py`), `config/urls.py`, `templates/gestion/usuarios*.html`, `templates/registration/`

### [x] Tarea 28: "¿Olvidaste tu contraseña?"
**Descripción:** Reutiliza la pieza de la tarea 27 para recuperar la contraseña desde el login.
**Criterios:**
- [x] `/contrasena/olvide/` (`PasswordResetView`) enlazado desde el login; la respuesta es idéntica exista o no el correo, y no envía nada a usuarios desactivados
- [x] Límite simple: como máximo 5 pedidos por IP cada 15 minutos (contador en la caché de Django)
- [x] Correo por consola en local
**Verificación:**
- [x] `python manage.py test accounts.tests.test_contrasena`: la misma respuesta para un correo existente y uno inexistente, 1 correo solo en el caso existente, el 6.º pedido se rechaza
**Dependencias:** 27 · **Alcance:** S · **Archivos:** `config/urls.py`, `accounts/views.py`, `templates/login.html`, `templates/registration/password_reset_*.html`, `accounts/tests/test_contrasena.py` (nuevo)

### Checkpoint H (tras 28): Gestión completa en local
- [x] Todas las pruebas pasan y `check --deploy` sin advertencias con variables de producción (24-09-2026: 247 pruebas OK; `check --deploy` sin advertencias con DEBUG=False, SECRET_KEY y ALLOWED_HOSTS ficticios; `makemigrations --check` sin cambios, en `d363c0a`)
- [ ] **Pendiente del usuario.** Flujo manual: el jefe crea personal y clientes desde `/gestion/usuarios/` → reciben correo y fijan contraseña → personal entra, crea empresa, proyecto, carpetas y sube archivos → cliente revisa y confirma
- [ ] **Pendiente del usuario.** Ningún usuario del flujo necesitó `/admin/`
- [ ] **Pendiente del usuario.** **Revisión contigo** y PR hacia `desarrollo` (los agentes no hacen push ni abren el PR). Después va el diseño DS-1 a DS-7 (`docs/09`, ampliado con las pantallas nuevas), antes de la tarea 16

---

## Fase 4 · Producción

### [ ] Tarea 15: Código listo para producción
**Descripción:** Conectar PostgreSQL y describir la aplicación para App Platform.
**Criterios:**
- [ ] `DATABASE_URL` configura la base con `dj-database-url`, y SQLite queda solo como respaldo local
- [ ] Estáticos: `STORAGES` con el almacenamiento comprimido de WhiteNoise y `collectstatic` en el comando de build
- [ ] `.do/app.yaml` versionado (instancia única, comando de `gunicorn`, `migrate` antes de cada despliegue, verificación en `/health/`, variables sin valores secretos)
- [ ] Pasos de despliegue y sincronización de tokens documentados
- [ ] (Auditoría 24-09) Estáticos con versión en el nombre (`CompressedManifestStaticFilesStorage`): sin eso, tras cada despliegue el navegador sigue usando el `portal.css` viejo (visto en local)
- [ ] (Auditoría 24-09, **preguntar primero**: toca seguridad) axes detrás del proxy de App Platform: hoy usa `REMOTE_ADDR`, que en producción es la IP del proxy, así que 5 logins fallidos de cualquiera bloquean a todos. Configurar la IP real del cliente y alinear `_get_client_ip` (usado por el límite de "¿Olvidaste tu contraseña?") con lo mismo
- [ ] (Auditoría 24-09, **preguntar primero**) Con `DEBUG=False` y sin `EMAIL_HOST`, el arranque debe fallar: hoy cae al backend de consola y los enlaces de invitación y recuperación quedarían en los logs de App Platform
**Verificación:**
- [ ] `python manage.py check --deploy` sin advertencias
- [ ] `python manage.py test` sigue pasando
- [ ] (v1.2) Variables `EMAIL_*` y `AVISO_RECEPCION_CORREOS` en `.do/app.yaml` (sin valores secretos)
**Dependencias:** Checkpoint H · **Alcance:** S · **Archivos:** `config/settings.py`, `.do/app.yaml`, `apps/portal/README.md`

### [ ] Tarea 16: Puesta en marcha en DigitalOcean
**Descripción:** Crear los recursos y publicar en `portal.empresabkb.cl`. Sin código: yo te guío y tú apruebas cada paso.
**Criterios:**
- [ ] PostgreSQL gestionado y la aplicación creados en **NYC3**, la región del Space
- [ ] Variables de entorno cargadas en App Platform, con prefijo `portal/` y una clave del Space **nueva para producción** (distinta de la de desarrollo; Limited, solo `bkb-space`, Read/Write/Delete, que es lo único que ofrece DigitalOcean)
- [ ] Dominio `portal.empresabkb.cl` con HTTPS
- [ ] CORS del Space actualizado con `https://portal.empresabkb.cl`
- [ ] Primer administrador creado desde la consola de la app
- [ ] (v1.2) Jefe designado en `/admin/` por el superusuario
- [ ] (v1.2) SMTP real con `instrumentacion@empresabkb.cl` (contraseña de aplicación) y los correos reales del jefe y de los avisos: una invitación de prueba llega a la bandeja. Si App Platform bloquea el puerto 587, detenerse y decidirlo contigo
**Verificación:**
- [ ] `https://portal.empresabkb.cl/health/` responde
- [ ] Sin redirecciones infinitas y con cookies seguras
**Dependencias:** 15 · **Requiere de ti:** aprobar gasto (el DNS de `empresabkb.cl` ya está en DigitalOcean) · **Alcance:** M

### Checkpoint E (tras 16)
- [ ] El login funciona en `portal.empresabkb.cl` con HTTPS
- [ ] Una subida y una descarga reales funcionan en producción
- [ ] (v1.2) Un correo real de invitación y uno de recepción llegan a su destino

### [ ] Tarea 17: Piloto y documentación
**Descripción:** Probar con un caso real y dejar la documentación al día.
**Criterios:**
- [ ] Piloto con un proyecto de prueba, un usuario del personal y un cliente de confianza: login → el personal sube → el cliente ve y descarga → el personal borra. (v1.2) Además: el jefe da de alta al cliente, el personal marca los hitos y el cliente confirma la recepción
- [ ] `docs/03-portal-django.md`: marcar la spec como implementada y anotar las desviaciones que hayan surgido
- [ ] `docs/00-contexto-proyecto.md` con el nuevo estado y `docs/06-bitacora-avances.md` con la entrada de la sesión
- [ ] `docs/04-seguridad-y-cumplimiento.md`: marcar como hechos los controles implementados (criterio 10 de la spec)
- [ ] Lista de seguimiento posterior escrita (incluir: editar nombre y RUT de una empresa desde `/gestion/`, §13.2, que quedó fuera de la T27)
**Verificación:**
- [ ] Los 15 criterios de éxito de la spec (sección 9) marcados uno a uno
**Dependencias:** 16 · **Alcance:** M · **Archivos:** `docs/03-portal-django.md`, `docs/00-contexto-proyecto.md`, `docs/04-seguridad-y-cumplimiento.md`, `docs/06-bitacora-avances.md`

### Checkpoint F: v1 terminada
- [ ] Los 15 criterios de la sección 9 de la spec se cumplen
- [ ] Documentación al día
