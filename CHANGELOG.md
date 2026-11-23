# Registro de cambios

Todos los cambios relevantes de ExtractJ, de la versión más nueva a la más
antigua.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
las versiones siguen [Versionado Semántico](https://semver.org/lang/es/):

- **Mayor** (`2.0.0`): cambios que alteran cómo funciona algo que ya existía.
- **Menor** (`2.1.0`): funciones nuevas; lo anterior sigue igual.
- **Parche** (`2.0.1`): correcciones.

Las notas completas de cada versión, con el detalle de cada novedad, están en
[`docs/notas-de-version/`](docs/notas-de-version/).
Las decisiones técnicas, en [`docs/NOTAS_TECNICAS.md`](docs/NOTAS_TECNICAS.md).

---

## [2.1.1] — 2026-11-23

[Notas de la versión completas →](docs/notas-de-version/2.1.1.md)

### Corregido

- Un favorito o reciente con **la misma carpeta en varias líneas** (por
  ejemplo, con filtros distintos) se cargaba con líneas de menos: las
  repetidas se pisaban entre sí y solo quedaba la última. Ahora se cargan
  todas, y la estrella de *Guardar favorito* se enciende como debe.

---

## [2.1.0] — 2026-11-18 · «Siempre al día»

[Notas de la versión completas →](docs/notas-de-version/2.1.0.md)

### Añadido

- **Actualizar carpeta.** Nueva ventana para poner al día una carpeta de
  ficheros copiados del proyecto. ExtractJ localiza el original de cada uno y
  sustituye los que hayan cambiado:
  - Los `.java` se localizan por su `package`, exactos aunque haya clases con
    el mismo nombre en paquetes distintos.
  - El resto de ficheros, por nombre dentro de las rutas de búsqueda.
  - Vista previa antes de tocar nada: *Cambiado*, *Igual*,
    *Varios candidatos* o *No encontrado*, con casilla por fichero.
  - Elección manual del original cuando hay varios o ninguno.
  - Las versiones anteriores se guardan en las copias de ExtractJ.
  - La carpeta recuerda el original de cada fichero: a partir de la segunda
    vez no hace falta buscar nada.
- **Filas de actualización en *Recientes***, con el botón
  *Versiones viejas (N)* para ver lo que se sustituyó.
- **Rutas de búsqueda** y **carpeta a actualizar** configurables, recordadas
  entre sesiones.
- **Número de versión** visible en la cabecera.

### Cambiado

- En el **modo oscuro**, los botones *Extraer ficheros* y
  *Actualizar marcados* usan un azul más apagado, acorde con el fondo. En
  claro no cambian.
- El contador *Guardar ficheros de* lo comparten ahora extracciones y
  actualizaciones.
- Los ejemplos de la interfaz usan rutas genéricas.

---

## [2.0.1] — 2026-11-05

### Corregido

- El README indicaba mal dónde poner la ruta de `pythonw.exe` en el lanzador
  `.bat`.

### Añadido

- `.gitignore` para que la configuración personal no se suba al repositorio.

---

## [2.0.0] — 2026-10-29

### Añadido

- **Filtros por carpeta:** tamaño mínimo y máximo, texto en el nombre y
  **muestra aleatoria** (número fijo o porcentaje).
- **Copias de las últimas extracciones**, con contador propio, carpeta
  configurable, ventana *Ver ficheros* y borrado automático seguro.
- **Modo oscuro:** *Sistema*, *Claro* u *Oscuro*, con cambio al momento y
  barra de título oscura en Windows 10 y 11.
- **Interfaz a dos columnas** con tarjetas, y ayuda emergente con todas las
  carpetas de un favorito o reciente.

### Cambiado

- ⚠️ `config.json` pasa a **formato 3**. Se convierte solo al arrancar, pero
  una versión 1.x ya no puede leerlo.
- ⚠️ La **extensión global** se escribe en las líneas al modificarla, en vez
  de sumarse por detrás sin verse.
- ⚠️ Una línea **sin extensiones extrae todos los tipos** (antes era un
  error). Nueva carpeta destino `CopiaTODO`.
- ⚠️ *Recientes* guarda una fila por conjunto de carpetas.

### Corregido

- La rueda del ratón no respondía encima de las filas de los paneles.
- Botones pequeños demasiado anchos con el tema `clam`.

---

## [1.3.0] — 2026-09-18

### Añadido

- **Varias carpetas de origen** en una misma extracción, cada una con sus
  extensiones.
- **Filtro por nombre**: contiene, empieza por o termina por, más exclusión.
- **Favoritos de grupo**: un favorito guarda todas las carpetas a la vez, con
  buscador por nombre.
- Contador para elegir cuántos recientes mostrar.

### Cambiado

- Destino `CopiaMIXTO` cuando hay varias extensiones.

---

## [1.2.0] — 2026-09-02

### Añadido

- Opción **Abrir la carpeta al terminar**.

### Cambiado

- La ventana **se ajusta sola** al contenido, hasta el 80 % de la pantalla,
  con barra de desplazamiento a partir de ahí.
- **Favoritos sin límite** (antes, tres como máximo).

### Corregido

- Con muchos favoritos, el botón *Extraer* quedaba fuera de la ventana.

---

## [1.1.0] — 2026-07-21

### Añadido

- Los favoritos tienen **nombre** propio y se pueden renombrar.
- Favoritos y recientes recuerdan la **extensión** además de la carpeta.

---

## [1.0.0] — 2026-07-20

Primera versión: reescritura completa en Python del antiguo script `.bat`.

### Añadido

- Interfaz gráfica, sin dependencias externas.
- Extensión libre, validada contra una lista de tipos conocidos.
- Destino configurable y recordado.
- Favoritos y recientes.
- Historial de extracciones.
- Barra de progreso, con la copia en segundo plano.
- Nombres repetidos resueltos como `Nombre_1`, `Nombre_2`…

[2.1.1]: https://github.com/jiahaoye04/ExtractJ/releases/tag/v2.1.1
[2.1.0]: https://github.com/jiahaoye04/ExtractJ/releases/tag/v2.1.0
[2.0.1]: https://github.com/jiahaoye04/ExtractJ/commit/a8f8e76
[2.0.0]: https://github.com/jiahaoye04/ExtractJ/commit/6cacbd6
[1.3.0]: https://github.com/jiahaoye04/ExtractJ/commit/7b23a47
[1.2.0]: https://github.com/jiahaoye04/ExtractJ/commit/065ccec
[1.1.0]: https://github.com/jiahaoye04/ExtractJ/blob/main/docs/NOTAS_TECNICAS.md
[1.0.0]: https://github.com/jiahaoye04/ExtractJ/blob/main/docs/NOTAS_TECNICAS.md
