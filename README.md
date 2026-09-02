# Extraer Ficheros

Recorre una carpeta y todas sus subcarpetas, y copia en un único sitio todos
los ficheros de la extensión que le digas. Útil para juntar de golpe todos los
`.java` de un proyecto, todos los `.pdf` de un archivo, etc.

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

1. **Extensión**: escribe el tipo de fichero que quieres recoger, por ejemplo
   `.java`. Vale escribirlo sin el punto.
2. **Carpeta de origen**: pega la ruta o pulsa *Examinar*.
3. **Carpeta de destino**: por defecto es la carpeta del propio programa.
4. Pulsa **Extraer ficheros**.

Debajo del destino verás la carpeta que se va a crear realmente. El nombre se
forma solo a partir de la extensión: `.java` da `CopiaJAVA`, `.py` da `CopiaPY`.

Mientras copia verás la barra de progreso, el contador de ficheros y el nombre
del que está copiando en ese momento.

Al terminar, si tienes marcada la casilla **Abrir la carpeta al terminar**, se
te abre el destino en el explorador en cuanto cierras el aviso de resumen. La
casilla viene marcada de fábrica y se recuerda para la próxima vez. Solo se
abre si se ha copiado al menos un fichero.

---

## Favoritos y recientes

Un favorito guarda tres cosas: un **nombre** que le pones tú, la **ruta** y la
**extensión**. Al pulsarlo se rellenan a la vez la carpeta de origen y la
extensión, así que con un clic lo tienes todo listo para extraer.

- Las **tres últimas combinaciones** de carpeta y extensión que hayas usado
  aparecen solas en *Recientes*. Pulsa una para volver a usarla.
- La estrella gris de la izquierda la convierte en **favorita** (se pone
  amarilla). Al hacerlo te pide el nombre. Los favoritos no se pierden nunca,
  aunque dejes de usarlos.
- También puedes pulsar el botón **+** que hay junto a la carpeta de origen
  para guardar lo que tengas escrito en ese momento.
- *Renombrar* cambia el nombre de un favorito; *Quitar* lo borra (o vuelve a
  pulsar su estrella).
- **No hay límite de favoritos.** La ventana crece sola para que quepan todos,
  hasta ocupar como mucho el 80% del alto de tu pantalla. A partir de ahí
  aparece una barra de desplazamiento en esa zona y puedes usar la rueda del
  ratón. El botón *Extraer ficheros* queda siempre a la vista, por muchos
  favoritos que tengas.

La misma carpeta con dos extensiones distintas son **dos entradas separadas**:
puedes tener guardado el mismo proyecto para `.java` y para `.jsp` a la vez.

Si no tienes ningún favorito, esa sección no aparece.

---

## Historial

El botón *Historial*, arriba a la derecha, abre una ventana con todas las
extracciones que has hecho: fecha, hora, tipo de fichero, cuántos se copiaron,
de dónde y a dónde. Se guardan las 200 últimas y hay un botón para vaciarlo.

---

## Cosas que conviene saber

- **La carpeta de destino se borra entera antes de cada extracción.** Si ya
  existía, el programa te avisa y te pide confirmación. No guardes nada tuyo
  dentro de una carpeta `Copia...`.
- Los ficheros se copian **planos**, sin respetar la estructura de carpetas del
  origen. Si en el origen hay dos ficheros con el mismo nombre en carpetas
  distintas, el segundo se guarda como `Nombre_1.java`, el tercero como
  `Nombre_2.java`, y así.
- Los ficheros originales **no se tocan**: es una copia, no un movimiento.
- La extensión tiene que ser una conocida. Si escribes algo como `.asdhaisud`
  el programa lo rechaza. Si escribes una válida pero no hay ningún fichero de
  ese tipo en el origen, te avisa de que no ha encontrado nada: son dos avisos
  distintos.
- El destino no puede estar dentro del origen.

---

## Qué se recuerda entre sesiones

En `config.json` se guardan la última extensión usada, la carpeta de destino,
si quieres que se abra el destino al terminar, los favoritos, los recientes y
el historial. Si borras ese fichero, el programa vuelve a su estado de fábrica.