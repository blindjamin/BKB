# 01 · Sistema de Diseño y Tokens BKB

> **Nota para IAs y diseñadores:**  
> La única fuente de verdad cromática y tipográfica es el paquete `packages/tokens`. No inventar nuevos colores hexadecimales arbitrarios en componentes o vistas.

---

## 1. Filosofía Visual: Ingeniería & Cobre
La identidad de BKB huye de estéticas genéricas ("AI slop") o gradientes artificiales. Se inspira en materiales tangibles de faena: cobre electrolítico de barrajes, carbón industrial y papel milimetrado técnico.

### Principios
1. **Legibilidad en Faena:** Texto base de 19 px (`1.1875rem`) para fácil lectura bajo luz solar o en tablets de terreno.
2. **Botón Primario Único:** El color cobre (`copper-700` `#B4470F`) se reserva estrictamente para la acción principal por pantalla.
3. **Fondo de Papel Cálido:** El lienzo utiliza `#FBF8F5` (`paper-50`) con trama técnica sutil, evitando el blanco puro cegador y los grises sintéticos fríos.
4. **Foco Visible de Alto Contraste:** 3 px de grosor en color `#1A1513` con offset de 3 px para cumplimiento estricto WCAG 2.2 AA.

---

## 2. Paleta de Colores Oficial

### Naranja Cobre (Acción de Marca)
| Token | Hex | Rol |
|---|---|---|
| `--bkb-copper-50` | `#FFF5EE` | Fondo de avisos suaves |
| `--bkb-copper-100` | `#FFE5D6` | Chips activos / Anillos de selección |
| `--bkb-copper-400` | `#F27A38` | Acentos gráficos |
| `--bkb-copper-700` | `#B4470F` | **Primario Oficial BKB** |
| `--bkb-copper-800` | `#8F3407` | Hover y estado activo de botón primario |

### Neutros Industriales
| Token | Hex | Rol |
|---|---|---|
| `--bkb-paper-50` | `#FBF8F5` | Fondo principal (Lienzo) |
| `--bkb-paper-100` | `#FAF6F2` | Cabeceras de tabla / Contenedores |
| `--bkb-paper-200` | `#F0EAE3` | Botón secundario / Cancelar |
| `--bkb-sand-200` | `#E6DDD5` | Bordes estándar (1.5 px) |
| `--bkb-sand-600` | `#7D6F64` | Texto secundario y placeholders |
| `--bkb-ink-900` | `#1A1513` | Tinta principal / Carbón industrial |

### Semáforo Normativo SEC
| Estado | Color Texto / Ícono | Fondo |
|---|---|---|
| **Vigente / OK** | `#1E6B47` | `#E6F4EC` |
| **Por Vencer (&lt; 30 días)** | `#B85D0A` | `#FEF3E6` |
| **Vencido / Crítico** | `#A8271B` | `#FDEEED` |
| **Trámite SEC** | `#1B5887` | `#EBF3F9` |
| **Reservado BKB** | `#7F7269` | `#F0EAE3` |

---

## 3. Tipografías
1. **Display & Títulos:** `Space Grotesk` (pesos 600, 700, 800).
2. **Cuerpo & Formularios:** `IBM Plex Sans` (pesos 400, 500, 600).
3. **Códigos & Mediciones:** `IBM Plex Mono` (pesos 500, 600) para RUT, certificados TE1, kVAr, kVA y amperajes.
