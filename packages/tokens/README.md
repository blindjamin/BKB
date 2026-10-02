# @bkb/tokens · Sistema de Diseño BKB

Paquete de tokens de diseño oficial para BKB (Sitio público y Portal de clientes).

## Principios
- **Naranjo BKB (`salmon-500` #FA5A36):** El color primario de marca (los tokens conservan el nombre `salmon`).
- **Temas:** oscuro (por defecto) y claro grafito y naranjo, con `data-theme="dark|light"`.
- **Superficies nocturnas:** Tokens fijos para componentes que siempre son oscuros (footer, hero).
- **Tipografía:** `Space Grotesk` para display y números, `IBM Plex Sans` para lectura en faena, y `IBM Plex Mono` para códigos SEC, RUT y mediciones.

## Uso
Importar en cualquier aplicación web o componente:
```css
@import "@bkb/tokens";
```
O directamente en el archivo CSS global del proyecto.
