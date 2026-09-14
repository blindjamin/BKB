# 05 · Flujo de Trabajo Git & Despliegue

> **REGLA ESTRICTA PARA TODA IA Y DESARROLLADOR:**  
> **NUNCA hacer push directo a la rama `main` ni a `origin/main`.**  
> Todo el desarrollo activo converge en la rama `desarrollo`.

---

## 1. Ramas Principales del Repositorio

- **`main`:** Rama de producción protegida. Solo recibe merges validados y probados provenientes de `desarrollo`.
- **`desarrollo`:** Rama base de integración continua. Toda nueva característica o corrección se fusiona hacia acá.

---

## 2. Nomenclatura Obligatoria de Ramas de Tarea

Cada vez que se vaya a realizar una modificación o avance, se debe crear una rama con el siguiente formato:

```
[nombre]/[fecha]-[descripcion]
```

### Ejemplos Válidos:
- `benjamin/2026-09-14-esqueleto-inicial-bkb`
- `benjamin/2026-09-21-formulario-contacto-turnstile`
- `benjamin/2026-10-05-autenticacion-clientes-django`

---

## 3. Protocolo Paso a Paso para Hacer Push de Avances

1. **Asegurarse de estar al día con `desarrollo`:**
   ```bash
   git checkout desarrollo
   git pull origin desarrollo
   ```

2. **Crear y cambiarse a la nueva rama de tarea:**
   ```bash
   git checkout -b benjamin/YYYY-MM-DD-descripcion-corta
   ```

3. **Verificar que la compilación y pruebas pasen en verde:**
   ```bash
   npm run build:web
   ```

4. **Hacer commit de los cambios:**
   ```bash
   git add .
   git commit -m "feat(modulo): descripcion concisa del cambio"
   ```

5. **Subir (push) exclusivamente a la rama de tarea creada:**
   ```bash
   git push -u origin benjamin/YYYY-MM-DD-descripcion-corta
   ```

6. **Merge hacia `desarrollo`:**
   Se realiza mediante Pull Request en GitHub o merge local hacia `desarrollo`:
   ```bash
   git checkout desarrollo
   git merge benjamin/YYYY-MM-DD-descripcion-corta
   git push origin desarrollo
   ```

---

## 4. Despliegue Continuo a GitHub Pages

El repositorio cuenta con la acción `.github/workflows/deploy-pages.yml` activa:
- Cada push o merge a la rama `desarrollo` compila automáticamente el sitio Astro con `GITHUB_PAGES=true` y lo publica en:
  **`https://blindjamin.github.io/BKB/`**
- Permite disponer de un enlace público funcional en cualquier momento sin costo de infraestructura mientras no se configure DigitalOcean.

