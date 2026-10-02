# Pendientes (al 01-10-2026)

Todo lo implementado (portal tareas 0 a 28, módulos 1 a 4 de `docs/11`, landing y `/arriendo`) está fusionado en `desarrollo` y `main`. Los planes y listas cumplidos se borraron; quedan en el historial de git. Aquí solo va lo que falta, en orden.

## 1. Alertas de seguridad
Detalle en `docs/04` §6.
- [x] IP real detrás de nginx: `X-Real-IP` para axes, "olvidé mi contraseña", `/cotizar/` y los registros (01-10-2026).
- [x] Chequeo de salud: `/health/` responde antes de los chequeos de Host y HTTPS (01-10-2026).
- [ ] **En espera:** conseguir las cuentas de correo de la empresa (enviar y recibir). Después, decidir qué pasa si falta `EMAIL_HOST` con `DEBUG=False` (propuesta: que no arranque).

## 2. Verificación manual en local
- [ ] Recorrido como personal y como cliente: crear empresa y proyecto con encargados (invitaciones en consola), avanzar hitos, aceptar y rechazar la Revisión, ver archivos al finalizar.
- [ ] Modificaciones: crear, adjuntar, enviar, responder desde el enlace y desde el panel; `manage.py enviar_recordatorios`.
- [ ] Revisar todas las plantillas con `manage.py vista_correos`.
- [ ] Formulario "Cotizar obra" de la landing contra el portal local (`PUBLIC_PORTAL_URL=http://localhost:8000`).
- [ ] `/arriendo`: claro, oscuro, 375 px y 1280 px, teclado, y el mensaje de WhatsApp con 1 y 3 equipos.

## 3. Tarea 16 · Producción en el Droplet
La landing y el portal ya corren en el Droplet (`/srv/BKB-2026`, ver `apps/portal/README.md`). Se descartó App Platform (01-10-2026).
- [ ] Clave del Space **nueva para producción** (Limited, solo `bkb-space`) en `portal.env`, con `SPACES_PREFIX=portal/`, y CORS del Space con `https://portal.empresabkb.cl`. Sin esto no se suben archivos.
- [ ] Primer superusuario (`manage.py createsuperuser` como `bkb`) y jefe designado en `/admin/`.
- [ ] SMTP real con `instrumentacion@empresabkb.cl` (en espera de las cuentas). DigitalOcean bloquea el 587 en Droplets nuevos: puede requerir un ticket de soporte o un proveedor con API.
- [ ] Respaldo periódico de `/srv/BKB-2026/data/portal.sqlite3` (o pasar a PostgreSQL) antes de cargar datos reales.
- [ ] Comprobar: login, una subida y una descarga reales, y un correo real de invitación.

## 4. Tarea 17 · Piloto
- [ ] Un proyecto de prueba con un usuario del personal y un cliente de confianza: alta por el jefe → subida → avance de hitos → Revisión aceptada → el cliente descarga → una modificación respondida.
- [ ] Marcar los criterios de éxito de `docs/03` §9 y `docs/11` y actualizar `docs/00` y `docs/06`.

## 5. Contenido de la landing (antes de publicar)
- [ ] Reemplazar los testimonios inventados (`data/landing.ts`, `TODO`) por reseñas reales.
- [ ] Validar con BKB los textos de uso de `data/arriendo.ts` y conseguir una foto de los equipos para la tarjeta de Arriendo.
- [ ] Contenido sin respaldo en `empresabkb.cl`: mercados, obras del portafolio y menciones a SEC TE1/Clase A. Autorización de los logos de clientes y nombre oficial ("Obras" o "Ingeniería Eléctrica & Servicios").
- [ ] Botón de envío de la cotización con `salmon-700` en vez de `salmon-500` (contraste AA).

## Después de la v1
Ver `docs/03` §15.3 (seguimiento posterior).
