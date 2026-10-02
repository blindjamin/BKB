# apps/portal · Portal de Archivos BKB (Django)

Portal donde el **personal de BKB sube documentos y fotos de cada proyecto** y los **clientes los consultan y descargan**, cada uno solo en los proyectos que se le asignan. Monolito Django con plantillas en servidor.

> **Estado (01-10-2026):** completo en local y fusionado en `desarrollo` y `main`: portal base (tareas 0 a 28 y diseño) más los 4 módulos de `docs/11` (encargados, avance, avisos y modificaciones). Falta la puesta en marcha en DigitalOcean (tarea 16) y el piloto. Especificación: [`docs/03-portal-django.md`](../../docs/03-portal-django.md) y [`docs/11-spec-avance-y-modificaciones.md`](../../docs/11-spec-avance-y-modificaciones.md). Pendientes: [`tasks/todo.md`](../../tasks/todo.md).

## Qué hace
1. **Tipos de usuario:** personal (ve todos los proyectos y sube archivos), jefe (además da de alta usuarios en `/gestion/`) y cliente (solo ve y descarga los proyectos que se le asignan). El superusuario es una cuenta técnica.
2. **Estructura:** empresas → proyectos → carpetas (solo en la base de datos) y archivos.
3. **Avance, Revisión y modificaciones** (`docs/11`): el personal marca los hitos y el cliente ve solo el avance. Al cumplirse los hitos, el cliente acepta o rechaza la **Revisión**; al aceptar, el proyecto queda finalizado y ve los archivos. Los encargados BKB proponen **modificaciones** con adjuntos; el cliente las aprueba o rechaza desde un enlace firmado del correo (sin sesión) o desde el portal, con recordatorios cada 2 días (hasta 5 correos). Ingeniería recibe copia y aviso de cada respuesta.
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

## Comandos
```powershell
.\.venv\Scripts\python.exe manage.py enviar_recordatorios   # M6: recordatorios de modificaciones sin respuesta (una vez al día)
.\.venv\Scripts\python.exe manage.py vista_correos --dir muestras   # una muestra HTML de cada correo para revisar en el navegador
```

## Pruebas
```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check
```
Las pruebas se corren con el `.env` local (`DJANGO_DEBUG=True`). Con `DJANGO_DEBUG=False` los estáticos usan el manifiesto de WhiteNoise, y las pruebas exigirían un `collectstatic` previo.

## Variables de entorno
La lista completa, con comentarios, está en [`.env.example`](.env.example). Las principales: `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL`, `SPACES_*`, `MAX_UPLOAD_MB`, `EMAIL_*`, `DEFAULT_FROM_EMAIL`, `AVISO_INGENIERIA_CORREOS` y `PORTAL_URL` (URL pública para los enlaces de los recordatorios, que se envían sin petición web).

## Despliegue (Droplet de DigitalOcean)
Producción vive en el Droplet `178.128.159.13` (Ubuntu 22.04), junto con la landing. Las notas del servidor están en `/srv/BKB-2026/LEEME.txt`.
- **Código:** clon de `main` en `/srv/BKB-2026/repo`; entorno Python en `/srv/BKB-2026/venv`.
- **Ejecución:** servicio systemd `bkb-2026-portal` (usuario `bkb`): `gunicorn config.wsgi:application --bind 127.0.0.1:8002 --workers 2 --timeout 60`.
- **nginx:** `/etc/nginx/sites-available/portal-empresabkb`, HTTPS con Certbot. Debe enviar `X-Real-IP $remote_addr` (la IP del cliente para axes y los topes) y `X-Forwarded-Proto $scheme`.
- **Variables:** `/srv/BKB-2026/portal.env` (fuera del repo).
- **Base de datos:** SQLite en `/srv/BKB-2026/data/portal.sqlite3`.
- **Publicar:** después de fusionar a `main`, `/srv/BKB-2026/deploy.sh` (pull, landing, `pip install`, `migrate`, `collectstatic` y reinicio).
- **Recordatorios:** cron diario de `python manage.py enviar_recordatorios` como usuario `bkb`.
- **Logs:** `journalctl -u bkb-2026-portal -n 50`. Sin `EMAIL_HOST`, los correos quedan ahí.
- **Límite de "¿Olvidaste tu contraseña?":** vive en la caché en memoria de cada proceso; con 2 workers, el límite efectivo es de 10 pedidos por IP cada 15 minutos.

Pendiente: qué hacer si falta `EMAIL_HOST` con `DEBUG=False` (en espera de las cuentas de correo, `docs/04` §6).

## Actualizar tokens de diseño
El portal usa los estilos de `packages/tokens`; `static/tokens/` es una copia y no se edita a mano. Para sincronizar (desde `apps/portal/`):
```powershell
New-Item -ItemType Directory -Force -Path static\tokens
Copy-Item -Recurse -Force ..\..\packages\tokens\src\* static\tokens\
```
Los ajustes propios del portal (por ejemplo `--text-muted` en tema claro) van en `static/portal.css`.
