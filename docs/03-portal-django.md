# 03 · Portal de Archivos BKB (`apps/portal`): especificación

> **Estado:** especificación APROBADA v1.1 (21-09-2026). Plan de implementación: [`tasks/plan.md`](../tasks/plan.md). Tareas: [`tasks/todo.md`](../tasks/todo.md).
> **Sustituye** al diseño anterior de este documento, que quedó desactualizado.
> **Origen:** entrevista de intención con el usuario (20-09-2026).
> **Cambios de la v1.1 (21-09-2026):** BKB indicó que el cliente **no puede subir archivos**, solo verlos. Por eso: (1) los roles pasan de tres a dos, (2) se elimina la marca interno/compartido, (3) todo el personal ve todos los proyectos, y (4) el personal puede borrar lo que él subió (el administrador, cualquier archivo).

---

## 1. Objetivo

Portal web donde el **personal de BKB sube documentos y fotos de cada proyecto** y los **clientes los consultan y descargan**, cada cliente solo en los proyectos que se le asignan. Reemplaza el envío de archivos por correo y el uso manual del Space.

**Usuarios y qué pueden hacer**

| Quién | Ve proyectos | Ve archivos | Sube | Borra |
|---|---|---|---|---|
| **Personal de BKB** | Todos | Todos | Sí | **Solo lo que él subió** |
| **Cliente** | Solo los que se le asignan | Todos los de esos proyectos | **No** | **No** |
| **Administrador** (superusuario de Django, por ahora tú) | Todos | Todos | Sí | **Cualquier archivo** |

El administrador crea usuarios, empresas, proyectos y asignaciones desde el panel de Django. No es un rol aparte del portal: es un usuario de tipo personal con permisos de superusuario.

**Reglas centrales**

1. El **personal** ve todos los proyectos y todos los archivos.
2. Un **cliente** ve únicamente los proyectos que se le asignaron y, dentro de ellos, todos los archivos.
3. Un proyecto no asignado **no existe** para el cliente: ni en listados ni por enlace directo. Se responde **404** (no 403), para no revelar que existe.
4. **Solo el personal sube.** Un archivo subido se ve **de inmediato** para los clientes asignados al proyecto. No hay paso de revisión dentro del sistema: se asume que el personal capacitado revisa antes de subir.
5. Un cliente que intente subir, confirmar o borrar recibe **403**.
6. **Borrar:** el personal puede borrar los archivos que él mismo subió, y el administrador cualquiera. Borrar es lógico y el archivo **desaparece al instante para todos**. El personal que intente borrar un archivo ajeno recibe 403.

**Éxito:** el personal entra, sube un archivo a un proyecto, y el cliente asignado lo ve y lo descarga. Si el personal se equivoca, borra su archivo y deja de verse. Un cliente no ve proyectos ajenos ni sus archivos.

**Restricciones:** lo desarrolla una persona con apoyo de IA; sin fecha (terminar lo antes posible); el costo de infraestructura importa (objetivo ≈ US$ 27/mes: 1 instancia, PostgreSQL gestionado y el Space actual; sin staging ni worker al inicio).

**Fuera de alcance de la v1:** subida de archivos por clientes, marca interno/compartido, asignación de proyectos al personal, migrar los archivos antiguos del Space (se dejan donde están; solo el personal los abre directo en DigitalOcean), facturas o ERP, firma electrónica, app móvil, visor DWG, miniaturas y previsualización, avisos por correo, Google SSO, 2FA, subcarpetas dentro de un proyecto y panel de administración propio.

**Si más adelante piden que el cliente suba o solicite documentos:** el acceso está centralizado en `permisos.py`, así que el cambio se concentra ahí y reutiliza el flujo de subida.

---

## 2. Suposiciones

Confirmadas por el usuario el 20-09-2026 y ajustadas el 21-09-2026 (las 6 y 8 cambiaron; la 5 se precisó).

1. **Login:** correo + contraseña de Django, cuentas creadas por el administrador, sin registro público. Google SSO y passkeys quedan para después.
2. **Administrador = superusuario de Django** (por ahora una sola persona, tú). Usa el panel `/admin/` para crear empresas, usuarios, proyectos y asignaciones, y puede borrar cualquier archivo. El personal que no es superusuario no entra al panel: borra desde el portal.
3. **Un cliente puede trabajar con más de una empresa.** El usuario no lleva empresa propia: su acceso sale solo de los proyectos que se le asignan (`Membresia`). El panel muestra la empresa de cada proyecto al asignarlo, para evitar errores.
4. **Categorías:** no hay categorías manuales. Un archivo es "foto" si su tipo es `image/*` y "documento" en otro caso. La lista se filtra por ese criterio.
5. **Borrado:** el personal borra **lo que él subió** (botón en el portal) y el administrador borra **cualquier archivo**. Es lógico: marca `eliminado_en` y `eliminado_por`, oculta el archivo al instante para todos y el objeto queda en el Space. Sirve para corregir una subida por error.
6. **Solo el personal sube y lo subido se ve de inmediato.** El personal ve todos los proyectos, sin asignación. `Membresia` existe solo para clientes.
7. **Límites de subida:** 50 MB por archivo. Tipos permitidos: `pdf, jpg, jpeg, png, heic, doc, docx, xls, xlsx, dwg, dxf`. Sin `zip`, ejecutables ni scripts.
8. **Sin antivirus en la v1.** Quienes suben son personal de BKB, no el público. Django nunca procesa el contenido de los archivos (viajan navegador ↔ Space) y las descargas salen siempre como adjunto. ClamAV queda como mejora opcional, ya no como condición del lanzamiento.
9. **Desarrollo local contra el Space real** con el prefijo `portal-dev/`, y producción con `portal/`. Las pruebas automáticas **no** tocan el Space (usan un cliente simulado).
10. **Interfaz:** plantillas Django con CSS propio que usa las variables de `packages/tokens` v2. Tema claro por defecto, con conmutador a oscuro igual que la landing. Sin Tailwind ni build de Node (ver sección 11).
11. **Python 3.12** (con soporte hasta oct-2028) y **Django 5.2 LTS**, fijado en `>=5.2,<5.3` (parches de seguridad hasta abril de 2028). El entorno local tiene hoy Django 6.1.1 (soporte hasta dic-2027, no LTS): se baja a 5.2 antes de escribir código.

---

## 3. Stack

| Capa | Elección |
|---|---|
| Lenguaje / framework | Python 3.12 · Django 5.2 LTS |
| Servidor | Gunicorn + WhiteNoise, en DigitalOcean App Platform |
| Base de datos | SQLite en local; PostgreSQL gestionado en producción vía `DATABASE_URL` (`dj-database-url`) |
| Archivos | DigitalOcean Space `bkb-space`, privado, con `django-storages`/`boto3` solo para firmar URLs |
| Seguridad | Argon2id, `django-axes` (bloqueo por fuerza bruta), `django-csp`, cookies seguras |
| Interfaz | Plantillas Django + CSS propio con tokens (HTMX solo si una pantalla lo necesita) |
| Permisos | Una función propia en `permisos.py`. Sin `rules` |

**Brechas del código actual** (`apps/portal/config/settings.py`), que la implementación debe cerrar:

- No hay `AUTH_USER_MODEL` propio. **Debe definirse antes del primer `migrate`.** El `db.sqlite3` local no versionado se descarta.
- `DEBUG` es `True` por defecto y `SECRET_KEY` tiene un valor inseguro por defecto. Debe pasar a `DEBUG=False` por defecto, y sin `SECRET_KEY` real el servidor debe negarse a arrancar (salvo con `DEBUG=True` en local).
- `settings.py` no lee el archivo `.env` (falta `load_dotenv()`), así que un `.env` local no tendría efecto.
- Detrás del proxy de App Platform, `SECURE_SSL_REDIRECT=True` sin `SECURE_PROXY_SSL_HEADER` causa una redirección infinita.
- La base de datos está fija en SQLite. `dj-database-url` se conecta en la tarea de despliegue; no bloquea el desarrollo local.
- `axes` está comentado: hay que activarlo (aplicación, middleware y backend de autenticación). `django-htmx`, `rules` y `django-allauth` salen de `requirements.txt` y de `pyproject.toml` (no se usan en la v1).
- `pyproject.toml` lista `django-rules`, un paquete distinto y abandonado; desaparece al quitar `rules`.
- Sin `pytest` en la v1: se elimina `[tool.pytest.ini_options]` de `pyproject.toml`.
- `requirements.txt` permite Django 5.1 (ya sin soporte) y 6.1 (instalado hoy): se fija a `>=5.2,<5.3`.

---

## 4. Comandos

Desde `apps/portal/` (Windows, PowerShell):

```powershell
python -m venv .venv                          # una sola vez
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python manage.py migrate                      # aplicar migraciones
python manage.py createsuperuser              # crear el primer administrador
python manage.py runserver                    # desarrollo en http://127.0.0.1:8000
python manage.py test                         # pruebas (runner de Django, sin dependencias nuevas)
python manage.py check --deploy               # revisión de seguridad para producción
python manage.py makemigrations --check       # falla si faltan migraciones
```

Variables de entorno (archivo `apps/portal/.env`, **nunca** versionado; se documenta `.env.example`):

```
DJANGO_SECRET_KEY=            DJANGO_DEBUG=False         DJANGO_ALLOWED_HOSTS=
DATABASE_URL=                 (vacío en local = SQLite)
SPACES_KEY=                   SPACES_SECRET=
SPACES_BUCKET=bkb-space       SPACES_REGION=              SPACES_ENDPOINT=
SPACES_PREFIX=portal-dev/     (producción: portal/)
MAX_UPLOAD_MB=50
```

---

## 5. Estructura del proyecto

```
apps/portal/
├── config/                 settings (por entorno), urls, wsgi
├── accounts/               Usuario (rol personal/cliente), login/logout
├── documentos/
│   ├── models.py           Empresa, Proyecto, Membresia, Archivo, DescargaLog
│   ├── permisos.py         ÚNICA fuente de reglas de acceso
│   ├── storage.py          URLs prefirmadas y prefijo del Space
│   ├── views.py            proyectos, archivos, subir, descargar, eliminar
│   ├── admin.py            panel de Django para el administrador
│   └── tests/              permisos, subida, descarga, storage
├── templates/              base, login, proyectos, archivos
├── static/portal.css       estilos con las variables de packages/tokens
└── .env.example
.do/app.yaml                especificación de App Platform (raíz del monorepo)
```

**Modelo de datos** (identificadores UUID, nunca correlativos):

| Modelo | Campos clave |
|---|---|
| `Empresa` | `id`, `nombre`, `rut` |
| `Usuario` | correo (login), `rol` (`personal`/`cliente`). Sin empresa propia. El superusuario es `personal` |
| `Proyecto` | `id`, `empresa`, `nombre`, `estado` (`activo`/`cerrado`) |
| `Membresia` | `usuario` (solo clientes), `proyecto` (único por par). Asignar personal se rechaza |
| `Archivo` | `id`, `proyecto`, `nombre_original`, `clave_space`, `tamano`, `tipo`, `subido_por`, `estado` (`pendiente`/`disponible`), `subido_en`, `eliminado_en`, `eliminado_por` |
| `DescargaLog` | `usuario`, `archivo`, `fecha`, `ip` |

**Rutas**

| Ruta | Quién | Función |
|---|---|---|
| `/login/`, `/logout/` | Todos | Acceso |
| `/` | Todos | Proyectos visibles para el usuario |
| `/proyectos/<uuid>/` | Todos | Archivos del proyecto (filtro foto/documento) |
| `POST /proyectos/<uuid>/subir/` | Personal | Inicia la subida: valida y devuelve un POST prefirmado |
| `POST /archivos/<uuid>/confirmar/` | Personal (quien subió) | Confirma la subida: verifica que el objeto existe en el Space |
| `GET /archivos/<uuid>/descargar/` | Todos | Responde 302 a una URL prefirmada de 60 s |
| `POST /archivos/<uuid>/eliminar/` | Personal (lo que subió) y administrador | Borrado lógico: oculta el archivo al instante |
| `/admin/`, `/health/` | Administrador / monitoreo | Panel de Django y salud del servicio |

**Almacenamiento**

- Clave de cada objeto: `{SPACES_PREFIX}{proyecto_uuid}/{archivo_uuid}`. El nombre original vive solo en la base de datos.
- Las claves se construyen **siempre** a partir de UUID y del prefijo configurado. Nunca desde texto del usuario.
- El portal **no lista, no borra y no toca** nada fuera de su prefijo.
- Subida: el navegador envía el archivo directo al Space con un **POST prefirmado** que fija `content-length-range` (así el límite de tamaño lo aplica el Space, no solo el portal). Requiere configurar CORS en el Space para el dominio del portal.
- Descarga: URL prefirmada de 60 s con `Content-Disposition: attachment`.

---

## 6. Estilo de código

Dominio en español (coincide con los docs y con los usuarios), idioma de Django en inglés. Sin capas ni abstracciones que no se usen.

```python
# documentos/permisos.py — toda vista decide acceso llamando aquí, nunca con ifs propios.
def proyectos_visibles(usuario):
    if usuario.rol == Rol.PERSONAL:
        return Proyecto.objects.all()
    return Proyecto.objects.filter(membresias__usuario=usuario)

def archivos_visibles(usuario, proyecto):
    if not proyectos_visibles(usuario).filter(pk=proyecto.pk).exists():
        return Archivo.objects.none()
    return proyecto.archivos.filter(estado='disponible', eliminado_en__isnull=True)

def puede_subir(usuario):
    return usuario.rol == Rol.PERSONAL

def puede_borrar(usuario, archivo):
    return usuario.rol == Rol.PERSONAL and (usuario.is_superuser or archivo.subido_por == usuario)
```

Las vistas obtienen objetos con `get_object_or_404(archivos_visibles(...), pk=...)`, de modo que "no existe" y "no tienes permiso" se ven igual desde afuera. Una acción no permitida sobre algo que el usuario sí ve (un cliente que intenta subir a su proyecto, o personal que intenta borrar un archivo ajeno) responde 403.

---

## 7. Estrategia de pruebas

- **Runner:** `python manage.py test`. Sin dependencias nuevas; el cliente S3 se simula con `unittest.mock`.
- **Matriz de permisos (la prueba más importante):** cada combinación de tipo de usuario (personal, cliente) × proyecto (asignado, no asignado) × archivo (disponible, pendiente, eliminado), verificada en **listado, descarga y acceso por UUID directo**. Se agrega el caso de un cliente con proyectos de dos empresas: ve ambos y ningún otro.
- **Subida:** solo el personal puede iniciar y confirmar; un cliente recibe 403; se rechazan tipos y tamaños no permitidos; solo quien subió puede confirmar.
- **Borrado:** el autor puede borrar; otro personal recibe 403; el superusuario puede borrar cualquiera; el cliente recibe 403; un archivo borrado desaparece de la lista y su descarga da 404.
- **Storage:** toda clave generada empieza con el prefijo configurado; ninguna operación sale de él.
- **Login:** bloqueo tras intentos fallidos; el mensaje de error no revela si el correo existe.
- **Manual (una vez por hito):** subir una foto y un PDF reales contra el Space con prefijo `portal-dev/` como personal, y verlos y descargarlos como un cliente de prueba asignado.
- **Cobertura:** sin porcentaje mínimo. La regla es que `permisos.py` y `storage.py` estén completamente cubiertos.

---

## 8. Límites

**Siempre**
- Todo acceso a un proyecto o archivo pasa por `permisos.py`.
- Responder 404 (no 403) cuando el recurso existe pero el usuario no debe saberlo.
- Correr `python manage.py test` antes de cada commit.
- Rama de tarea `benjamin/AAAA-MM-DD-descripcion` y PR manual hacia `desarrollo` (ver `docs/05-git-workflow.md`).
- Validar en el servidor: tipo de usuario, extensión, tamaño, pertenencia al proyecto y autoría para borrar.

**Preguntar primero**
- Agregar una dependencia (incluye `pytest`, ClamAV, Tailwind).
- Cambiar un modelo cuando ya haya datos reales.
- Tocar configuración de seguridad (cookies, CSP, hosts, axes).
- Cualquier gasto nuevo en DigitalOcean (segunda instancia, staging, worker, otro Space).
- Cualquier cambio en el Space que no sea bajo el prefijo `portal/`.

**Nunca**
- Versionar `.env`, claves del Space, `SECRET_KEY` ni `db.sqlite3`.
- Hacer público el Space ni un objeto suelto.
- Listar, mover o borrar archivos antiguos del Space.
- Aceptar rutas o claves del Space desde el usuario.
- Dejar que un cliente suba, confirme o borre archivos, ni que vea un proyecto que no se le asignó.
- Dejar que el personal borre archivos que subió otra persona (solo el administrador puede).
- Borrar de verdad el objeto del Space desde el portal: el borrado es siempre lógico.
- Desactivar CSRF, axes o la validación de contraseñas para "probar más rápido".
- Pasar el contenido de los archivos por el servidor Django.

---

## 9. Criterios de éxito (v1 terminada)

1. La matriz de permisos completa pasa: **un cliente nunca ve un proyecto no asignado ni sus archivos**, ni por listado, ni por enlace directo, ni por UUID adivinado (todos dan 404). El personal ve todos los proyectos y archivos.
2. El personal sube un archivo y, una vez confirmado, lo ven de inmediato los clientes asignados. Un cliente que intenta subir o confirmar recibe 403.
3. Se rechazan archivos de más de `MAX_UPLOAD_MB` y con extensiones fuera de la lista permitida.
4. El personal borra un archivo que subió y desaparece al instante para todos (el cliente ya no lo ve y su descarga da 404). El personal no puede borrar uno ajeno (403), el administrador puede borrar cualquiera y el cliente no puede borrar.
5. Toda descarga autorizada (de personal o de cliente) devuelve una URL prefirmada de **60 s**, como adjunto, y deja un `DescargaLog`.
6. Las pruebas demuestran que ninguna clave generada queda fuera del prefijo `portal/`.
7. Tras 5 intentos fallidos el login queda bloqueado, y el mensaje de error no revela si el correo existe.
8. `python manage.py check --deploy` sin advertencias con variables de producción.
9. Desplegado en `portal.empresabkb.cl` con HTTPS, `/health/` respondiendo y un piloto completo (login → el personal sube → el cliente ve y descarga → el personal borra) con un proyecto de prueba.
10. `docs/00`, `docs/04` y la bitácora `docs/06` reflejan el estado final del portal.

---

## 10. Preguntas abiertas

| # | Pregunta | Propuesta por defecto |
|---|---|---|
| 1 | ¿Quién administra el DNS? | **Resuelta (21-09-2026):** el único dominio es `empresabkb.cl`, con DNS en DigitalOcean. El portal será `portal.empresabkb.cl` |
| 2 | ¿Se crea una clave de acceso del Space dedicada al portal (no la personal)? | Sí, guardada solo en las variables de App Platform |
| 3 | ¿Quién puede borrar? | **Resuelta (21-09-2026):** el personal borra lo que él subió y el administrador cualquier archivo |

---

## 11. Decisión: estilos del portal (elegida la opción A)

| | A · CSS propio con tokens (recomendada) | B · Tailwind v4 |
|---|---|---|
| Build en el despliegue | Ninguno | Hay que compilar; App Platform con Python no trae Node, así que se compila en local y se versiona el CSS |
| Riesgo | Ninguno | Olvidar recompilar y publicar un CSS desactualizado |
| Coherencia con la landing | Total, viene de los tokens | Total, viene de los tokens |
| Pantallas de la v1 | ≈ 5 (login, proyectos, archivos, subida, error): caben en un CSS corto | Sobra para 5 pantallas |
| Cambiar de idea después | Reescribir clases de las plantillas (barato con 5 pantallas) | Igual |
