# 12 · Spec: Carpetas dentro de carpetas, subir carpetas completas, mover y renombrar

> **Estado:** APROBADA v1.0 (14-10-2026). Las decisiones están en la sección "Decisiones".
> El portal **está en producción con datos reales**: el cambio de modelo va con una migración que conserva todo lo
> que existe hoy.

## Objetivo

Hoy cada proyecto tiene carpetas de **un solo nivel** (docs/03 §14). BKB necesita:

1. **Carpetas dentro de carpetas**, con la misma navegación de siempre: Empresa → Proyecto → Planos → Rev A → …
2. **Subir una carpeta completa** desde el computador, con el botón o arrastrándola, de modo que en el portal
   quede la misma estructura de subcarpetas.
3. **Mover y renombrar** carpetas y archivos dentro del proyecto.

No cambia:

- **El Space.** Las carpetas siguen siendo solo filas en la base de datos, y la clave de cada archivo sigue siendo
  `{prefijo}{proyecto}/{archivo}`. Mover o renombrar no copia nada.
- **Los permisos.** Solo el personal y el jefe crean, suben, mueven, renombran y eliminan. El cliente solo mira y
  descarga.
- **El bloqueo del cliente** mientras el proyecto está en curso (A8).
- **La cola de subida** (`subir.js`). `iniciar_subida` y `confirmar_subida` no cambian.

## Mapa de módulos

| Módulo | Qué hace | Depende de |
|---|---|---|
| `arbol` | Agrega `padre` al modelo, con su migración. Navegación anidada con migas de pan, crear subcarpetas y eliminar carpetas sin perder archivos. | — |
| `subir-carpeta` | Botón «Subir carpeta» y arrastrar carpetas: recrea las subcarpetas y sube los archivos con la cola actual. | arbol |
| `mover-renombrar` | Renombrar carpetas y archivos. Mover carpetas y archivos (uno o varios) a otra carpeta del mismo proyecto. | arbol |
| `ordenar-importadas` | Convierte las carpetas importadas con nombres como «Planos / TBC - 03» en carpetas anidadas de verdad. `importar_antiguos` pasa a crear el árbol directamente. | arbol |

**Orden de construcción:** arbol → subir-carpeta → mover-renombrar → ordenar-importadas. Todo va en una sola rama
y un solo PR hacia `main`.

**Queda fuera de este alcance:** descargar una carpeta como ZIP.

---

## Módulo `arbol`

### Reglas

- **C1.** Una carpeta está en la raíz del proyecto (`padre = null`) o dentro de otra carpeta **del mismo
  proyecto**.
- **C2.** Dentro de un mismo lugar (la raíz o una carpeta) no puede haber dos carpetas con el mismo nombre, sin
  importar mayúsculas y minúsculas. En lugares distintos sí se puede: `Planos/Rev A` y `Fotos/Rev A` pueden
  existir a la vez.
- **C3.** La profundidad máxima es de **8 niveles**. Si alguien intenta crear un noveno nivel, recibe un error
  claro. Una carpeta más profunda que eso se rechaza **antes** de subir cualquier archivo.
- **C4.** **Eliminar una carpeta nunca borra archivos.** Su contenido, archivos y subcarpetas, sube a la carpeta
  de arriba, o a la raíz si estaba en la raíz. Si al subir una subcarpeta choca con otra del mismo nombre, las dos
  se fusionan, con la misma regla hacia abajo.
- **C5.** Dentro de cada carpeta se ve lo mismo que hoy en la raíz: primero sus subcarpetas, después sus archivos,
  y los filtros Todos, Documentos y Fotos. «+ Nueva carpeta» crea la carpeta **dentro de la que se está mirando**.
- **C6.** Las migas de pan muestran el camino completo, por ejemplo `Tecfluid › NV 28174 › Planos › Rev A`, y cada
  tramo es un enlace. La flecha «←» vuelve a la carpeta de arriba.
- **C7.** La tarjeta de cada carpeta cuenta solo lo que tiene **directamente** adentro, por ejemplo «2 carpetas ·
  14 archivos». Igual que hoy, el conteo sale de `archivos_visibles`, así que respeta el bloqueo del cliente.
- **C8.** Las modificaciones y el aviso del hito en curso se siguen mostrando **solo en la raíz** del proyecto.

### Modelo

```python
class Carpeta(models.Model):
    ...
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='carpetas')   # se mantiene
    padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                              related_name='subcarpetas')                                      # nuevo

    class Meta:
        ordering = ['nombre']
        constraints = [
            # C2: único por lugar sin distinguir mayúsculas. La raíz necesita su propia regla porque NULL != NULL.
            models.UniqueConstraint(Lower('nombre'), 'padre', name='carpeta_unica_en_padre'),
            models.UniqueConstraint(Lower('nombre'), 'proyecto', condition=Q(padre__isnull=True),
                                    name='carpeta_unica_en_raiz'),
        ]
```

- **Cada carpeta conserva `proyecto`.** Así, contar, borrar y validar que una carpeta pertenece a un proyecto
  sigue siendo una sola consulta. El código exige que `padre.proyecto == proyecto`.
- **Sin librerías de árboles** (django-mptt o treebeard). Un proyecto tiene decenas de carpetas, no miles. La
  vista carga **todas las carpetas del proyecto en una sola consulta** y arma en Python el camino, los hijos y la
  profundidad.
- **`padre` tiene `on_delete=CASCADE`** como red de seguridad para cuando se borra el proyecto completo. Para
  eliminar una carpeta, `eliminar_carpeta` primero sube su contenido (C4) dentro de una transacción y después la
  borra, así que el CASCADE nunca alcanza nada.

### Migración

`0009_carpetas_anidadas` agrega `padre` en null y cambia `unique_together` por las dos restricciones nuevas. Todas
las carpetas existentes quedan en la raíz, así que **nada cambia de lugar**.

Hoy la unicidad sí distingue mayúsculas. Antes de crear la restricción nueva, la migración renombra cualquier par
que solo difiera en mayúsculas, como «Planos» y «planos»: la segunda pasa a llamarse «planos (2)».

### Rutas

| Ruta | Quién | Cambio |
|---|---|---|
| `GET /proyectos/<uuid>/?carpeta=<uuid>` | Todos | Igual que hoy, pero ahora muestra subcarpetas y migas. |
| `POST /proyectos/<uuid>/carpetas/nueva/` | Personal y jefe | Acepta `padre` (opcional). |
| `POST /carpetas/<uuid>/eliminar/` | Personal y jefe | Aplica C4. La confirmación dice cuántos archivos y subcarpetas suben de nivel. |

---

## Módulo `subir-carpeta`

### Reglas

- **S1.** Junto a «Subir archivos» aparece **«Subir carpeta»**: es `<input type="file" webkitdirectory>` y
  funciona en Chrome, Edge, Firefox y Safari de escritorio. En los navegadores que no lo soportan, como el iPhone,
  el botón **no se muestra**.
- **S2.** **Arrastrar** una o varias carpetas a la página funciona igual que el botón, y también se pueden mezclar
  con archivos sueltos. Lo que se suelta sobre una tarjeta de carpeta queda dentro de esa carpeta.
- **S3.** La carpeta elegida **se crea dentro de la carpeta que se está mirando**, con todas sus subcarpetas. Si
  ya existe una carpeta con el mismo nombre en ese lugar, se crea **«Planos (2)»**, o «(3)» y así, y todo queda
  adentro de la nueva (D6). Las subcarpetas de adentro son siempre nuevas, así que no chocan.
- **S4.** **Antes de subir nada**, aparece un resumen para confirmar, por ejemplo: «Subir "Planos": 3 carpetas,
  48 archivos (1,2 GB). 2 archivos no se subirán: tipo no permitido.». Más de **500 archivos** se rechazan con un
  mensaje que pide subirlos por partes.
- **S5.** Los archivos de sistema se ignoran sin avisar: `.DS_Store`, `Thumbs.db`, `desktop.ini` y los que
  empiezan con `~$`. Los que tienen un tipo no permitido o pasan del límite se cuentan en el resumen, no se suben y
  no frenan al resto.
- **S6.** Las carpetas vacías **también se crean**.
- **S7.** La subida usa la cola de siempre: 3 archivos a la vez, con barra de progreso y reintento. Cada fila
  muestra la ruta, por ejemplo `Planos/Rev A/plano-01.pdf`.

### Cómo funciona

1. El navegador arma la lista de rutas.
   - Con el botón, la saca de `file.webkitRelativePath`.
   - Al arrastrar, la saca de `webkitGetAsEntry()` y `readEntries()`, leyendo en tandas, porque Chrome entrega
     como máximo 100 entradas por llamada.
2. Envía **una sola llamada** a `POST /proyectos/<uuid>/carpetas/arbol/`, con
   `{padre: <uuid|null>, raiz: "Planos", rutas: ["Rev A", "Rev A/Detalles", …]}`.
3. El servidor procesa todo en una transacción:
   - valida C3 y cada nombre (que no esté vacío y tenga a lo más 100 caracteres);
   - crea la raíz con el primer nombre libre (S3) y debajo el árbol completo;
   - devuelve `{"": <uuid raíz>, "Rev A": <uuid>, …}`.

   Si algo falla, no se crea nada.
4. El navegador pone cada archivo en la cola con el `carpeta_id` de su ruta.

Si alguien cancela la subida o cierra la pestaña, pueden quedar carpetas vacías. Se eliminan con el botón de
siempre.

---

## Módulo `mover-renombrar`

### Reglas

- **R1.** **Renombrar una carpeta:** desde la carpeta abierta, con «Renombrar». Aplica C2: si el nombre ya existe
  en ese lugar, se muestra un error y no cambia nada.
- **R2.** **Renombrar un archivo:** desde la fila del archivo. Se edita solo el nombre antes del punto, porque **la
  extensión no cambia**: un `.pdf` no puede pasar a ser `.dwg`. Las descargas usan el nombre nuevo.
- **R3.** **Mover una carpeta:** el destino se elige de una lista con la raíz y todas las carpetas del proyecto,
  escritas con su camino (`Planos › Rev A`).
  - La lista **no ofrece** la misma carpeta, sus subcarpetas (eso formaría un ciclo) ni los destinos que dejarían
    el árbol con más de 8 niveles.
  - El servidor vuelve a validarlo todo.
  - Si en el destino ya hay una carpeta con el mismo nombre, se muestra un error que pide renombrarla primero.
- **R4.** **Mover archivos:** cada archivo tiene una casilla. Al marcar uno o más, aparece la barra
  «Mover a… [lista] [Mover]». Si en el destino hay archivos con el mismo nombre, quedan los dos, como hoy.
- **R5.** Solo el personal y el jefe pueden mover y renombrar (`puede_gestionar_estructura`). Los adjuntos de
  modificaciones no aparecen en la lista, así que no se pueden mover.
- **R6.** Las carpetas y archivos se mueven solo dentro del **mismo proyecto**.
- **R7.** Todo funciona sin JavaScript, con formularios normales y `<select>`. El JavaScript solo muestra la barra
  al marcar casillas.

### Rutas

| Ruta | Datos |
|---|---|
| `POST /carpetas/<uuid>/renombrar/` | `nombre` |
| `POST /carpetas/<uuid>/mover/` | `destino` (uuid, o vacío para la raíz) |
| `POST /archivos/<uuid>/renombrar/` | `nombre` (sin la extensión) |
| `POST /proyectos/<uuid>/archivos/mover/` | `archivos` (varios uuid) y `destino` |

---

## Módulo `ordenar-importadas`

`importar_antiguos` guardaba las rutas del Space antiguo como un solo nombre de carpeta, por ejemplo «Planos /
TBC - 03».

- **`importar_antiguos`** pasa a crear las carpetas anidadas (`Planos` › `TBC - 03`).
- **Comando nuevo `manage.py anidar_carpetas`:**
  - convierte en árbol cada carpeta cuyo nombre contiene « / »;
  - si las carpetas ya existen, las fusiona, por ejemplo «Planos» con «Planos / TBC - 03»;
  - sin `--ejecutar` solo muestra lo que haría;
  - a los archivos solo les cambia el `carpeta_id`.

---

## Decisiones

| # | Pregunta | Elegido |
|---|---|---|
| D1 | ¿Qué pasa al eliminar una carpeta con contenido? | Su contenido sube un nivel; nunca se borran archivos (C4). |
| D2 | ¿Profundidad máxima? | 8 niveles. |
| D3 | ¿Ordenar las carpetas importadas con « / »? | Sí, con el comando `anidar_carpetas`. |
| D4 | ¿Mover y renombrar entran ahora? | Sí, con el módulo `mover-renombrar`. |
| D5 | ¿Qué cuenta la tarjeta de una carpeta? | Solo lo que tiene directamente adentro. |
| D6 | ¿Qué pasa al subir una carpeta que ya existe en ese lugar? | Se crea «Planos (2)». Para agregar archivos a una carpeta existente, se entra a ella y se usa «Subir archivos». |

## Pruebas

Las pruebas nuevas van en `test_carpetas_arbol.py` y las que se ajustan, en `test_carpetas.py`.

- **Árbol:**
  - crear una subcarpeta;
  - un nombre puede repetirse en lugares distintos, pero no en el mismo, sin importar mayúsculas (C2);
  - pasar la profundidad máxima da error (C3);
  - un `padre` de otro proyecto da 400 (C1);
  - las migas de pan muestran el camino (C6);
  - los conteos respetan el bloqueo del cliente (C7).
- **Eliminar (C4):**
  - el contenido sube un nivel;
  - las subcarpetas con el mismo nombre se fusionan;
  - no se borra ni un archivo ni una descarga.
- **Subida de carpeta:**
  - se crea toda la estructura;
  - si la carpeta ya existe, se crea «Planos (2)» (D6);
  - con una ruta inválida no se crea nada;
  - para un cliente da 403.
- **Mover y renombrar:**
  - un nombre repetido da error (R1);
  - la extensión se conserva (R2);
  - mover una carpeta a sí misma o a una subcarpeta se rechaza (R3);
  - se respeta la profundidad (R3);
  - un destino de otro proyecto da 404 (R6);
  - para un cliente da 403 (R5);
  - se pueden mover varios archivos a la vez;
  - `clave_space` no cambia.
- **`anidar_carpetas`:**
  - sin `--ejecutar` no cambia nada;
  - con `--ejecutar` arma el árbol y fusiona;
  - las claves de los archivos no cambian.
- **CSP:** la vista de una subcarpeta cumple el contrato.
- **JS:** se prueba a mano en el servidor local:
  - el botón y el arrastre;
  - más de 100 archivos;
  - carpetas vacías;
  - archivos no permitidos.

## Despliegue

1. Respaldar `portal.sqlite3`.
2. Ejecutar `deploy.sh`, que aplica la migración 0009.
3. Correr `anidar_carpetas` sin `--ejecutar` y revisar el resultado con el usuario.
4. Correr `anidar_carpetas --ejecutar`.

Al terminar se actualiza docs/03: §14, la línea «Fuera de alcance» de la §1 y la tabla de rutas.
