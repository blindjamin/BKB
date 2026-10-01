# Pendientes (al 01-10-2026)

Todo lo implementado (portal tareas 0 a 28, módulos 1 a 4 de `docs/11`, landing y `/arriendo`) está fusionado en `desarrollo` y `main`. Los planes y listas cumplidos se borraron; quedan en el historial de git. Aquí solo va lo que falta, en orden.

## 1. Decidir las 3 alertas de seguridad (bloquean la tarea 16)
Detalle en `docs/04` §6. **Preguntar al usuario antes de tocar código.**
- [ ] axes detrás del proxy de App Platform: hoy usa `REMOTE_ADDR` (la IP del proxy), así que 5 logins fallidos de cualquiera bloquean a todos. Alinear también `_get_client_ip` (límite de "¿Olvidaste tu contraseña?" y de `/cotizar/`).
- [ ] Con `DEBUG=False` y sin `EMAIL_HOST`, el arranque debería fallar: hoy cae al backend de consola y los enlaces de invitación quedarían en los logs.
- [ ] El chequeo de salud podría llegar por HTTP interno o con un `Host` fuera de `ALLOWED_HOSTS` y recibir 301 o 400 por `SECURE_SSL_REDIRECT`. Se verifica en la tarea 16.

## 2. Verificación manual en local
- [ ] Recorrido como personal y como cliente: crear empresa y proyecto con encargados (invitaciones en consola), avanzar hitos, aceptar y rechazar la Revisión, ver archivos al finalizar.
- [ ] Modificaciones: crear, adjuntar, enviar, responder desde el enlace y desde el panel; `manage.py enviar_recordatorios`.
- [ ] Revisar todas las plantillas con `manage.py vista_correos`.
- [ ] Formulario "Cotizar obra" de la landing contra el portal local (`PUBLIC_PORTAL_URL=http://localhost:8000`).
- [ ] `/arriendo`: claro, oscuro, 375 px y 1280 px, teclado, y el mensaje de WhatsApp con 1 y 3 equipos.

## 3. Tarea 16 · Puesta en marcha en DigitalOcean (requiere al usuario)
- [ ] PostgreSQL gestionado y la app en **NYC3** (región del Space).
- [ ] `doctl apps spec validate .do/app.yaml` (incluye el job diario `enviar_recordatorios`; si la cuenta no tiene jobs `SCHEDULED`, usar un cron externo).
- [ ] Variables en App Platform, prefijo `portal/` y una clave del Space **nueva para producción** (Limited, solo `bkb-space`).
- [ ] Dominio `portal.empresabkb.cl` con HTTPS y CORS del Space con ese origen.
- [ ] Primer superusuario desde la consola y jefe designado en `/admin/`.
- [ ] SMTP real con `instrumentacion@empresabkb.cl` (contraseña de aplicación). Si App Platform bloquea el 587, detenerse y decidir.
- [ ] Comprobar: `/health/` responde, sin redirecciones infinitas, cookies seguras, login, una subida y una descarga reales, y un correo real de invitación.

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
