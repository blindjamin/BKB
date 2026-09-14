# apps/portal · Portal de Clientes y Gestión Documental BKB (Django)

Backend y panel web interactivo para clientes y técnicos de **BKB**, diseñado con arquitectura monolítica segura en Django y plantillas server-side (HTMX + Tailwind CSS).

## Objetivos del Portal
1. **Acceso de Clientes:** Descarga de certificados SEC TE1, planos As-Built y dossiers de obras ejecutadas.
2. **Autorización Granular:** Políticas estrictas por rol (`Cliente`, `Técnico`, `Administrador`) e identificación UUID.
3. **Almacenamiento Privado:** Documentos alojados en DigitalOcean Spaces con URLs prefirmadas de 60 segundos (sin enlaces públicos).
4. **Auditoría de Descargas:** Registro inmutable de cada visualización y descarga (quién, qué documento, fecha, IP).

## Estructura
- `config/settings.py`: Parámetros de seguridad ASVS Nivel 2, Argon2id y soporte PostgreSQL.
- `config/urls.py`: Enrutamiento base y endpoint de health check (`/health/`).
- `config/wsgi.py`: Entrada WSGI para despliegue en DigitalOcean App Platform con Gunicorn.

## Preparación del Entorno de Desarrollo
```bash
# Crear entorno virtual Python
python -m venv .venv

# Activar entorno virtual
# En Windows:
.venv\Scripts\activate
# En Linux/macOS:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor de desarrollo
python manage.py runserver
```
