# apps/portal · Portal de Archivos BKB (Django)

Portal donde el **personal de BKB sube documentos y fotos de cada proyecto** y los **clientes los consultan y descargan**, cada uno solo en los proyectos que se le asignan. Monolito Django con plantillas en servidor.

> **Estado:** solo existe el esqueleto (`config/` y `/health/`). La especificación está en [`docs/03-portal-django.md`](../../docs/03-portal-django.md), el plan en [`tasks/plan.md`](../../tasks/plan.md) y las tareas en [`tasks/todo.md`](../../tasks/todo.md).

## Qué hará (resumen)
1. **Dos tipos de usuario:** personal (ve todos los proyectos y sube archivos) y cliente (solo ve y descarga, y solo los proyectos que se le asignan). El administrador es el superusuario de Django.
2. **Visibilidad:** lo que sube el personal se ve de inmediato para los clientes asignados al proyecto. No hay revisión previa dentro del sistema.
3. **Archivos:** en un DigitalOcean Space privado, bajo el prefijo `portal/`. Descarga con URL prefirmada de 60 segundos.
4. **Auditoría:** registro de cada descarga (quién, qué archivo, fecha e IP).

## Estructura actual
- `config/settings.py`: configuración de seguridad (Argon2id, cookies y HTTPS). Tiene brechas conocidas que corrige la tarea 2 del plan.
- `config/urls.py`: enrutamiento base y endpoint `/health/`.
- `config/wsgi.py`: entrada WSGI para Gunicorn en DigitalOcean App Platform.

## Preparación del Entorno de Desarrollo
Python 3.12. Desde `apps/portal/`:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py runserver
```
Las variables de entorno van en un archivo `.env` local que **nunca** se versiona. Su plantilla (`.env.example`) se crea en la tarea 1 del plan.
