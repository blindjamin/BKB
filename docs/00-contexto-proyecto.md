# 00 · Contexto del Proyecto BKB

> **Nota para IAs y nuevos desarrolladores:**  
> Este documento resume el propósito, negocio, actores y decisiones estratégicas de la plataforma BKB. Léalo antes de realizar cualquier cambio arquitectónico.

---

## 1. ¿Qué es BKB?
**BKB Obras Eléctricas & Servicios** es una empresa chilena de ingeniería eléctrica industrial con más de 25 años de trayectoria (fundada en 1999). Sus principales áreas de negocio son:
1. **Montaje de Tableros Eléctricos:** Tableros de Distribución de Fuerza (TDF), Tableros de Alumbrado (TDA) y Centros de Control de Motores (CCM).
2. **Automatización y Control:** Programación de autómatas PLC (Siemens, Schneider, Allen-Bradley), telemetría y SCADA.
3. **Obras Civiles Eléctricas:** Tendido de escalerillas portacables, mallas de puesta a tierra y salas eléctricas.
4. **Regularizaciones Normativas:** Tramitación y obtención de declaraciones eléctricas **SEC TE1** (Superintendencia de Electricidad y Combustibles), contando con categoría máxima **SEC Clase A**.
5. **Mantención Industrial:** Termografía infrarroja certificada, ajuste de torque y guardia técnica 24/7.

> **Pendiente de definir:** el logo nuevo dice "Ingeniería Eléctrica & Servicios", pero los documentos y la metadata dicen "Obras Eléctricas & Servicios". Hay que decidir cuál es el nombre oficial (afecta `<title>`, Schema.org y footer).

---

## 2. Los Dos Productos Digitales
Son dos aplicaciones con objetivos distintos y técnicamente desacopladas:

1. **Sitio Público (`www.empresabkb.cl`):**
   - **Objetivo:** vender la empresa y generar confianza en futuros clientes corporativos, recibir solicitudes de cotización y postulaciones (CV), y posicionarse en buscadores.
   - **Tecnología:** Astro 5 (salida estática), Tailwind CSS v4 y `@bkb/tokens`. Sin servidor: el formulario "Cotizar obra" publica en `/cotizar/` del portal.
   - **Estado:** landing de una página y `/arriendo` terminadas; falta validar contenido con BKB (ver `tasks/todo.md` §5).
   - **Hosting:** hoy se previsualiza en GitHub Pages; el destino es DigitalOcean App Platform (sitio estático).

2. **Portal de Proyectos (`portal.empresabkb.cl`):**
   - **Objetivo:** que el cliente siga el avance de su proyecto, apruebe o rechace la Revisión final y las modificaciones que BKB le propone, y descargue los documentos y fotos al finalizar. **Es el propósito principal de la plataforma.**
   - **Tecnología:** Django 5.2 LTS, plantillas en servidor, PostgreSQL y los archivos en un DigitalOcean Space privado (`bkb-space`).
   - **Estado:** completo en local (spec base `03-portal-django.md` más los 4 módulos de `11-spec-avance-y-modificaciones.md`). Falta el despliegue (tarea 16) y el piloto (tarea 17).
   - **Hosting:** DigitalOcean App Platform, una sola instancia, más PostgreSQL gestionado (`.do/app.yaml`).

---

## 3. Principales Actores y Roles
- **Visitante / Mandante potencial:** navega el sitio público, cotiza obras o arriendo de equipos (WhatsApp) y postula.
- **Personal de BKB:** ve todos los proyectos y sube y organiza archivos en carpetas. Solo los **encargados BKB** de un proyecto (y el jefe) avanzan hitos, editan el proyecto y crean modificaciones.
- **Jefe:** una persona que administra empresas, usuarios y proyectos desde Gestión, con invitaciones por correo.
- **Cliente:** el **encargado** de una empresa ve todos sus proyectos; el encargado de un proyecto, solo ese. Durante el proyecto ve el avance y las modificaciones; los archivos se le muestran al aceptar la Revisión.
- **Administrador:** superusuario de Django, para lo técnico (designar al jefe, `changepassword`).
- **Ingeniería (`ingenieria@empresabkb.cl`):** recibe copia de los correos del portal y las cotizaciones.

---

## 4. Estado Actual (al 01-10-2026)
- **Ramas:** todo el trabajo está fusionado en `desarrollo` y en `main` (PR #21). Flujo en `05-git-workflow.md`.
- **Tokens (`packages/tokens`):** tema oscuro y tema claro grafito y naranjo, más el semáforo SEC. Ver `01-tokens-y-sistema-diseno.md`.
- **Sitio público (`apps/web`):** landing (hero con carrusel de clientes, "Qué hacemos" con fotos reales, mercados, portafolio, testimonios provisorios y contacto con formulario y mapa), `/arriendo`, `/trabaja-con-nosotros`, `/privacidad`, `/terminos` y `404`. Ver `02-sitio-web-astro.md`.
- **Portal (`apps/portal`):** empresas → proyectos → carpetas, encargados, 7 hitos con Revisión del cliente, correos HTML con copia a ingeniería, modificaciones con enlace firmado y recordatorios, gestión de usuarios y recuperación de contraseña. Ver `03-portal-django.md` y `11-spec-avance-y-modificaciones.md`.
- **Despliegue continuo:** GitHub Action que publica el sitio estático en GitHub Pages (`https://blindjamin.github.io/BKB/`) con cada push a `desarrollo`.

### Pendientes abiertos
La lista única y ordenada está en [`tasks/todo.md`](../tasks/todo.md): la alerta de correo en espera, verificación manual, despliegue (tarea 16), piloto (tarea 17) y contenido de la landing.
