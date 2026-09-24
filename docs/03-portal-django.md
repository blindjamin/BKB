# 03 · Portal de Archivos BKB (`apps/portal`): especificación

> **Estado:** especificación APROBADA v1.2 (22-09-2026), sobre la v1.1 (21-09-2026). Plan de implementación: [`tasks/plan.md`](../tasks/plan.md). Tareas: [`tasks/todo.md`](../tasks/todo.md).
> **Sustituye** al diseño anterior de este documento, que quedó desactualizado.
> **Origen:** entrevista de intención con el usuario (20-09-2026).
> **Cambios de la v1.1 (21-09-2026):** BKB indicó que el cliente **no puede subir archivos**, solo verlos. Por eso: (1) los roles pasan de tres a dos, (2) se elimina la marca interno/compartido, (3) todo el personal ve todos los proyectos, y (4) el personal puede borrar lo que él subió (el administrador, cualquier archivo).
> **Cambios de la v1.2 (22-09-2026):** BKB pidió **hitos por proyecto con aviso al cliente y recepción obligatoria**. (1) El personal crea proyectos y su lista de hitos **desde el portal**, y los marca en orden. (2) Al abrir un proyecto, el cliente ve un aviso con el avance. (3) Cuando se marca el último hito, el cliente **no ve archivos** hasta confirmar "recepcionado y revisado" con el nombre de quien revisó. (4) La confirmación, y el botón "No conforme", **envían un correo** a direcciones fijas de BKB. (5) Se agrega el perfil **jefe**: una sola persona que administra empresas, usuarios y proyectos desde una pantalla del portal, sin usar `/admin/`. Los usuarios nuevos crean su contraseña con un enlace que les llega por correo. Detalle en las secciones 12 y 13.
> **Cambios de la v1.3 (22-09-2026):** BKB pidió reorganizar la navegación en una jerarquía de 3 niveles: (1) Tras el login, el personal y el jefe ven las **empresas con proyectos vigentes** (con botón de acceso rápido `+ Nueva Empresa`); (2) Al seleccionar una empresa, se despliega el **historial de proyectos** de ese cliente (activos y cerrados, con botón `+ Nuevo Proyecto`); (3) Dentro de cada proyecto, el personal y el jefe pueden **crear carpetas** para organizar fotos y documentos de forma ordenada (con botón `+ Nueva Carpeta`). El cliente solo tiene vista de solo lectura. Las carpetas son 100% virtuales en base de datos (las claves del Space no cambian). Detalle en la sección 14.

---

## 1. Objetivo

Portal web donde el **personal de BKB sube documentos y fotos de cada proyecto** y los **clientes los consultan y descargan**, cada cliente solo en los proyectos que se le asignan. Reemplaza el envío de archivos por correo y el uso manual del Space.

**Usuarios y qué pueden hacer**

| Quién | Ve proyectos | Ve archivos | Sube | Borra |
|---|---|---|---|---|
| **Personal de BKB** | Todos | Todos | Sí | **Solo lo que él subió** |
| **Cliente** | Solo los que se le asignan | Todos los de esos proyectos | **No** | **No** |
| **Jefe** (v1.2, una sola persona) | Todos | Todos | Sí | **Cualquier archivo** |

Desde la v1.2, **el jefe es el administrador del negocio**. Hace todo lo del personal y además, desde la pantalla **Gestión** del portal (sección 13), crea y edita empresas y usuarios. **No usa `/admin/`.** El personal y el jefe crean proyectos, hitos y asignaciones desde el portal (sección 12).
El **superusuario de Django** queda solo como cuenta técnica del informático (mantenimiento, casos raros y designar al jefe) y no participa en el uso diario.

**Reglas centrales**

1. El **personal** ve todos los proyectos y todos los archivos.
2. Un **cliente** ve únicamente los proyectos que se le asignaron y, dentro de ellos, todos los archivos, **salvo cuando el proyecto espera su recepción** (sección 12): ahí no ve ni descarga ningún archivo hasta confirmar.
3. Un proyecto no asignado **no existe** para el cliente: ni en listados ni por enlace directo. Se responde **404** (no 403), para no revelar que existe.
4. **Solo el personal sube.** Un archivo subido se ve **de inmediato** para los clientes asignados al proyecto. No hay paso de revisión dentro del sistema: se asume que el personal capacitado revisa antes de subir.
5. Un cliente que intente subir, confirmar o borrar recibe **403**.
6. **Borrar:** el personal puede borrar los archivos que él mismo subió, y el jefe (y el superusuario técnico) cualquiera. Borrar es lógico y el archivo **desaparece al instante para todos**. El personal que intente borrar un archivo ajeno recibe 403.

**Éxito:** el personal entra, sube un archivo a un proyecto, y el cliente asignado lo ve y lo descarga. Si el personal se equivoca, borra su archivo y deja de verse. Un cliente no ve proyectos ajenos ni sus archivos.

**Restricciones:** lo desarrolla una persona con apoyo de IA; sin fecha (terminar lo antes posible); el costo de infraestructura importa (objetivo ≈ US$ 27/mes: 1 instancia, PostgreSQL gestionado y el Space actual; sin staging ni worker al inicio).

**Fuera de alcance de la v1:** subida de archivos por clientes, marca interno/compartido, asignación de proyectos al personal, migrar los archivos antiguos del Space (se dejan donde están; solo el personal los abre directo en DigitalOcean), facturas o ERP, firma electrónica, app móvil, visor DWG, miniaturas y previsualización, avisos por correo **al subir archivos** (sí hay correo al confirmar o rechazar la recepción, sección 12), Google SSO, 2FA, subcarpetas anidadas de profundidad infinita (la v1.3 contempla carpetas de un solo nivel por proyecto) y un panel de administración propio más allá de la pantalla Gestión del jefe (sección 13).

**Si más adelante piden que el cliente suba o solicite documentos:** el acceso está centralizado en `permisos.py`, así que el cambio se concentra ahí y reutiliza el flujo de subida.

---

## 2. Suposiciones

Confirmadas por el usuario el 20-09-2026 y ajustadas el 21-09-2026 (las 6 y 8 cambiaron; la 5 se precisó).

1. **Login:** correo + contraseña de Django, cuentas creadas por el administrador, sin registro público. Google SSO y passkeys quedan para después.
2. **Administrador = superusuario de Django** (por ahora una sola persona, tú). Usa el panel `/admin/` para crear empresas, usuarios, proyectos y asignaciones, y puede borrar cualquier archivo. El personal que no es superusuario no entra al panel: borra desde el portal. **Reemplazada en la v1.2:** lo operativo pasa al **jefe** desde el portal (sección 13) y el superusuario queda solo como cuenta técnica.
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
EMAIL_HOST=                   EMAIL_PORT=587             EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=          DEFAULT_FROM_EMAIL=        (v1.2, sección 12)
AVISO_RECEPCION_CORREOS=      (lista separada por comas; vacía en local = el correo se imprime en consola)
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
| `Usuario` | correo (login), `nombre` (v1.2), `rol` (`personal`/`cliente`/`jefe`, v1.2). Sin empresa propia. El superusuario es `personal`. **Como máximo un jefe activo** |
| `Proyecto` | `id`, `empresa`, `nombre`, `estado` (`activo`/`cerrado`) |
| `Membresia` | `usuario` (solo clientes), `proyecto` (único por par). Asignar personal se rechaza |
| `Carpeta` (v1.3) | `id`, `proyecto`, `nombre`, `creado_en`, `creado_por`. Único por (`proyecto`, `nombre`) |
| `Archivo` | `id`, `proyecto`, `carpeta` (opcional, v1.3), `nombre_original`, `clave_space`, `tamano`, `tipo`, `subido_por`, `estado` (`pendiente`/`disponible`), `subido_en`, `eliminado_en`, `eliminado_por` |
| `DescargaLog` | `usuario`, `archivo`, `fecha`, `ip` |
| `Hito` (v1.2) | `id`, `proyecto`, `orden`, `nombre`, `cumplido_en`, `cumplido_por`. Único por (`proyecto`, `orden`) |
| `RespuestaRecepcion` (v1.2) | `id`, `proyecto`, `usuario` (el cliente que responde), `nombre_revisor`, `conforme` (sí/no), `fecha`, `ip`. Nunca se edita ni se borra desde el portal |

**Rutas**

| Ruta | Quién | Función |
|---|---|---|
| `/login/`, `/logout/` | Todos | Acceso |
| `/` | Personal/Jefe: empresas vigentes · Cliente: proyectos asignados | Entrada principal según perfil |
| `/empresas/nueva/` (v1.3) | Personal y Jefe | Botón rápido para crear empresa |
| `/empresas/<uuid>/` (v1.3) | Todos (según asignación) | Historial de proyectos de la empresa (con botón "+ Nuevo Proyecto") |
| `/proyectos/<uuid>/` | Todos | Detalle del proyecto (hitos, carpetas, archivos) |
| `POST /proyectos/<uuid>/carpetas/nueva/` (v1.3) | Personal y Jefe | Crear carpeta en el proyecto |
| `POST /carpetas/<uuid>/eliminar/` (v1.3) | Personal y Jefe | Eliminar carpeta vacía |
| `POST /proyectos/<uuid>/subir/` | Personal y Jefe | Inicia la subida (acepta `carpeta_id` opcional): valida y devuelve POST prefirmado |
| `POST /archivos/<uuid>/confirmar/` | Personal y Jefe (quien subió) | Confirma la subida: verifica existencia y tamaño en el Space |
| `GET /archivos/<uuid>/descargar/` | Todos | Responde 302 a una URL prefirmada de 60 s |
| `POST /archivos/<uuid>/eliminar/` | Personal (lo propio), Jefe y superusuario (cualquiera) | Borrado lógico: oculta el archivo al instante |
| `/proyectos/nuevo/` (v1.2) | Personal y Jefe | Crear proyecto: empresa, nombre, hitos y clientes asignados |
| `/proyectos/<uuid>/editar/` (v1.2) | Personal y Jefe | Cambiar nombre, clientes e hitos aún no cumplidos |
| `POST /proyectos/<uuid>/hitos/avanzar/` y `/retroceder/` (v1.2) | Personal y Jefe | Marca el siguiente hito o desmarca el último marcado |
| `POST /proyectos/<uuid>/recepcion/` (v1.2) | Cliente asignado | Confirma ("conforme") o rechaza ("no conforme") y envía el correo |
| `/gestion/usuarios/`, `/gestion/usuarios/nuevo/`, `/gestion/usuarios/<uuid>/` (v1.2) | Jefe | Listar, crear, editar, desactivar o reactivar usuarios y reenviar la invitación |
| `/contrasena/crear/<uidb64>/<token>/` (v1.2) | Quien recibe el enlace | Crear o restablecer la contraseña (vista estándar de Django) |
| `/contrasena/olvide/` (v1.2) | Todos | Pedir el enlace por correo. La respuesta es la misma exista o no el correo |
| `/admin/`, `/health/` | Superusuario técnico / monitoreo | Panel de Django (solo el informático) y salud del servicio |

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
- **Hitos y recepción (v1.2):** la matriz de permisos suma el eje "estado del proyecto" (en curso, esperando recepción, recibido) para el cliente en **listado, descarga y UUID directo**; el personal ve todo en los tres. Hitos: solo se avanza al siguiente y solo se retrocede el último; un cliente que intenta avanzar recibe 403; no se retrocede si ya hay recepción conforme. Recepción: sin nombre de revisor se rechaza; personal o cliente no asignado no pueden responder; "conforme" desbloquea y "no conforme" no; ambos dejan registro y mandan un correo (`django.core.mail.outbox`); si el envío falla, la respuesta igual queda guardada.
- **Jefe y gestión (v1.2):** `/gestion/` responde 403 al personal y al cliente. El jefe crea empresas y usuarios, pero no puede crear otro jefe ni un superusuario, cambiarse el rol ni desactivarse. Solo puede existir un jefe activo. Crear un usuario manda la invitación (`mail.outbox`) y el enlace permite fijar la contraseña una sola vez. Un usuario desactivado no entra ni ve nada. "Olvidé mi contraseña" responde igual exista o no el correo. El jefe puede borrar cualquier archivo.
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
- Dejar que el personal borre archivos que subió otra persona (solo el jefe y el superusuario pueden).
- (v1.2) Dejar que el jefe cree o edite superusuarios u otro jefe, se cambie su propio rol o se desactive a sí mismo.
- (v1.2) Que el jefe o cualquier pantalla del portal vea, escriba o envíe una contraseña: se crean solo con el enlace por correo.
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
11. (v1.2) El personal crea un proyecto con sus hitos desde el portal, sin entrar a `/admin/`, y los marca en orden.
12. (v1.2) El cliente ve el aviso con el avance al abrir el proyecto y, mientras no se marque el último hito, lo cierra y ve los archivos.
13. (v1.2) Con el último hito marcado y sin recepción conforme, el cliente no ve ni descarga ningún archivo del proyecto (lista vacía y descarga 404, también por enlace directo), aunque desactive JavaScript.
14. (v1.2) Al confirmar con el nombre del revisor, los archivos vuelven a verse y llega un correo a `AVISO_RECEPCION_CORREOS`. "No conforme" también manda un correo y mantiene el bloqueo.
15. (v1.2) El jefe, sin entrar a `/admin/`, crea una empresa y un cliente. El cliente recibe un correo, crea su contraseña con el enlace y entra al portal. Un usuario de tipo personal que abre `/gestion/` recibe 403.

---

## 10. Preguntas abiertas

| # | Pregunta | Propuesta por defecto |
|---|---|---|
| 1 | ¿Quién administra el DNS? | **Resuelta (21-09-2026):** el único dominio es `empresabkb.cl`, con DNS en DigitalOcean. El portal será `portal.empresabkb.cl` |
| 2 | ¿Se crea una clave de acceso del Space dedicada al portal (no la personal)? | Sí, guardada solo en las variables de App Platform |
| 3 | ¿Quién puede borrar? | **Resuelta (21-09-2026):** el personal borra lo que él subió y el administrador cualquier archivo |
| 4 | (v1.2) Si hay varios clientes asignados, ¿basta la confirmación de uno para desbloquear a todos? | **Resuelta (22-09-2026):** sí. La recepción es del proyecto y queda el nombre de quien revisó |
| 5 | (v1.2) ¿Qué direcciones reciben los correos? | **Resuelta (22-09-2026):** el correo del jefe. Va en la variable `AVISO_RECEPCION_CORREOS`, no en el código. **Mientras tanto (pruebas):** el jefe y el destinatario son dos correos del desarrollador, definidos solo en el `.env` local |
| 6 | (v1.2) ¿Desde qué cuenta se envían los correos? | **Resuelta (22-09-2026):** `instrumentacion@empresabkb.cl` (Google Workspace, `smtp.gmail.com:587` con STARTTLS y una contraseña de aplicación). **Por ahora los correos salen por consola** (`EMAIL_HOST` vacío), también en las pruebas manuales. Conectar la cuenta queda pendiente: requiere verificación en dos pasos y una contraseña de aplicación. **Verificar que App Platform permita SMTP saliente por el puerto 587**; si no, se necesita un proveedor con API (dependencia nueva: preguntar) |
| 7 | (v1.2) ¿Quién crea las empresas y las cuentas? | **Resuelta (22-09-2026):** el **jefe**, desde la pantalla Gestión del portal (sección 13). El personal solo elige empresas y clientes que ya existen |
| 8 | (v1.2) ¿Qué pasa con un proyecto que ya tiene recepción conforme y luego se le agregan archivos o hitos? | **Resuelta (22-09-2026), por ahora:** sigue desbloqueado. En la v1 no se agregan hitos después de la recepción |

---

## 11. Decisión: estilos del portal (elegida la opción A)

| | A · CSS propio con tokens (recomendada) | B · Tailwind v4 |
|---|---|---|
| Build en el despliegue | Ninguno | Hay que compilar; App Platform con Python no trae Node, así que se compila en local y se versiona el CSS |
| Riesgo | Ninguno | Olvidar recompilar y publicar un CSS desactualizado |
| Coherencia con la landing | Total, viene de los tokens | Total, viene de los tokens |
| Pantallas de la v1 | ≈ 5 (login, proyectos, archivos, subida, error): caben en un CSS corto | Sobra para 5 pantallas |
| Cambiar de idea después | Reescribir clases de las plantillas (barato con 5 pantallas) | Igual |

---

## 12. Hitos del proyecto y recepción del cliente (v1.2)

**Por qué:** BKB quiere que el cliente vea en qué va su proyecto y que, al terminarlo, **deje constancia de que lo recibió y revisó** antes de seguir usando los archivos. El personal recibe esa confirmación por correo, sin tener que entrar al portal a revisar.

### 12.1 Flujo

```
Login → Mis proyectos → clic en un proyecto
                          │
                          ├─ Personal: panel de hitos con casillas (sin aviso) + archivos
                          │
                          └─ Cliente: AVISO con la lista de hitos y el actual
                                ├─ En curso (falta marcar hitos): "Cerrar" → ve los archivos
                                ├─ Esperando recepción (todos marcados, sin conforme):
                                │     no se puede cerrar ni ver archivos
                                │     [Nombre de quien revisó] [✓ Recepcionado y revisado]
                                │     (Confirmar)   (No conforme)
                                └─ Recibido: aviso informativo, "Cerrar" → ve los archivos
```

### 12.2 Estados del proyecto (se calculan, no se guardan)

| Estado | Condición | Cliente ve archivos |
|---|---|---|
| **En curso** | Queda al menos un hito sin marcar | Sí |
| **Esperando recepción** | Todos los hitos marcados y no hay `RespuestaRecepcion` conforme | **No** |
| **Recibido** | Hay una `RespuestaRecepcion` conforme | Sí |

- El estado **se deriva** de `Hito` y `RespuestaRecepcion`, sin campo propio. Así no hay dos fuentes que puedan contradecirse.
- El campo actual `Proyecto.estado` (`activo`/`cerrado`) se mantiene como está y no interviene en el bloqueo.
- Todo proyecto tiene **al menos un hito**. El formulario lo exige.

### 12.3 Reglas

1. **Crear proyecto (personal, en el portal):** empresa (de una lista existente), nombre, hitos en orden (texto libre, uno por línea o con "agregar hito") y clientes asignados (solo de tipo cliente). Crear empresas y cuentas sigue siendo del administrador en `/admin/`.
2. **Editar:** el personal renombra, reordena, agrega o quita hitos **aún no marcados**, y cambia los clientes asignados. Los hitos ya marcados no se editan.
3. **Marcar hitos:** solo el siguiente sin marcar (`avanzar`) y solo el último marcado (`retroceder`). Se registra quién y cuándo. No se retrocede si ya hay recepción conforme.
4. **Aviso al cliente:** sale **cada vez** que abre el proyecto. Es un `<dialog>` nativo con JS externo (compatible con la CSP, sin estilos ni manejadores en línea). Sin JS, el mismo contenido se ve arriba de la página.
5. **Bloqueo:** en "esperando recepción", `permisos.archivos_visibles` devuelve **vacío para el cliente**. Por eso la lista sale vacía y la descarga da **404**, también por enlace directo. **El bloqueo es del servidor, no del aviso.**
6. **Confirmar:** exige el nombre del revisor y la casilla "Recepcionado y revisado". Crea `RespuestaRecepcion(conforme=True)`, desbloquea para **todos** los clientes del proyecto y envía el correo de conforme.
7. **No conforme:** exige el nombre de quien revisó. Crea `RespuestaRecepcion(conforme=False)` y envía un correo que dice que la recepción no se hizo y que el cliente será contactado para solucionarlo. **El bloqueo sigue** y el cliente puede confirmar más tarde.
8. **Correo:** con `django.core.mail.send_mail` (sin dependencias nuevas) a `AVISO_RECEPCION_CORREOS`. Incluye proyecto, empresa, resultado, nombre del revisor, correo del cliente y fecha. Si el envío falla, **la respuesta se guarda igual** y el error queda en el log: el cliente no pierde su confirmación por un problema de correo.
9. **Permisos nuevos en `permisos.py`:** `estado_proyecto(proyecto)`, `puede_gestionar_hitos(usuario)` (personal y jefe) y `puede_responder_recepcion(usuario, proyecto)` (cliente asignado, proyecto esperando recepción). Las vistas no deciden con ifs propios.
10. El personal, el jefe y el superusuario **nunca** quedan bloqueados.

### 12.4 Qué cambia respecto de la v1.1

| Área | v1.1 | v1.2 |
|---|---|---|
| Crear proyectos | Solo el administrador en `/admin/` | El personal y el jefe, desde el portal |
| Empresas y usuarios | El administrador en `/admin/` | El jefe, en la pantalla Gestión (sección 13) |
| Qué ve el cliente | Todos los archivos de sus proyectos | Todos, salvo mientras el proyecto espera su recepción |
| Correo | Fuera de alcance | Al confirmar o rechazar la recepción, y para las invitaciones y la recuperación de contraseña |
| Modelos | 5 | 7 (`Hito`, `RespuestaRecepcion`) |
| Pantallas | ≈ 5 | ≈ 7 (formulario de proyecto y aviso) |

### 12.5 Fuera de alcance (v1.2)

Plantillas de hitos reutilizables (se agregan si repiten siempre la misma lista), fechas estimadas por hito, comentarios del cliente en el portal (el "no conforme" se resuelve por teléfono o correo), correo al cliente cuando avanza un hito, y firma electrónica de la recepción.

---

## 13. Jefe y pantalla de gestión (v1.2)

**Por qué:** el administrador de la v1.1 tenía que usar `/admin/`, que solo maneja bien un informático. BKB quiere que **el jefe** administre todo desde una pantalla simple del portal.

### 13.1 Perfiles

| Perfil | Qué es | Cómo se crea |
|---|---|---|
| **Cliente** | Ve sus proyectos asignados y confirma la recepción | Lo crea el jefe |
| **Personal** | Sube, borra lo suyo, crea proyectos y marca hitos | Lo crea el jefe |
| **Jefe** | Todo lo del personal + Gestión + borra cualquier archivo | Lo designa el superusuario en `/admin/` (una vez, o cuando cambie el jefe) |
| **Superusuario** | Cuenta técnica del informático | `createsuperuser` |

- El jefe es un **valor más de `rol`** (`jefe`), no un permiso de Django. Todas las reglas lo tratan como personal, más lo propio de su perfil.
- **Solo puede haber un jefe activo.** El modelo lo valida: designar un segundo jefe se rechaza con un mensaje claro.
- El jefe **no entra a `/admin/`** (sigue reservado al superusuario).

### 13.2 Qué hace el jefe en Gestión

| Sección | Puede | No puede |
|---|---|---|
| **Empresas** | Crear, editar nombre y RUT, y ver sus proyectos | Borrar (los proyectos dependen de ellas) |
| **Usuarios** | Crear personal y clientes (nombre, correo, tipo), editar nombre y tipo, desactivar, reactivar y reenviar la invitación | Crear o editar jefes y superusuarios, cambiarse el rol, desactivarse, ver o fijar contraseñas, borrar usuarios (se desactivan, para no perder el registro de quién subió o descargó) |
| **Proyectos** | Lo mismo que el personal (sección 12), sobre cualquier proyecto | — |
| **Archivos** | Borrar cualquiera | — |

Desactivar a un usuario **cierra su acceso al instante**: `permisos.py` ya trata como sin acceso a quien está inactivo.

### 13.3 Contraseñas por enlace

1. El jefe crea el usuario **sin contraseña** (no se puede usar para entrar).
2. El portal envía un correo de invitación con un enlace de un solo uso para crear la contraseña. Usa el generador de tokens de Django y `PasswordResetConfirmView`, sin dependencias nuevas. El enlace **vence a los 3 días** (`PASSWORD_RESET_TIMEOUT`).
3. Si vence, el jefe pulsa "Reenviar invitación".
4. La misma pieza da **"¿Olvidaste tu contraseña?"** en el login. La respuesta es idéntica exista o no el correo, y queda sujeta al límite de intentos.
5. Las contraseñas pasan por los validadores de Django y se guardan con Argon2id, como ya está.

**Consecuencia:** el correo pasa a ser **necesario para dar de alta usuarios**, no solo para los avisos de recepción. Sin la cuenta `@empresabkb.cl` funcionando, el lanzamiento queda bloqueado. En local, los correos se imprimen en la consola.

### 13.4 Permisos nuevos en `permisos.py`

```python
def es_jefe(usuario):
    return _activo(usuario) and usuario.rol == Rol.JEFE

def puede_borrar(usuario, archivo):
    return _es_personal(usuario) and (
        usuario.is_superuser or es_jefe(usuario) or archivo.subido_por_id == usuario.pk
    )
```

`_es_personal` pasa a incluir al jefe. Las vistas de `/gestion/` exigen `es_jefe` y responden 403 a cualquier otro usuario con sesión.

### 13.5 Fuera de alcance

Varios jefes o permisos a medida por persona, historial de cambios de Gestión (quién editó qué), carga masiva de usuarios, borrado de empresas o usuarios y cambio del correo de un usuario por él mismo.

---

## 14. Jerarquía de navegación y Carpetas por proyecto (v1.3)

**Por qué:** Para evitar una lista plana de proyectos desordenada cuando crecen los clientes y los trabajos, BKB organiza la estructura en 3 niveles: **Empresa (Cliente)** → **Proyectos históricos** → **Carpetas y Archivos**. Además, el personal y el jefe disponen de botones de fácil acceso para crear empresas, proyectos y carpetas sobre la marcha sin rodeos administrativos.

### 14.1 Jerarquía y flujo de navegación

```
Login → [ / ]
          │
          ├─ Personal / Jefe:
          │     │
          │     ▼
          │   Lista de Empresas con proyectos vigentes (con [+ Nueva Empresa])
          │     │
          │     ▼ (Clic en empresa)
          │   [ /empresas/<uuid>/ ]
          │   Historial completo de proyectos de la empresa (con [+ Nuevo Proyecto])
          │     │
          │     ▼ (Clic en proyecto)
          │   [ /proyectos/<uuid>/ ]
          │   Detalle del proyecto: panel de hitos, carpetas ([+ Nueva Carpeta]) y archivos ([+ Subir])
          │
          └─ Cliente:
                │
                ▼
              Lista directa de sus proyectos asignados (o selector de empresas si tiene varias asignadas).
              Al abrir un proyecto ve las carpetas y archivos en modo solo lectura.
```

### 14.2 Carpetas virtuales por proyecto

1. **Modelo `Carpeta`:**
   - `id`: UUID.
   - `proyecto`: ForeignKey a `Proyecto` (`on_delete=models.CASCADE`, `related_name='carpetas'`).
   - `nombre`: `CharField(max_length=100)`.
   - `creado_en`: `DateTimeField(auto_now_add=True)`.
   - `creado_por`: ForeignKey al usuario (`on_delete=models.PROTECT`).
   - `unique_together`: `[('proyecto', 'nombre')]` (no puede haber dos carpetas con el mismo nombre en un proyecto).
2. **Relación con `Archivo`:**
   - `Archivo.carpeta`: ForeignKey opcional (`null=True, blank=True, on_delete=models.SET_NULL`, `related_name='archivos'`).
   - Los archivos sin carpeta se listan en la raíz del proyecto.
   - Si se elimina una carpeta, sus archivos no se borran: vuelven a la raíz (`SET_NULL`).
3. **Almacenamiento en DigitalOcean Spaces (invariable):**
   - La clave en el Space sigue siendo `{SPACES_PREFIX}{proyecto_uuid}/{archivo_uuid}`.
   - Las carpetas viven **exclusivamente en la base de datos**. Renombrar, mover o borrar carpetas no toca el Space.

### 14.3 Permisos y reglas de acceso

1. **Empresas activas:**
   - `permisos.empresas_visibles(usuario)`: para personal y jefe devuelve las empresas que tienen proyectos vigentes; para clientes devuelve las empresas de sus proyectos asignados.
2. **Proyectos de la empresa:**
   - `permisos.proyectos_de_empresa(usuario, empresa)`: personal y jefe ven todos los proyectos de esa empresa (activos y cerrados); el cliente ve solo los que se le asignaron en esa empresa.
3. **Carpetas:**
   - Solo el personal y el jefe pueden crear (`POST /proyectos/<uuid>/carpetas/nueva/`) o eliminar carpetas vacías (`POST /carpetas/<uuid>/eliminar/`).
   - El cliente solo consulta las carpetas existentes y descarga sus archivos autorizados.
4. **Bloqueo por recepción (v1.2):**
   - Si el proyecto está en `esperando_recepcion`, el cliente queda bloqueado de ver archivos **en todas las carpetas y en la raíz**.

### 14.4 Botones de acción rápida

- En `/`: botón `+ Nueva Empresa` (formulario simple con nombre y RUT).
- En `/empresas/<uuid>/`: botón `+ Nuevo Proyecto` (con la empresa preseleccionada).
- En `/proyectos/<uuid>/`: botón `+ Nueva Carpeta` y botón `+ Subir Archivo` (con selector de carpeta destino).
