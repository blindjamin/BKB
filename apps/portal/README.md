# apps/portal · Portal de Archivos BKB (Django)

Portal donde el **personal de BKB sube documentos y fotos de cada proyecto** y los **clientes los consultan y descargan**, cada uno solo en los proyectos que se le asignan. Monolito Django con plantillas en servidor.

> **Estado (25-09-2026):** funcionalidad y diseño completos en local (tareas 1 a 28 y pasos de diseño A a D); el código está listo para App Platform (tarea 15). Falta la puesta en marcha en DigitalOcean (tarea 16), que requiere decisiones y credenciales del usuario. La especificación está en [`docs/03-portal-django.md`](../../docs/03-portal-django.md), el plan en [`tasks/plan.md`](../../tasks/plan.md) y las tareas en [`tasks/todo.md`](../../tasks/todo.md).

## Qué hace
1. **Tipos de usuario:** personal (ve todos los proyectos y sube archivos), jefe (además da de alta usuarios en `/gestion/`) y cliente (solo ve y descarga los proyectos que se le asignan). El superusuario es una cuenta técnica.
2. **Estructura:** empresas → proyectos → carpetas (solo en la base de datos) y archivos.
3. **Hitos y recepción:** el personal marca los hitos; al completarlos, el cliente debe confirmar la recepción para volver a ver los archivos, y se avisa por correo.
4. **Archivos:** en un DigitalOcean Space privado, bajo `SPACES_PREFIX`. Se suben directo del navegador al Space y se descargan con una URL prefirmada de 60 segundos.
5. **Auditoría:** registro de cada descarga (quién, qué archivo, fecha e IP).

## Estructura
- `config/`: configuración, rutas y entrada WSGI (Gunicorn).
- `accounts/`: usuario propio (entra con correo) y "¿Olvidaste tu contraseña?".
- `documentos/`: empresas, proyectos, carpetas, hitos, archivos y permisos (`permisos.py` es la única fuente de reglas de acceso).
- `gestion/`: alta de usuarios con invitación (solo el jefe).
- `templates/` y `static/`: plantillas, CSS, JS externo (sin nada en línea, por la CSP), fuentes e íconos.

## Desarrollo local
Python 3.12 (`.python-version`). Desde `apps/portal/`:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # y completar; .env nunca se versiona
python manage.py migrate
python manage.py runserver
```
Sin `DATABASE_URL` se usa SQLite (`db.sqlite3`). Sin `EMAIL_HOST` los correos salen por la consola.

## Pruebas
```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check
```
Las pruebas se corren con el `.env` local (`DJANGO_DEBUG=True`). Con `DJANGO_DEBUG=False` los estáticos usan el manifiesto de WhiteNoise, y las pruebas exigirían un `collectstatic` previo.

## Variables de entorno
La lista completa, con comentarios, está en [`.env.example`](.env.example). Las principales: `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL`, `SPACES_*`, `MAX_UPLOAD_MB`, `EMAIL_*`, `DEFAULT_FROM_EMAIL` y `AVISO_RECEPCION_CORREOS`.

## Despliegue (DigitalOcean App Platform)
La especificación está en [`.do/app.yaml`](../../.do/app.yaml), en la raíz del monorepo. Resumen:
- **Build:** `python manage.py collectstatic --noinput` (WhiteNoise sirve los estáticos comprimidos y con versión en el nombre).
- **Ejecución:** `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 60`, una sola instancia.
- **Antes de cada despliegue:** job `PRE_DEPLOY` con `python manage.py migrate --noinput`.
- **Salud:** `/health/`.
- **Base de datos:** PostgreSQL administrado; `DATABASE_URL` lo inyecta App Platform y ya trae `sslmode=require`, por eso el código no fuerza SSL (así sigue funcionando el respaldo de SQLite en local).
- **Secretos:** `DJANGO_SECRET_KEY`, `SPACES_KEY`, `SPACES_SECRET`, `EMAIL_HOST_PASSWORD` y `AVISO_RECEPCION_CORREOS` van en `app.yaml` como `type: SECRET` **sin valor**, y se cargan a mano en el panel de App Platform. `DJANGO_SECRET_KEY` también se necesita en el build, porque `collectstatic` carga la configuración.
- **Límite de "¿Olvidaste tu contraseña?":** vive en la caché en memoria de cada proceso; con 2 workers, el límite efectivo es de 10 pedidos por IP cada 15 minutos.
- **Validación del spec:** `doctl apps spec validate .do/app.yaml` queda para la tarea 16 (necesita una sesión de DigitalOcean).

Pendientes de decisión del usuario antes de la tarea 16 (ver `tasks/todo.md`): la IP real del cliente para axes detrás del proxy, el arranque sin `EMAIL_HOST` con `DEBUG=False`, y verificar que el chequeo de salud no choque con la redirección HTTPS o con `ALLOWED_HOSTS`.

## Actualizar tokens de diseño
El portal usa los estilos de `packages/tokens`; `static/tokens/` es una copia y no se edita a mano. Para sincronizar (desde `apps/portal/`):
```powershell
New-Item -ItemType Directory -Force -Path static\tokens
Copy-Item -Recurse -Force ..\..\packages\tokens\src\* static\tokens\
```
Los ajustes propios del portal (por ejemplo `--text-muted` en tema claro) van en `static/portal.css`.
