# 06 · Bitácora Cronológica de Avances

> **Propósito de este archivo:**  
> Servir de memoria de trabajo para el equipo y para cualquier modelo de Inteligencia Artificial que retome el proyecto.  
> Cada sesión de trabajo debe cerrar con un nuevo registro fechado que resuma los avances y defina el punto de partida del día siguiente.

---

## Sesión 1 · 14 de Septiembre de 2026

### 1. Resumen de la Jornada
- **Alineación de Requerimientos:** Se ejecutó el proceso de `/grill-me` acordando arquitectura monorepo, tokens oficiales de UI Kit v1.0, sistema dual de documentación, y política estricta de ramas Git.
- **Creación de la Plataforma Base:** Se creó la subcarpeta `bkb-platform/` con workspaces de npm, configurando `.gitignore` y scripts de desarrollo.
- **Tokens de Diseño (`packages/tokens`):**
  - Implementación de variables CSS de marca (`copper-700 #B4470F`, `paper-50 #FBF8F5`, `ink-900 #1A1513`), tipografías (`Space Grotesk`, `IBM Plex Sans`, `IBM Plex Mono`) y semáforo normativo SEC.
- **Sitio Público (`apps/web`):**
  - Configuración con Astro 5+ en modo estático (`output: 'static'`).
  - Maquetación y desarrollo de las 8 rutas requeridas:
    - `/` (Inicio): Hero con titular industrial, badge SEC Clase A, 4 métricas de faena, banner del portal y CTA.
    - `/servicios`: Catálogo técnico de 5 especialidades (`SRV-01` a `SRV-05`) con checklists de alcance.
    - `/obras`: Portafolio de proyectos industriales con ubicaciones, etiquetas técnicas y credenciales.
    - `/nosotros`: Historia de BKB desde 1999, pilares de ejecución y sectores atendidos.
    - `/contacto`: Formulario estructurado con campo trampa honeypot anti-spam.
    - `/trabaja-con-nosotros`: Convocatorias y recepción de CVs cumpliendo con la Ley 21.719 de datos personales.
    - `/privacidad` y `/terminos`: Documentos legales adaptados al marco normativo chileno.
- **Integración de Estilos y Galería Fotográfica:**
  - Instalación e integración de Tailwind CSS v4 (`@tailwindcss/vite`).
  - Migración de 12 fotografías y planos reales a `apps/web/public/assets/images/`.
  - Hero actualizado con layout de 2 columnas y fotografía de faena (`hero-tablero.jpg`).
  - Tarjetas de obras y servicios enriquecidas con vistas previas fotográficas reales.
- **Portal de Clientes (`apps/portal`):**
  - Estructuración base en Django con configuración de seguridad ASVS Nivel 2 (Argon2id, cookies seguras, CSP, endpoint `/health/`).
  - Soporte dual para base de datos SQLite (desarrollo local) y PostgreSQL (producción).
- **Despliegue Continuo (CI/CD):**
  - Creación del workflow `.github/workflows/deploy-pages.yml` para publicación automática en GitHub Pages (`https://blindjamin.github.io/BKB/`).
  - Creación del helper `apps/web/src/utils/paths.ts` para resolución automática de rutas en local (`/`) y Pages (`/BKB/`).
- **Configuración de Git y Repositorio Remoto:**
  - Repositorio remoto vinculado: `https://github.com/blindjamin/BKB.git`.
  - Estructura de 3 niveles establecida:
    1. `main` (Producción)
    2. `desarrollo` (Integración activa)
    3. `[nombre]/[fecha]-[descripcion]` (Ramas de trabajo con Pull Request manual a `desarrollo`).

---

### 2. Estado de Ramas al Cierre del Día
- `main`: Establecida en GitHub (`origin/main`).
- `desarrollo`: Al día con la configuración base y el workflow de GitHub Pages (`origin/desarrollo`).
- `benjamin/2026-09-14-estilos-tailwind-web`: Rama con Tailwind v4 y fotografías de faena.
  - **Pull Request pendiente de merge manual por el usuario:**  
    [Ver Pull Request en GitHub](https://github.com/blindjamin/BKB/pull/new/benjamin/2026-09-14-estilos-tailwind-web).

---

### 3. Plan y Punto de Partida para Mañana (Sesión 2)

Cuando se retome el trabajo en la siguiente sesión, la IA o desarrollador debe realizar lo siguiente:

1. **Paso 1 · Verificar fusión del PR de estilos:**
   - Confirmar si el usuario ya aprobó y fusionó `benjamin/2026-09-14-estilos-tailwind-web` en `desarrollo`.
   - Si ya está fusionado: hacer `git checkout desarrollo && git pull origin desarrollo`.
2. **Paso 2 · Selección de siguiente bloque:**
   - **Opción A (Backend Portal):** Crear la rama `benjamin/YYYY-MM-DD-modelos-portal-django`, levantar el entorno virtual Python (`.venv`), instalar `requirements.txt`, definir los modelos `Empresa`, `Obra`, `Documento` y `DescargaLog`, y registrar el admin de Django.
   - **Opción B (Formularios y Funcionalidad Web):** Conectar los formularios de `/contacto` y `/trabaja-con-nosotros` con un backend serverless, endpoint de correo o Google Workspace relay, incorporando protección Cloudflare Turnstile.
3. **Paso 3 · Recordar protocolo:**
   - Crear siempre rama de tarea `benjamin/YYYY-MM-DD-descripcion`.
   - Push a la rama de tarea.
   - Entregar enlace de Pull Request al usuario para merge manual a `desarrollo`.

---

## Sesión 2 · 15 de Septiembre de 2026

### Resumen
- **Revisión del sitio:** se detectaron 10 pendientes (formularios que enviaban datos por la URL, header roto entre 1024 y 1240 px, contenido de relleno y otros). Se documentaron y el plan de rediseño los resolvió.
- **Corrección del portal:** `requirements.txt` pasó a usar el paquete correcto `rules`.
- **Handoff de Claude Design:** se incorporó a `docs/design/handoff-landing/` y se escribió `08-plan-rediseno-landing.md`.
- **Rediseño implementado** en la rama `benjamin/2026-09-15-rediseno-landing` (ya subida a GitHub), en 4 commits:
  1. Tokens v2: paleta salmón y temas oscuro y claro.
  2. Layout v2, header con menú móvil y footer oscuro.
  3. Landing ensamblada con animaciones, componentes de interfaz e imágenes.
  4. Redirecciones de las rutas antiguas, páginas legales reestilizadas, limpieza y control de calidad.

### Punto de partida
Verificar las fases 8 a 10 del plan 08 y validar el contenido de la lista D7.

---

## Sesión 3 · 20 de Septiembre de 2026

### Resumen
- **Definición del portal:** por entrevista se acordó que el portal es un repositorio de documentos y fotos por proyecto, con tres roles (admin, funcionario, cliente). Lo que sube el cliente es visible de inmediato para todo el proyecto. Lo que sube un funcionario queda interno hasta que se comparte.
- **Especificación aprobada:** `docs/03-portal-django.md` (sustituye al diseño anterior, en que el cliente no subía archivos).
- **Plan de implementación:** `tasks/plan.md` y `tasks/todo.md` (17 tareas en 4 fases, con checkpoints).
- **Decisiones técnicas:** Django 5.2 LTS (el entorno local traía 6.1.1), sin `pytest` (corredor de Django), se quitan `django-htmx`, `rules` y `django-allauth`, CSS propio con tokens en el portal, tema claro por defecto con conmutador, y los archivos antiguos del Space se dejan donde están (el portal usa el prefijo `portal/`).
- **Limpieza:** se eliminaron `docs/07` (revisión ya resuelta por el rediseño), las copias `scratch_buenosvientos.*` (sitio ajeno), `Handoff de pagina.zip` (idéntico a `docs/design/handoff-landing/`) y `UI Kit/BKB UI Kit completo.zip` (copia anterior a la carpeta).
- **Documentación actualizada:** `00`, `01`, `02`, `03`, `04`, `05`, `08` y los README del monorepo y del portal.

### Punto de partida para la próxima sesión
1. Crear la rama del portal desde `desarrollo` (tarea 0) y confirmar la limpieza y actualización de documentos.
2. Antes de la tarea 6, crear en DigitalOcean una clave del Space solo para el portal y configurar CORS.
3. Empezar por las tareas 1 y 2 (entorno y `settings.py`) y seguir el orden de `tasks/todo.md`.

---

## Sesión 4 · 21 de Septiembre de 2026

### Resumen
- **Cambio de requisito:** BKB indicó que el cliente **no puede subir archivos**, solo verlos. Se decidió: dos tipos de usuario (personal y cliente), sin marca interno/compartido (lo que sube el personal se ve de inmediato), el personal ve todos los proyectos y el cliente solo los que se le asignan. El administrador es el superusuario de Django.
- **Spec v1.1** (`docs/03-portal-django.md`) y plan reescritos: de 17 a **16 tareas**. Se eliminó la tarea "Compartir con el cliente", se achicó la matriz de permisos y la subida pasó a ir antes que la descarga. El antivirus dejó de ser condición del lanzamiento.
- **Documentación actualizada:** `00`, `03`, `04`, `tasks/plan.md`, `tasks/todo.md`, el README del portal y la nota de vigencia de `Plan-Implementacion-BKB.md`.

### Punto de partida
Igual que la sesión 3. Decisión posterior del mismo día: **el personal puede borrar lo que él subió y el administrador cualquier archivo** (el cliente nunca). Como el personal no entra al panel de Django, se agregó al plan la tarea 14 "Borrar lo propio": el plan queda en **17 tareas**.


---

## Sesión 5 · 21 de Septiembre de 2026 (ajustes de diseño del landing)

### Resumen
Trabajo iterativo sobre `apps/web`, viendo el resultado en vivo. Los cambios de código ya están en `desarrollo` (commit `07336c1`, PR #4, junto con el portal). Esta rama solo agrega la documentación.

- **Títulos:** en Tailwind v4, `text-[var(--bkb-text-h1)]` se interpreta como color y no como tamaño, así que el h1 del hero se renderizaba a 16 px. Se corrigió con `text-[length:var(--…)]` en `Hero` y `SectionHeading` (los títulos de todas las secciones estaban chicos).
- **Hero:** ocupa toda la pantalla y el carrusel de clientes va superpuesto en la parte inferior, sin fondo, con el título "TRAYECTORIA COMPARTIDA" (antes "CONFÍAN EN BKB") en blanco. La etiqueta dice "Obras Eléctricas & Servicios Industriales · Más de 30 años de trayectoria" (25 pasó a 30 en hero, footer, métricas y metadescripción).
- **Tarjeta del portal:** solo "Soy Cliente →" (se quitó "Soy BKB", porque el login entra siempre por ahí), subtítulo "Gestión Documental" (sin SEC TE1) y el logo circular en lugar del escudo.
- **Logos:** los 16 logos de clientes tenían márgenes blancos distintos y se veían de tamaños dispares; se recortaron. El logo final es circular con fondo transparente (`public/assets/bkb-logo-final.png`). La ruta que pedían el header y el footer no existía y daba 404.
- **Portal SEC:** se eliminó la sección `PortalShowcase` (maqueta del portal) para no mostrar la interfaz a personas ajenas, y también los enlaces "Portal SEC" del header y del footer.
- **Qué hacemos:** tarjetas con foto de fondo y texto centrado. Contenido según empresabkb.cl, quinta tarjeta "Arriendo de Equipos" y carrusel manual infinito.

### Contenido verificado
El usuario confirmó que `https://empresabkb.cl/` (sitio antiguo en producción) es información real. Comparación con el landing:

| Tema | empresabkb.cl (verificado) | Landing |
|---|---|---|
| Servicios | Ingeniería Eléctrica, Automatización PLC, Fabricación Propia, Montaje y Soporte | Ya alineado. Se sumó Arriendo de Equipos (dato del usuario) |
| Mercados | Industrias primarias y minería, EPCs, shutdowns, modernización | Sin respaldo: Agroindustria, Recursos Hídricos, Energía |
| Cifras | Ninguna | Sin respaldo: 150+ proyectos, 40+ clientes, 100 % certificaciones |
| Obras | Ninguna | Sin respaldo: 3 proyectos con kVA |
| Guardia 24/7 y SEC TE1/Clase A | No aparecen | Sin respaldo |
| Cobertura | Chile, norte y centro | Valparaíso y Región Metropolitana |

- **Arriendo de equipos:** instrumentación eléctrica, analizadores, y medidores de tierra, de fuga y de aislación, además de calibración.
- **Teléfonos reales:** `+56 9 8975 3095` y `+56 9 6191 1593`. El landing usa `+56 9 8249 1403` (`config/site.ts`), que no coincide con ninguno.

### Punto de partida
1. Decidir qué hacer con lo que no tiene respaldo (Mercados, métricas, obras, Guardia 24/7, SEC): reescribirlo con el texto verificado, quitarlo, o conservar lo que el usuario confirme como real.
2. Elegir el o los teléfonos que van en `config/site.ts`.
3. Conseguir fotos definitivas para las tarjetas de servicios (hoy son fotos de faena repetidas).
4. Alinear la lista de servicios del footer, que aún dice "Obras Civiles" y "Mantención 24/7".
5. Definir el dominio (`empresabkb.cl` o `bkb.cl`) para el correo y el sitio.

---

## Sesión 6 · 22 de Septiembre de 2026 (portal v1.2: hitos, recepción y jefe)

### Resumen
- **Nuevo requisito de BKB:** al abrir un proyecto, el cliente ve un aviso con el avance por hitos. Cuando se marca el último hito, no ve archivos hasta confirmar "recepcionado y revisado" con el nombre de quien revisó. La confirmación, y el botón "No conforme", mandan un correo a direcciones fijas.
- **Nuevo perfil jefe:** una sola persona que administra empresas, usuarios y proyectos desde una pantalla "Gestión" del portal, sin `/admin/`. Los usuarios crean su contraseña con un enlace que les llega por correo. El superusuario queda solo como cuenta técnica.
- **Spec v1.2 aprobada** (`docs/03`, secciones 12 y 13) y **plan aprobado** (`tasks/plan.md`, "Ampliación v1.2"; tareas 18 a 28 en `tasks/todo.md`).
- **Correo:** por ahora sale por consola. Remitente previsto: `instrumentacion@empresabkb.cl` (Google Workspace). Las direcciones de prueba van solo en el `.env` local.
- **Hallazgo:** `descargar_archivo` y `eliminar_archivo` no pasan por `permisos.py`. Se corrige en la tarea 18, antes que todo lo demás, porque el bloqueo por recepción depende de ello.

### Punto de partida
Seguir la tabla "Orden de ejecución" al inicio de `tasks/todo.md`, empezando por la **tarea 18**.

---

## Sesión 7 · 22 de Septiembre de 2026 (portal v1.3: jerarquía de 3 niveles y carpetas virtuales)

### Resumen
- **Diagnóstico de subida en dev server:** La subida de archivos al Space de DigitalOcean fallaba con HTTP 403 en la petición preflight `OPTIONS` al acceder desde `http://127.0.0.1:8000/`. El Space solo tenía `http://localhost:8000` en su lista blanca de CORS. Se indicó acceder por `http://localhost:8000/` o agregar `127.0.0.1` en la consola de DigitalOcean.
- **Rediseño del flujo de navegación (3 niveles):**
  1. Pantalla principal (`/`): Muestra las empresas/clientes con proyectos vigentes (con botón de acceso rápido `+ Nueva Empresa` para personal/jefe).
  2. Vista de empresa (`/empresas/<uuid>/`): Muestra el historial completo de proyectos de dicha empresa (con botón rápido `+ Nuevo Proyecto`).
  3. Detalle de proyecto (`/proyectos/<uuid>/`): Archivos organizados en raíz o carpetas, con botones `+ Nueva Carpeta` y `+ Subir Archivo`.
  4. Los clientes entran directamente al listado histórico de sus proyectos asociados.
- **Carpetas por proyecto (v1.3):**
  - Personal y jefe pueden crear y eliminar carpetas (de 1 solo nivel, sin árboles anidados para preservar experiencia móvil de 375 px).
  - El cliente tiene acceso de solo lectura al contenido organizado en carpetas.
  - **Invariante de almacenamiento:** Las carpetas son 100% virtuales en la base de datos (modelo `Carpeta` y FK opcional en `Archivo`). En DigitalOcean Spaces la ruta del objeto se mantiene inalterada (`{SPACES_PREFIX}{proyecto_uuid}/{archivo_uuid}`). Crear o borrar carpetas tiene impacto cero en el Space.
- **Documentación actualizada:**
  - `docs/03-portal-django.md`: Sección 14 incorporada con modelos, rutas y reglas de negocio.
  - `tasks/plan.md`: Decisiones de diseño v1.3 y secuencia de trabajo ajustada.
  - `tasks/todo.md`: Tareas 22 (Estructura de empresas y proyectos) y 23 (Carpetas por proyecto) adaptadas con criterios y pruebas completas.
### Avances de Implementación (Tareas 21 y 22)
- **Tarea 21 (Hitos, recepción y bloqueo — núcleo):**
  - Modelos `Hito` (orden, nombre, cumplido_en, cumplido_por) y `RespuestaRecepcion` (usuario, revisor, conforme, fecha, IP).
  - Cálculo derivado de estado en `permisos.estado_proyecto(proyecto)`: `en_curso`, `esperando_recepcion`, `recibido`.
  - Bloqueo de acceso en el servidor: los clientes con proyectos en `esperando_recepcion` quedan bloqueados tanto en el listado de archivos como en la descarga directa por UUID (HTTP 404). Personal, jefe y superusuario nunca se bloquean.
  - Registro de solo lectura en `/admin/` para hitos (inline) y respuestas de recepción.
- **Tarea 22 (Estructura: Empresas activas y proyectos por empresa):**
  - Inicio bifurcado en `/`: personal y jefe ven el catálogo de empresas vigentes con conteo de proyectos activos y botón de acceso rápido `+ Nueva Empresa`; clientes acceden directamente a sus proyectos asignados.
  - Formulario `EmpresaForm` (`/empresas/nueva/`) y vista histórica de proyectos por empresa (`/empresas/<uuid>/`) con botón `+ Nuevo Proyecto`.
  - Formulario `ProyectoForm` (`/proyectos/nuevo/` y `.../editar/`) con validación de hitos multilínea y asignación de clientes.
  - Control de acceso estricto: intentos de acceso o creación por parte de clientes responden HTTP 403.
  - 154 pruebas unitarias ejecutadas con éxito en el portal (100% aprobadas).

### Punto de partida
Seguir la tabla "Orden de ejecución" de `tasks/todo.md`, comenzando por la **Tarea 23 (Carpetas por proyecto y organización de archivos)**.

---

## Sesión 8 · 23 y 24 de Septiembre de 2026 (tareas 23 a 28, checkpoints G y H, DS-1)

### Resumen
- **Forma de trabajo:** tres agentes: un director (armaba el plan de cada tarea y resolvía dudas con la spec), un implementador (skill `incremental-implementation`) y un auditor (pruebas repetidas en orden aleatorio, revisión de seguridad, skill `code-simplification` y commit). Solo se le preguntó al usuario lo que la spec no respondía.
- **Tarea 23 · Carpetas:** modelo `Carpeta` (un nivel) y `Archivo.carpeta` opcional. Crear y eliminar carpetas es solo para personal y jefe; al eliminar una carpeta, sus archivos vuelven a la raíz. La clave en el Space no cambia. Después se arregló la vista de carpeta, que se veía igual que la raíz: ahora el título es la carpeta y aparece "← Volver a".
- **Tarea 24 · Hitos:** "Marcar siguiente hito" y "Deshacer último", en una transacción con bloqueo de fila. No se puede retroceder tras una recepción conforme. `ProyectoForm` ya no deja renombrar ni mover hitos cumplidos.
- **Tarea 25 · Aviso al cliente:** un `<dialog>` con el avance. En "esperando recepción" no se puede cerrar y lleva el formulario de recepción. Funciona sin JS.
- **Tarea 26 · Recepción y correo:** "Conforme" desbloquea los archivos; "No conforme" mantiene el bloqueo. En los dos casos sale un correo (por consola en local). Si el correo falla, la respuesta queda guardada igual.
- **Test intermitente arreglado:** la regex del contrato CSP a veces calzaba dentro del nonce aleatorio. Ahora se quita el nonce antes de buscar; la regla no se debilitó.
- **Tarea 27 · Gestión de usuarios:** app `gestion/`. El jefe crea personal y clientes (nunca jefes) y los desactiva o reactiva. Cada uno recibe un enlace de un solo uso, válido por 3 días, para crear su contraseña. Superusuarios, jefes y el propio jefe no se pueden editar (404).
- **Tarea 28 · "¿Olvidaste tu contraseña?":** la respuesta es la misma exista o no el correo, y se admiten 5 pedidos por IP cada 15 minutos. El jefe también puede recuperar su contraseña.
- **Checkpoints G y H:** la parte automática está cerrada: pruebas, `check` y `check --deploy` con variables ficticias, sin advertencias.
- **DS-1 · Fundaciones de diseño:** `docs/09` aprobado por el usuario el 24-09-2026.
  - Fuentes de marca locales (Google Fonts, OFL) y texto de 18 px.
  - Sprite de 12 íconos y logo recortado (53 KB).
  - `base.html` con "Saltar al contenido", zona única de mensajes y pie con los teléfonos +56 9 8975 3095 y +56 9 6191 1593.
- **Pruebas:** 252, todas en verde.

### Pendiente del usuario
- Flujo manual de los Checkpoints G y H en el navegador (incluye crear un jefe en `/admin/` para ver "Gestión").
- Tecla Esc en el aviso bloqueante.
- Revisiones a 375 y 1280 px de las tareas 22, 23, 25 y DS-1.
- Revisar y fusionar el PR hacia `desarrollo`.

### Alertas para producción (anotadas en la Tarea 15)
- axes detrás del proxy: con 5 fallos de cualquiera se bloquearía a todos.
- Sin `EMAIL_HOST` en producción, los enlaces de contraseña quedarían en los logs.
- Los estáticos no llevan versión en el nombre, así que el navegador puede seguir usando el CSS viejo tras un despliegue.

### Punto de partida
Paso B completado. Siguiente: Paso C (DS-4 y DS-5 con hitos, carpetas y aviso), luego Paso D (DS-6 y DS-7) y la Tarea 15. La Tarea 16 (DigitalOcean) requiere al usuario.

---

## Sesión 9 · 24 de Septiembre de 2026 (Paso B: DS-2, DS-3, Empresas, Formularios, Gestión y Contraseñas)

### Resumen
- **Forma de trabajo:** El paso B lo hizo el usuario con otro asistente (commit `8a1ffda`). El equipo de agentes lo revisó el 25-09-2026: 271 pruebas en verde, sin estilos ni scripts en línea; se corrigió que el conteo de archivos mostrara al cliente datos de un proyecto bloqueado (ver el commit siguiente).
- **DS-2 · Login Institucional:** Panel de marca para escritorio (≥ 900 px) con logo e identidad, tarjeta centrada en móvil (375 px), alternador accesible "Mostrar / Ocultar" contraseña (`login.js` externo cumpliendo CSP), alertas semánticas con `role="alert"` y teléfonos oficiales de asistencia (+56 9 8975 3095 / +56 9 6191 1593).
- **DS-3 · Catálogo de Empresas y Proyectos:** Tarjetas con tipografía de 18 px (`--bkb-text-body-lg`), pastillas de estado (`Activo` / `Cerrado`), optimización de consultas para conteo de archivos y última fecha de carga en `views.py`, foco visible de 3 px y estados vacíos asistidos.
- **Formularios de Empresa y Proyecto:** Estandarización de bordes (radio 10 px), etiquetas permanentes visibles, renderizado accesible de errores (ícono SVG de alerta + texto explicativo) y selector estilizado de clientes mediante casillas ordenadas.
- **Gestión de Usuarios y Contraseñas:** Tabla responsiva en escritorio y tarjetas apiladas en móvil para `/gestion/usuarios/`, filtros combinables (`?rol=&activo=`) con `aria-current`, visibilidad condicional de "Reenviar invitación" (solo cuando está pendiente) y pantallas de invitación, restablecimiento y confirmación de contraseña integradas visualmente.
- **Contrato CSP y Pruebas:** Cero estilos ni manejadores en línea. 271 pruebas unitarias (19 pruebas nuevas cubriendo accesibilidad, filtros, conteos y formularios), todas en verde al 100%.
- **Aislamiento de red:** Cero llamadas o conexiones a DigitalOcean ni CDNs externas; operación 100% local.

### Punto de partida
Diseño: Paso C (DS-4 y DS-5: Detalle de proyecto y archivos con filtro `?tipo=`, subida con cola, panel de hitos, carpetas y aviso modal).
