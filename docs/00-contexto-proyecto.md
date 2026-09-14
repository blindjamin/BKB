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

---

## 2. Los Dos Productos Digitales
El proyecto se divide en dos aplicaciones complementarias pero técnicamente desacopladas:

1. **Sitio Público (`www.bkb.cl`):**
   - **Objetivo:** Atracción de clientes corporativos, conversión de cotizaciones, recepción de postulaciones (CV) y posicionamiento orgánico (SEO).
   - **Tecnología:** Astro 5+, salida estática (SSG), cero JavaScript innecesario, máxima velocidad (Lighthouse ≥ 95).
   - **Hosting:** DigitalOcean App Platform (nivel estático gratuito).

2. **Portal de Clientes (`portal.bkb.cl`):**
   - **Objetivo:** Plataforma documental privada donde los mandantes e inspectores técnicos pueden consultar el estado de sus obras, verificar vigencia de certificados SEC TE1 y descargar planos As-Built en PDF/DWG.
   - **Tecnología:** Django (Python 3.12+), plantillas renderizadas en servidor con HTMX, base de datos PostgreSQL y archivos en DigitalOcean Spaces (S3 compatible).
   - **Hosting:** DigitalOcean App Platform con workers dedicados y antivirus ClamAV.

---

## 3. Principales Actores y Roles
- **Visitante / Mandante Potencial:** Navega el sitio público, consulta especialidades y envía formularios de cotización o postulación laboral.
- **Cliente BKB (Empresa):** Ingresa al portal mediante credenciales seguras (correo + contraseña Argon2id / Passkey) y accede **únicamente a los documentos de sus propias obras**.
- **Técnico Interno BKB:** Personal de terreno que puede consultar información técnica de todas las obras para faenas de mantenimiento.
- **Administrador BKB:** Personal autorizado que gestiona usuarios, obras y carga nuevos documentos asignando permisos en el momento de la subida.

---

## 4. Estado Actual del Repositorio (al 14-09-2026)
- **Estructura:** Monorepo con `npm workspaces` en la carpeta `bkb-platform/`.
- **Sistema de Diseño (`packages/tokens`):** Implementado con tokens oficiales de color, tipografía y semáforo normativo SEC del UI Kit v1.0.
- **Sitio Público (`apps/web`):**
  - Astro 5+ con salida estática y Tailwind CSS v4 (`@tailwindcss/vite`).
  - 8 rutas completas generadas: `/`, `/servicios`, `/obras`, `/nosotros`, `/contacto`, `/trabaja-con-nosotros`, `/privacidad`, `/terminos`.
  - Galería de 12 fotografías y planos reales de faena integrados en `public/assets/images/`.
  - Helper de rutas (`src/utils/paths.ts`) compatible con local y GitHub Pages.
- **Portal de Clientes (`apps/portal`):** Esqueleto base Django con configuración ASVS Nivel 2, endpoint `/health/` y soporte para SQLite local / PostgreSQL.
- **Despliegue Continuo:** GitHub Action activo para publicar automáticamente en GitHub Pages (`https://blindjamin.github.io/BKB/`) tras cada merge a `desarrollo`.
- **Jerarquía Git:**
  1. `main` (Producción / Primaria)
  2. `desarrollo` (Integración / Secundaria)
  3. Ramas de tarea `[nombre]/[fecha]-[descripcion]` con Pull Request manual a `desarrollo`.
- **Pull Request Actual:** `benjamin/2026-09-14-estilos-tailwind-web` esperando revisión manual del usuario.
