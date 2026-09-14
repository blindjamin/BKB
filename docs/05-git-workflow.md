# 05 · Flujo de Trabajo Git & Despliegue

> **REGLA ESTRICTA PARA TODA IA Y DESARROLLADOR:**  
> **NUNCA hacer push directo a la rama `main` ni a `origin/main`.**  
> Todo el desarrollo activo converge en la rama `desarrollo`.

---

## 1. Jerarquía de Ramas (Estructura de 3 Niveles)

El repositorio sigue un modelo de tres niveles estricto:

1. **Nivel 1 · `main` (Rama Primaria / Producción):**
   - Es la rama principal del repositorio.
   - Contiene únicamente versiones estables y listas para producción.
   - **Nadie hace commits ni push directo a `main`**. Solo recibe merges controlados provenientes de `desarrollo`.

2. **Nivel 2 · `desarrollo` (Rama Secundaria / Integración Activa):**
   - Es la rama base donde se reúne el trabajo activo del proyecto.
   - Recibe los Pull Requests de las ramas de tarea una vez revisadas por el usuario/equipo.
   - Es la rama que dispara el despliegue de previsualización en GitHub Pages.

3. **Nivel 3 · `[nombre]/[fecha]-[descripcion]` (Ramas Terciarias / Tareas Específicas):**
   - Ramas efímeras creadas a partir de `desarrollo` para cada funcionalidad, ajuste o avance.
   - Todo push se hace **únicamente** hacia la rama de tarea creada.
   - El desarrollador o la IA genera el Pull Request hacia `desarrollo` para que el usuario lo revise y fusione manualmente.

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

