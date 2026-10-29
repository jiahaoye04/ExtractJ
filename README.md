# Extraer Ficheros

Recorre una o varias carpetas con todas sus subcarpetas y copia en un único
sitio los ficheros que te interesen. Puedes elegir los tipos de fichero de cada
carpeta, filtrar por nombre y tamaño, o sacar solo una muestra al azar.

Sirve para juntar de golpe todos los `.java` de un proyecto, todos los `.jsp`
y `.css` que contengan la palabra `cocina` repartidos por tres carpetas, o
veinte ficheros cualesquiera de un directorio enorme para echarles un vistazo.

---

## Instalación

Necesitas Python 3 instalado en Windows. No hace falta nada más: el programa
solo usa la biblioteca estándar.

Deja los dos ficheros en la misma carpeta:

- `ExtraerFicheros.py`
- `ExtraerFicheros.bat`

Y haz doble clic en el `.bat`. Al arrancar por primera vez se crea un tercer
fichero, `config.json`, donde se guardan tus preferencias.

Si al abrirlo no pasa nada, edita el `.bat` con el Bloc de notas y corrige la
ruta de `pythonw.exe` de la primera línea.

---

## La ventana

- **Arriba**: la extensión global, el filtro global de nombre, el selector de
  tema y el botón *Historial*.
- **Columna izquierda**: las carpetas de origen y, debajo, las extracciones
  recientes.
- **Columna derecha**: los favoritos.
- **Abajo**: la carpeta de destino, el progreso y el botón **Extraer ficheros**,
  que siempre queda a la vista.

La ventana crece sola hasta ocupar como mucho el 80 % del alto de tu pantalla.
A partir de ahí, cada sección saca su propia barra de desplazamiento, y la
rueda del ratón mueve la sección que tengas debajo del puntero.

---

## Cómo se usa

1. **Carpetas de origen**: escribe o elige una carpeta en la primera línea
   (botón `...`), y en el campo de al lado sus extensiones, separadas por
   espacios: `.java .jsp .css`. Con *+ Añadir carpeta* metes tantas como
   quieras, cada una con las suyas. La `×` quita una línea y *Limpiar* las
   vacía todas.
2. **Opcional**: filtros (ver más abajo).
3. **Destino**: por defecto, la carpeta del propio programa.
4. Pulsa **Extraer ficheros**.

Debajo del destino verás la carpeta que se va a crear:

| Lo que extraes                                   | Carpeta      |
|--------------------------------------------------|--------------|
| Una sola extensión en todas las líneas           | `CopiaJAVA`  |
| Varias extensiones                               | `CopiaMIXTO` |
| Todas las líneas sin extensión (todos los tipos) | `CopiaTODO`  |
| Mezcla de líneas con y sin extensión             | `CopiaMIXTO` |

Los filtros no influyen en el nombre.

Al terminar, si tienes marcada **Abrir la carpeta al terminar**, se abre el
destino en el explorador en cuanto cierras el aviso de resumen.

---

## Extensiones

- **Una línea con el campo vacío extrae todos los tipos de fichero**, incluidos
  los que no tienen extensión (`Makefile`, `LICENSE`). La tarjeta lo indica con
  *Todos los tipos*.
- **Extensión global**: lo que escribas arriba **se escribe en todas las
  líneas** en cuanto lo modificas (medio segundo después de dejar de teclear).
  Si la cambias, cada línea pierde la extensión global anterior, recibe la
  nueva y conserva lo suyo. Con la global en `.java` y una línea en
  `.jsp .java`, cambiar la global a `.css` deja esa línea en `.jsp .css`.
- La global **solo actúa cuando la modificas**. Al cargar un favorito o un
  reciente, añadir una línea o abrir el programa, no se aplica. Para repartirla
  de nuevo basta con escribir una letra y borrarla.
- Cambiar una línea a mano nunca cambia la global.
- Las extensiones tienen que ser conocidas. Si escribes algo como `.asdhaisud`,
  la extracción **no empieza**: te dice en qué línea está el fallo y qué texto
  exactamente, y no se copia nada.

---

## Filtros

### Filtro global de nombre

Arriba, para todas las líneas a la vez:

- **Inclusión**, con su modo: *Contiene*, *Empieza por* o *Termina por*.
- **Excluir**: descarta todo lo que contenga esa palabra.

Se compara siempre con el **nombre sin la extensión**, sin distinguir
mayúsculas. Por eso `holacocina.java` sí pasa *Termina por* `cocina`.

### Filtros de cada carpeta

El botón **Filtros…** de cada línea abre una ventanita con:

- **Tamaño mínimo y máximo**, en KB. Los dos son opcionales y admiten
  decimales (`1,5`).
- **El nombre contiene**: como el filtro global, pero solo para esa carpeta.
- **Muestra aleatoria**: en vez de todo, saca un **número fijo** de ficheros al
  azar o un **porcentaje**. Se aplica la última, sobre lo que haya quedado tras
  los demás filtros. Si pides un porcentaje pequeño de pocos ficheros, sale al
  menos uno.

Debajo de cada ruta se ve un resumen en azul, por ejemplo
`Filtros: <= 40 KB · 15 al azar`. El aviso final te dice cuántos ficheros
salieron de cuántos en cada carpeta con muestra aleatoria.

Si pones **la misma carpeta en dos líneas con filtros distintos**, se hacen dos
pasadas y los ficheros repetidos se descartan. Así puedes sacar, por ejemplo,
10 al azar y además todos los de menos de 3 KB.

---

## Favoritos

Un favorito es un **grupo entero**: un nombre que le pones tú y la lista
completa de carpetas, cada una con sus extensiones y sus filtros. Al pulsarlo
se cargan todas de golpe.

- **☆ Guardar favorito** guarda las líneas que tengas escritas. Se convierte en
  **★ En favoritos** cuando lo que hay en pantalla coincide exactamente con uno
  guardado, y pulsándolo entonces lo quita.
- La estrella **solo brilla si coinciden las carpetas, las extensiones y los
  filtros**. Cambiar cualquiera de las tres la apaga.
- **Guardar un grupo con las mismas carpetas que un favorito lo sobrescribe**:
  se queda con las extensiones y filtros actuales y te ofrece el nombre
  anterior. Una carpeta de más o de menos ya es un favorito nuevo.
- **Buscar** filtra los favoritos por nombre mientras escribes.
- **Sustituir al cargar**: apagado (de fábrica), pulsar un favorito **añade**
  sus carpetas a las que ya tienes, para combinar varios favoritos en una
  extracción. Encendido, borra lo que haya antes de cargar. Se recuerda.
- Si dejas el ratón quieto sobre un favorito, aparece un recuadro con todas sus
  carpetas, extensiones y filtros.
- No hay límite de favoritos.

---

## Recientes y ficheros guardados

Cada extracción aparece en *Recientes*. Hay **una fila por conjunto de
carpetas**: repetir una extracción sube su fila arriba con lo último que
usaste, sin crear otra. Pulsar una fila carga sus carpetas, y su estrella la
guarda como favorito.

### Ficheros de las últimas extracciones

Además de la lista, ExtractJ puede **conservar una copia de los ficheros** de
las últimas extracciones. La carpeta de destino (`CopiaJAVA`…) se sigue
vaciando en cada extracción; las copias van aparte.

- **Recordar** (1–10): cuántas filas de recientes se guardan.
- **Guardar ficheros de** (0–10): de cuántas de esas extracciones se conserva
  la copia. Nunca puede pasar de *Recordar*. A 0 no se guarda nada.
- **Copias en: … / Cambiar…**: dónde se guardan. Por defecto, una carpeta
  `Extracciones guardadas` junto al programa.

Ejemplo, guardando 3: si extraes en este orden path3, path1, path2, path1,
path1 y path2, quedan guardados los ficheros de la última extracción de path2,
la última de path1 y la de path3.

Los recientes con copia llevan el botón **Ver ficheros (N)**. Abre una ventana
con la lista de ficheros, la carpeta de la que salió cada uno y su tamaño, y un
botón para abrir la copia en el explorador.

**Las copias que sobran se borran solas**: al repetir las mismas carpetas, al
quedar fuera del límite por una extracción nueva y al bajar cualquiera de los
dos contadores. Por seguridad, ExtractJ solo borra carpetas que lleven dentro
su fichero `_contenido_extractj.json`. Nunca toca una carpeta que no haya
creado él.

Cada copia ocupa lo mismo que la extracción. Con código son unos pocos megas;
con imágenes o vídeo, vigila el contador.

---

## Historial

El botón *Historial*, arriba a la derecha, abre una ventana con todas las
extracciones que has hecho: fecha, hora, tipos, cuántos ficheros se copiaron,
de dónde y a dónde. Si tenía varias carpetas, la columna *Origen* muestra la
primera y `(+N)`. Se guardan las 200 últimas y hay un botón para vaciarlo.

---

## Tema

El selector **Tema** de la cabecera tiene tres opciones:

- **Sistema** (de fábrica): sigue el modo claro u oscuro de Windows, y si lo
  cambias con el programa abierto te sigue en unos segundos.
- **Claro** y **Oscuro**: fuerzan uno, sin mirar a Windows.

El cambio se aplica al momento en todas las ventanas del programa, incluida la
barra de título en Windows 10 y 11. Los avisos de Windows y el selector de
carpetas son del sistema y siguen el tema de Windows, no el del programa.

---

## Cosas que conviene saber

- **La carpeta de destino se borra entera antes de cada extracción.** Si ya
  existía, el programa te avisa y te pide confirmación. No guardes nada tuyo
  dentro de una carpeta `Copia...`.
- Los ficheros se copian **planos**, sin respetar la estructura de carpetas del
  origen. Si dos acaban con el mismo nombre, el segundo se guarda como
  `Nombre_1.java`, el tercero como `Nombre_2.java`, y así.
- Los ficheros originales **no se tocan**: es una copia, no un movimiento.
- Si no se encuentra ningún fichero, te avisa, y si tenías filtros te sugiere
  que quizá alguno sea demasiado estricto.
- El destino y la carpeta de copias guardadas no pueden estar dentro de
  ninguna de las carpetas de origen.
- Las rutas largas se ven por el final, que es donde está el nombre de la
  carpeta que importa.

---

## Qué se recuerda entre sesiones

En `config.json`: la extensión global, el destino, si abrir el destino al
terminar, el modo de carga de favoritos, el modo del filtro global, el tema,
los dos contadores de recientes, la carpeta de copias guardadas, los favoritos,
los recientes y el historial. Si borras ese fichero, el programa vuelve a su
estado de fábrica, pero las copias guardadas siguen en su carpeta hasta que
las borres tú.

El fichero está en **formato 3**. Si vienes de una versión anterior, se
convierte solo al arrancar la primera vez y no pierdes favoritos, recientes
ni historial.
