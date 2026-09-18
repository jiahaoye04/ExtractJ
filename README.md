# Extraer Ficheros

Recorre una o varias carpetas y todas sus subcarpetas, y copia en un único
sitio los ficheros de las extensiones que le digas, con un filtro opcional por
nombre. Útil para juntar de golpe todos los `.java` de un proyecto, o todos los
`.jsp` y `.css` que contengan la palabra `cocina` repartidos por tres carpetas
distintas.

---

## Instalación

Necesitas Python 3 instalado en Windows. No hace falta nada más.

Deja los dos ficheros en la misma carpeta:

- `ExtraerFicheros.py`
- `ExtraerFicheros.bat`

Y haz doble clic en el `.bat`. Al arrancar por primera vez se crea un tercer
fichero, `config.json`, donde se guardan tus preferencias.

Si al abrirlo no pasa nada, edita el `.bat` con el Bloc de notas y corrige la
ruta de `pythonw.exe` de la primera línea.

---

## Cómo se usa

1. **Carpetas de origen**: escribe o elige una carpeta en la primera línea, y
   en el campo de al lado sus extensiones, separadas por espacios:
   `.java .jsp .css`. Con *+ Añadir línea* metes tantas carpetas como quieras,
   cada una con sus propias extensiones. La `×` quita una línea y *Limpiar* las
   vacía todas.
2. **Extensión global** (arriba): lo que escribas ahí **se suma** a las
   extensiones de todas las líneas. Si la línea 1 tiene `.jsp` y arriba pones
   `.java`, esa línea extrae las dos. Vacía, no aporta nada.
3. **Filtro por nombre** (opcional): ver el apartado de abajo.
4. **Carpeta de destino**: por defecto es la carpeta del propio programa.
5. Pulsa **Extraer ficheros**.

Debajo del destino verás la carpeta que se va a crear realmente. Si todas las
líneas comparten una sola extensión, se llama `CopiaJAVA`, `CopiaJSP`, etc. Si
hay varias, se llama `CopiaMIXTO`. El filtro no influye en el nombre.

Mientras copia verás la barra de progreso, el contador de ficheros y el nombre
del que está copiando en ese momento.

Al terminar, si tienes marcada la casilla **Abrir la carpeta al terminar**, se
te abre el destino en el explorador en cuanto cierras el aviso de resumen. La
casilla viene marcada de fábrica y se recuerda. Solo se abre si se ha copiado
al menos un fichero.

---

## Filtro por nombre

Dos campos que se pueden combinar:

- **Inclusión** con su modo: *Contiene*, *Empieza por* o *Termina por*.
- **Excluir**: descarta todo lo que contenga esa palabra.

Se comparan siempre contra el **nombre sin la extensión**, y sin distinguir
mayúsculas. Por eso `holacocina.java` sí pasa el filtro *Termina por* `cocina`:
la extensión no cuenta. Los dos campos vacíos, no filtra nada.

Ejemplo: *Termina por* `cocina` más excluir `test` sobre una carpeta de `.java`
se queda con `holacocina.java` y descarta `test_cocina.java` y `cliente.java`.

---

## Favoritos y recientes

Un favorito es un **grupo entero**: un nombre que le pones tú y la lista
completa de carpetas con sus extensiones. Al pulsarlo se cargan todas de golpe.

- El botón **☆ Guardar como favorito** guarda las líneas que tengas escritas en
  ese momento. Se pone **★ En favoritos** cuando lo que hay en pantalla coincide
  exactamente con uno guardado, y pulsándolo entonces lo quita.
- La estrella de cada fila de *Recientes* hace lo mismo con esa extracción.
- **La estrella solo brilla si coinciden las carpetas Y las extensiones.** Si el
  favorito tiene `.java` y en la línea pones `.java .jsp`, se apaga hasta que lo
  actualices. Cambiar la extensión global también la apaga, porque cambia las
  extensiones efectivas.

**Guardar un grupo cuyas carpetas ya son favoritas lo sobrescribe**, no crea
otro. Se queda con las extensiones que tengas ahora, sin acumular las viejas, y
te ofrece el nombre anterior por si lo quieres conservar. Basta con que cambie
una carpeta —una de más o una de menos— para que sea un favorito nuevo.

- **Buscar**: filtra los favoritos por nombre mientras escribes.
- **Sustituir las líneas al cargar**: con el interruptor apagado (de fábrica),
  pulsar un favorito **añade** sus carpetas a lo que ya tengas, lo que permite
  combinar dos favoritos en una extracción. Si una carpeta ya está en pantalla
  se le actualizan las extensiones en vez de duplicar la línea. Encendido,
  borra lo que haya antes de cargar. La preferencia se recuerda.
- **Recientes**: una fila por extracción, mostrando la primera carpeta y
  `(+N)` si había más. Con el contador de al lado eliges cuántas ver, de 1 a 10.

No hay límite de favoritos ni de carpetas de origen. Cuando no caben, cada
sección saca su propia barra de desplazamiento y la ventana crece hasta ocupar
como mucho el 80% del alto de tu pantalla. El botón *Extraer ficheros* queda
siempre a la vista.

---

## Historial

El botón *Historial*, arriba a la derecha, abre una ventana con todas las
extracciones que has hecho: fecha, hora, extensiones, cuántos ficheros se
copiaron, de dónde y a dónde. Si la extracción tenía varias carpetas, la
columna *Origen* muestra la primera y `(+N)`. Se guardan las 200 últimas y hay
un botón para vaciarlo.

---

## Cosas que conviene saber

- **La carpeta de destino se borra entera antes de cada extracción.** Si ya
  existía, el programa te avisa y te pide confirmación. No guardes nada tuyo
  dentro de una carpeta `Copia...`.
- Los ficheros se copian **planos**, sin respetar la estructura de carpetas del
  origen. Si dos ficheros acaban teniendo el mismo nombre —algo bastante más
  probable ahora que se puede extraer de varias carpetas a la vez—, el segundo
  se guarda como `Nombre_1.java`, el tercero como `Nombre_2.java`, y así.
- Los ficheros originales **no se tocan**: es una copia, no un movimiento.
- Las extensiones tienen que ser conocidas. Si escribes algo como `.asdhaisud`,
  la extracción **no empieza**: te dice en qué línea está el fallo y qué texto
  exactamente, y no se copia nada. Si son válidas pero no hay ningún fichero que
  cumpla, te avisa de que no ha encontrado nada, y si tenías filtro te sugiere
  que quizá sea demasiado estricto.
- Si repites la misma carpeta en dos líneas, se fusionan en una sola pasada
  sumando sus extensiones: no se recorre dos veces.
- El destino no puede estar dentro de ninguna de las carpetas de origen.

---

## Qué se recuerda entre sesiones

En `config.json` se guardan la extensión global, la carpeta de destino, si
abrir el destino al terminar, el modo de carga de favoritos, el modo del filtro,
cuántos recientes mostrar, los favoritos, los recientes y el historial. Si
borras ese fichero, el programa vuelve a su estado de fábrica.

El fichero está en **formato 2**. Si vienes de una versión anterior, tus
favoritos y recientes se convierten solos al arrancar la primera vez: cada uno
pasa a ser un grupo de una sola carpeta con su extensión, conservando el
nombre. Si tenías la misma carpeta guardada dos veces con extensiones distintas,
se fusionan en un único favorito con las dos.
