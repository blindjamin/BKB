# 04 · Seguridad y Cumplimiento Normativo

> **Nota para IAs y auditores de seguridad:**  
> La seguridad de esta plataforma sigue el estándar OWASP ASVS 5.0 Nivel 2 y las normativas chilenas vigentes (Ley 21.719 de Protección de Datos y Ley 21.663 Marco de Ciberseguridad).

---

## 1. Protección de Datos Personales (Ley 21.719)
- **Formularios de CV y Trabaja con Nosotros:** Los CVs contienen datos sensibles. El formulario requiere un checkbox obligatorio de consentimiento explícito.
- **Plazo de Retención:** Los antecedentes curriculares se retienen por un máximo de **12 meses**, automatizando su borrado periódico.
- **Canal ARCO:** Se dispone de la casilla formal `privacidad@bkb.cl` para atender solicitudes de acceso, rectificación, cancelación u oposición dentro de los plazos legales.

---

## 2. Seguridad en la Aplicación Web (ASVS Nivel 2)
1. **Hashing de Contraseñas:** Argon2id prioritario con parámetros de memoria y tiempo robustos, más verificación contra contraseñas vulneradas.
2. **Control de Sesiones:**
   - Cookies `__Host-`, `HttpOnly`, `Secure` y `SameSite=Lax/Strict`.
   - Timeout por inactividad: 30 minutos.
   - Duración absoluta máxima de sesión: 12 horas (no hay "recordar sesión" infinito).
3. **Cabeceras de Seguridad (HTTP Headers):**
   - `Content-Security-Policy`: Sin `unsafe-inline` innecesario.
   - `Strict-Transport-Security`: `max-age=31536000; includeSubDomains; preload`.
   - `X-Frame-Options: DENY` para prevenir clickjacking.
   - `X-Content-Type-Options: nosniff`.
4. **Protección Anti-Automatización (Bots):**
   - Campos honeypot trampa en formularios de contacto.
   - Integración prevista con Cloudflare Turnstile sin cookies de rastreo comercial.
   - Límite de intentos con `django-axes` para mitigar ataques de fuerza bruta.

---

## 3. Seguridad en la Infraestructura
- **Aislamiento por Subdominios:** El sitio estático (`www.bkb.cl`) y el portal transaccional (`portal.bkb.cl`) no comparten cookies ni estado.
- **Base de Datos Privada:** PostgreSQL no cuenta con IP pública; solo acepta conexiones autorizadas provenientes de los servidores de la aplicación en la VPC de DigitalOcean.
- **Secretos:** Gestionados como variables de entorno cifradas en DigitalOcean App Platform, nunca comprometidas en el repositorio Git.
