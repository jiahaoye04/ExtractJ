# ExtractJ

![Versión](https://img.shields.io/badge/versi%C3%B3n-2.1.0-2f7fd1)
![Python](https://img.shields.io/badge/python-3.8%2B-3776ab)
![Plataforma](https://img.shields.io/badge/plataforma-Windows%2010%20%7C%2011-555555)
![Dependencias](https://img.shields.io/badge/dependencias-ninguna-2e8b57)

**Reúne en una sola carpeta los ficheros que necesitas de cualquier proyecto,
y mantenlos al día.**

ExtractJ (en la ventana, *Extraer Ficheros*) recorre una o varias carpetas con
todas sus subcarpetas y copia en un único sitio los ficheros que te
interesan. Puedes elegir los tipos de cada carpeta, filtrar por nombre y por
tamaño, o sacar solo una muestra al azar. Y si guardas copias de ficheros para
consultarlos, ExtractJ las pone al día cuando cambian los originales.

- Junta de golpe todos los `.java` de un proyecto.
- Saca los `.jsp` y `.css` que contengan `cocina` de tres carpetas distintas.
- Coge veinte ficheros al azar de un directorio enorme para echarles un
  vistazo.
- Pon al día tu carpeta de clases de referencia después de un merge.

> ### 🆕 Novedades de la 2.1 · «Siempre al día»
>
> **Actualizar carpeta**: ExtractJ encuentra el original de cada fichero de
> tu carpeta (los `.java` por su `package`) y sustituye los que han cambiado,
> con vista previa y copia de las versiones anteriores.
>
> [Leer las notas de la versión →](docs/notas-de-version/2.1.0.md)

---

## Índice

- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Primeros pasos](#primeros-pasos)
- [La ventana](#la-ventana)
- [Extensiones](#extensiones)
- [Filtros](#filtros)
- [Favoritos](#favoritos)
- [Recientes y copias guardadas](#recientes-y-copias-guardadas)
- [Actualizar carpeta](#actualizar-carpeta)
- [Historial](#historial)
- [Tema claro y oscuro](#tema-claro-y-oscuro)
- [Preguntas frecuentes](#preguntas-frecuentes)
- [Tus datos](#tus-datos)
- [Versiones](#versiones)

---

## Requisitos

- **Windows 10 u 11.**
- **Python 3.8 o superior**, con `tkinter`, que viene incluido en el
  instalador oficial de [python.org](https://www.python.org/downloads/).

Nada más: ExtractJ solo usa la biblioteca estándar de Python.

---

## Instalación

1. Descarga el repositorio: botón **Code → Download ZIP**, o
   `git clone https://github.com/jiahaoye04/ExtractJ.git`.
2. Deja juntos en la misma carpeta:
   - `ExtraerFicheros.py`
   - `ExtraerFicheros.bat`
3. Haz doble clic en `ExtraerFicheros.bat`.

La primera vez se crea `config.json` junto al programa, con tus preferencias.

**Si al abrirlo no pasa nada**, edita el `.bat` con el Bloc de notas y pon en
la línea `set "PYTHONW=..."` la ruta completa a tu `pythonw.exe`.

### Actualizar a una versión nueva

Sustituye `ExtraerFicheros.py` por el nuevo. Tu `config.json` se conserva, y
si viene de una versión antigua se convierte solo al arrancar. En la cabecera
verás el número de la versión instalada.

---

## Primeros pasos

Tu primera extracción, en cuatro pasos:

1. En **Carpetas de origen**, elige una carpeta con el botón `...`.
2. En el campo de al lado, escribe las extensiones: `.java`. Vacío extrae
   todos los tipos.
3. Revisa el **Destino**. Debajo verás la carpeta que se va a crear, por
   ejemplo `CopiaJAVA`.
4. Pulsa **Extraer ficheros**.

Al terminar se abre la carpeta con todo lo copiado (opción *Abrir la carpeta al
terminar*, activada de fábrica).

---

## La ventana

- **Cabecera:** versión instalada, tema, **Actualizar carpeta…** e
  **Historial**. Debajo, la extensión global y el filtro global de nombre.
- **Columna izquierda:** las carpetas de origen y, debajo, *Recientes*.
- **Columna derecha:** los favoritos.
- **Abajo:** el destino, el progreso y el botón **Extraer ficheros**, que
  siempre queda a la vista.

La ventana crece sola hasta ocupar como mucho el 80 % del alto de la
pantalla. A partir de ahí, cada sección tiene su propia barra de
desplazamiento, y la rueda del ratón mueve la que tengas debajo.

### Carpetas de origen

- Cada línea es una carpeta con sus extensiones.
- **+ Añadir carpeta** añade una línea; la `×` quita una y **Limpiar** las
  vacía todas.
- Las rutas largas se ven por el final, que es donde está el nombre de la
  carpeta.

### Carpeta de destino

| Lo que extraes                                   | Carpeta que se crea |
|--------------------------------------------------|---------------------|
| Una sola extensión en todas las líneas           | `CopiaJAVA`         |
| Varias extensiones                               | `CopiaMIXTO`        |
| Todas las líneas sin extensión (todos los tipos) | `CopiaTODO`         |
| Mezcla de líneas con y sin extensión             | `CopiaMIXTO`        |

Con **Abrir la carpeta al terminar** marcada, se abre en el explorador en
cuanto cierras el aviso de resumen.

---

## Extensiones

- Se escriben separadas por espacios: `.java .jsp .css`.
- **Una línea vacía extrae todos los tipos**, incluidos los ficheros sin
  extensión (`Makefile`, `LICENSE`).
- **Extensión global:** lo que escribas arriba se escribe en todas las líneas
  al modificarlo. Al cambiarla, cada línea pierde la extensión global anterior,
  recibe la nueva y conserva lo suyo. Con la global en `.java` y una línea en
  `.jsp .java`, cambiar la global a `.css` deja esa línea en `.jsp .css`.
- La global **solo se aplica cuando la modificas**. Al cargar un favorito,
  añadir una línea o abrir el programa, no se aplica. Para repartirla otra vez,
  escribe una letra y bórrala.
- Cambiar una línea a mano nunca cambia la global.
- Si escribes una extensión desconocida, la extracción no empieza y se te
  indica en qué línea está el fallo.

---

## Filtros

### Filtro global de nombre

Arriba, para todas las líneas a la vez:

- **Inclusión** con su modo: *Contiene*, *Empieza por* o *Termina por*.
- **Excluir:** descarta lo que contenga esa palabra.

Se compara con el **nombre sin la extensión** y sin distinguir mayúsculas:
`holacocina.java` sí pasa *Termina por* `cocina`.

### Filtros de cada carpeta

El botón **Filtros…** de cada línea permite:

- **Tamaño mínimo y máximo**, en KB, con decimales (`1,5`).
- **El nombre contiene**, solo para esa carpeta.
- **Muestra aleatoria:** un número fijo de ficheros o un porcentaje, elegidos
  al azar entre los que pasan los demás filtros.

El resumen aparece en azul bajo la ruta, por ejemplo
`Filtros: <= 40 KB · 15 al azar`.

Si pones **la misma carpeta en dos líneas con filtros distintos**, se hacen
dos pasadas y no se repiten ficheros. Así puedes sacar, por ejemplo, 10 al
azar y además todos los de menos de 3 KB.

---

## Favoritos

Un favorito es un **grupo entero**: un nombre y todas sus carpetas, con sus
extensiones y filtros. Al pulsarlo se cargan de golpe.

- **☆ Guardar favorito** guarda las líneas actuales. Se convierte en
  **★ En favoritos** cuando lo que ves coincide exactamente con uno guardado;
  pulsándolo entonces, lo quitas.
- La estrella solo brilla si coinciden **carpetas, extensiones y filtros**.
- **Guardar las mismas carpetas otra vez sobrescribe** ese favorito, y se te
  ofrece el nombre anterior. Con una carpeta de más o de menos, es un
  favorito nuevo.
- **Buscar** filtra los favoritos por nombre.
- **Sustituir al cargar:** apagado, pulsar un favorito **añade** sus carpetas
  a las que ya tienes, para combinar varios. Encendido, sustituye lo que haya.
- Si dejas el ratón quieto sobre un favorito, ves todas sus carpetas.

---

## Recientes y copias guardadas

*Recientes* muestra tus últimas operaciones:

- **Extracciones**, con estrella para guardarlas como favorito. Pulsarlas
  carga sus carpetas.
- **↻ Actualizaciones**, que vuelven a abrir *Actualizar carpeta* con esa
  carpeta.

Hay una fila por conjunto de carpetas: repetir una operación sube su fila
arriba, sin duplicarla.

### Copias guardadas

ExtractJ puede **conservar una copia de los ficheros** de tus últimas
operaciones:

| Ajuste                          | Qué hace                                                                                       |
|---------------------------------|------------------------------------------------------------------------------------------------|
| **Recordar** (1–10)             | Cuántas filas tiene *Recientes*                                                                |
| **Guardar ficheros de** (0–10)  | De cuántas se guarda copia. Nunca más que *Recordar*; a 0 no se guarda nada                    |
| **Copias en… / Cambiar…**       | Dónde se guardan. Por defecto, `Extracciones guardadas` junto al programa                      |

- En una **extracción** se guardan los ficheros copiados. Botón
  **Ver ficheros (N)**.
- En una **actualización** se guardan las versiones que se sustituyeron.
  Botón **Versiones viejas (N)**.

Las copias que sobran **se borran solas**. Por seguridad, ExtractJ solo borra
carpetas que llevan dentro su fichero `_contenido_extractj.json`: nunca toca
una carpeta que no haya creado él.

---

## Actualizar carpeta

*Nuevo en la 2.1.* Para cuando guardas copias de ficheros del proyecto y se
quedan desfasadas.

1. Pulsa **Actualizar carpeta…** en la cabecera.
2. En **Rutas de búsqueda**, añade dónde están los originales. Para un
   proyecto Java, la carpeta `src`; para JSP, CSS o JS, también la carpeta
   web.
3. En **Carpeta a actualizar**, elige tu carpeta con *Examinar…*. Por defecto
   propone `ConstanteJAVA` dentro del destino.
4. Pulsa **Analizar**, revisa la vista previa y pulsa
   **Actualizar marcados**.

### Cómo encuentra los originales

1. **Registro de la carpeta:** si ya se actualizó antes, va directo.
2. **`.java`, por su `package`:** `package com.ejemplo.app;` en `Clase.java`
   → `src\com\ejemplo\app\Clase.java`. Es exacto aunque haya clases con el
   mismo nombre en otros paquetes.
3. **Por nombre**, para todo lo demás y para los Java que se hayan cambiado
   de paquete. Se saltan `build`, `bin`, `target`, `.git` y similares.

### Vista previa

| Estado                | Qué significa                         | Qué puedes hacer                     |
|-----------------------|---------------------------------------|--------------------------------------|
| **Cambiado**          | El original es distinto de tu copia   | Viene marcado; clic en la casilla para desmarcarlo |
| **Igual**             | Ya está al día                        | Nada                                 |
| **Varios candidatos** | Hay varios ficheros con ese nombre    | Doble clic y eliges el original      |
| **No encontrado**     | No está en las rutas de búsqueda      | Doble clic y lo indicas a mano       |

Se compara **el contenido**, no la fecha. Nada se modifica hasta que pulsas
*Actualizar marcados*, y los ficheros no encontrados no se tocan nunca.

Al actualizar, la carpeta guarda en `_origenes_extractj.json` el original de
cada fichero, también los que elegiste a mano: la siguiente vez se resuelve
todo al instante.

Solo se revisan los ficheros que están directamente en la carpeta, no los de
sus subcarpetas.

---

## Historial

El botón **Historial** lista todas tus extracciones y actualizaciones:
fecha, hora, tipo, número de ficheros, origen y destino. Se guardan las 200
últimas.

---

## Tema claro y oscuro

El selector **Tema** de la cabecera tiene tres opciones:

- **Sistema** (de fábrica): sigue a Windows, también si lo cambias con el
  programa abierto.
- **Claro** y **Oscuro**: fuerzan uno.

El cambio es inmediato en todas las ventanas, incluida la barra de título en
Windows 10 y 11. Los avisos y el selector de carpetas son del sistema y siguen
el tema de Windows.

---

## Preguntas frecuentes

**¿ExtractJ modifica mis ficheros originales?**
No. Extraer es copiar, nunca mover. *Actualizar carpeta* solo escribe en la
carpeta que tú eliges, nunca en las rutas de búsqueda.

**¿Qué pasa con la carpeta `CopiaJAVA` si ya existía?**
Se vacía antes de cada extracción, y antes se te pide confirmación. No guardes
nada tuyo dentro de una carpeta `Copia...`.

**¿Y si dos ficheros se llaman igual?**
La copia es plana, sin subcarpetas: el segundo se guarda como
`Nombre_1.java`, el tercero como `Nombre_2.java`, etc.

**Mi extensión no es válida.**
ExtractJ acepta una lista amplia de tipos conocidos (código, documentos,
imágenes, audio, vídeo, comprimidos…). Si echas en falta alguno, abre una
*issue*.

**No encuentra ningún fichero.**
Revisa los filtros: el aviso te sugiere si alguno puede ser demasiado
estricto.

**Actualizar carpeta dice que no hay rutas de búsqueda.**
Añade al menos una con *+ Añadir ruta*. Para Java, la carpeta `src` del
proyecto.

**¿Funciona fuera de Windows?**
Está pensado para Windows. Al ser Python con `tkinter` puede arrancar en otros
sistemas, pero no se prueba en ellos, y el tema del sistema y la barra de
título oscura solo funcionan en Windows.

---

## Tus datos

Todo se queda en tu equipo. ExtractJ no se conecta a internet.

| Fichero                       | Dónde                         | Qué guarda                                                                                         |
|-------------------------------|-------------------------------|----------------------------------------------------------------------------------------------------|
| `config.json`                 | Junto al programa             | Preferencias, favoritos, recientes, historial y rutas de búsqueda                                  |
| `Extracciones guardadas/`     | Junto al programa, o donde elijas | Copias de tus últimas operaciones                                                             |
| `_contenido_extractj.json`    | Dentro de cada copia guardada | Lista de ficheros y su origen; autoriza el borrado automático                                      |
| `_origenes_extractj.json`     | En cada carpeta actualizada   | El original de cada fichero                                                                        |

Si borras `config.json`, ExtractJ vuelve a su estado de fábrica; las copias
guardadas siguen en su carpeta hasta que las borres tú. Ninguno de estos
ficheros se sube al repositorio: están en el `.gitignore`.

---

## Versiones

| Versión | Fecha       | Lo principal                                                      |
|---------|-------------|-------------------------------------------------------------------|
| **2.1.0** | 2026-11-18 | Actualizar carpeta · [notas](docs/notas-de-version/2.1.0.md)     |
| 2.0.1   | 2026-11-05  | Correcciones del repositorio y del README                         |
| 2.0.0   | 2026-10-29  | Filtros por carpeta, copias guardadas, modo oscuro, dos columnas  |
| 1.3.0   | 2026-09-18  | Varias carpetas a la vez, filtro de nombre, favoritos de grupo    |
| 1.2.0   | 2026-09-02  | Ventana ajustable, favoritos ilimitados, abrir al terminar        |
| 1.1.0   | 2026-07-21  | Favoritos con nombre y extensión                                  |
| 1.0.0   | 2026-07-20  | Primera versión en Python                                         |

- [Registro de cambios completo](CHANGELOG.md)
- [Notas de versión](docs/notas-de-version/)
- [Notas técnicas de desarrollo](docs/NOTAS_TECNICAS.md)
