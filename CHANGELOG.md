# Registro de cambios

Notas técnicas para mí, no documentación de usuario. Para eso está `README.md`.

---

## Antes — `ExtrarFicheros.bat`

Script `.bat` de un solo uso. Lo que hacía y por qué se ha reescrito:

- Extensión `.java` fija, escrita a fuego en el bucle `for /r`.
- Destino fijo en `C:\Users\alema\Desktop\CopiaJava`, borrado sin preguntar.
- Origen pedido por `set /p` en la consola, sin validación más allá de
  comprobar que la carpeta existía.
- Sin persistencia de ningún tipo, sin historial, sin progreso real: el eco por
  fichero copiado hacía las veces de barra.
- **Bug latente:** la etiqueta `:buscar` para resolver colisiones estaba dentro
  de un bloque `for`. En `cmd` una etiqueta dentro de un bloque parenteado
  rompe el análisis del bloque; funcionaba de milagro según el contenido.

---

## 2026-07-20 — Reescritura en Python

Migrado a Python 3 + `tkinter`. Sin dependencias externas, todo biblioteca
estándar (`tkinter`, `ttk`, `json`, `shutil`, `os`, `threading`, `queue`).
Un único fichero, `ExtraerFicheros.py`, más un `.bat` lanzador que apunta a
`pythonw.exe` por ruta absoluta (el alias de la Microsoft Store ensombrece el
PATH en esta máquina; mismo problema que en la barra de jornada).

### Modelo de datos

- `config.json` junto al ejecutable, no en `%APPDATA%`. Decisión deliberada:
  el programa es portable y se lleva a otros equipos con la carpeta entera.
  `directorio_programa()` contempla `sys.frozen` por si algún día se empaqueta
  con PyInstaller.
- Un solo fichero de configuración, no dos. A diferencia de la barra de
  jornada, aquí no hay estado efímero que separar de las preferencias.
- Todas las comparaciones de rutas pasan por `_normalizar()`
  (`normcase` + `normpath`). En Windows hace falta para que
  `C:\Proyecto` y `c:\proyecto\` sean la misma entrada de favoritos.
- Recientes y favoritos son listas independientes. Un favorito puede estar a la
  vez en recientes; la estrella se pinta consultando `es_favorito()`, no la
  lista en la que vive la fila.

### Validación de extensión

Dos comprobaciones que son **casos distintos** y dan mensajes distintos:

1. La extensión no está en `EXTENSIONES_VALIDAS` → error, no se ejecuta nada.
   Lista blanca de ~130 extensiones, ampliable en una línea.
2. La extensión es válida pero `os.walk` no encuentra coincidencias → aviso de
   "no se han encontrado ficheros", sin tocar el destino.

La segunda se evalúa **antes** de borrar la carpeta destino. Importante: si se
hiciera después, una extracción fallida destruiría la copia anterior.

`normalizar_extension()` acepta `java`, `.java`, `.JAVA` y `*.java`.

### Copia

- `os.walk` recoge la lista completa antes de empezar, para poder fijar el
  máximo de la `Progressbar` en modo determinado.
- Colisiones: el conjunto `usados` es **por ejecución**, no contra el disco. Es
  la semántica correcta desde que el destino se borra y se recrea; comprobar
  con `os.path.exists` daría el mismo resultado pero con una llamada al sistema
  por fichero.
- Guarda contra destino dentro de origen. Sin esto, el `os.walk` previo no lo
  ve (aún no existe la carpeta) pero una segunda ejecución copiaría la copia.
- Los fallos de `shutil.copy2` se acumulan en `fallidos` y no abortan el
  proceso; se resumen al final. Un fichero bloqueado no debe tirar la tanda.

### Concurrencia

- La copia va en un `threading.Thread` daemon; el hilo no toca widgets, publica
  tuplas en una `queue.Queue` y el hilo de UI las drena con `after(60, ...)`.
  Tkinter no es seguro desde otros hilos.
- `_procesar_cola` vacía la cola entera en cada pasada. Con miles de ficheros
  pequeños la copia produce mensajes mucho más rápido que los 60 ms de refresco;
  procesar uno por pasada dejaría la barra retrasada respecto al trabajo real.
- El botón de extraer se deshabilita mientras el hilo vive, más una guarda
  `is_alive()` al entrar por si acaso.

### Interfaz

- Favoritos y recientes viven en dos `Frame` contenedores que se destruyen y
  reconstruyen enteros en `_refrescar_rutas()`. Es fuerza bruta, pero son 6
  filas como mucho y evita llevar contabilidad de widgets. La cabecera de cada
  sección se crea dentro del mismo método, así una lista vacía no deja ni el
  título ni huecos.
- Las estrellas son `tk.Button` y no `ttk.Button`: `ttk` no deja fijar `fg` de
  forma directa sin pelearse con el tema.
- `trace_add` sobre extensión y destino para actualizar en vivo la etiqueta con
  la carpeta que se va a crear. Es lo que evita la sorpresa de descubrir el
  nombre `FicheroCopiaXXX` después de pulsar.
- Historial en un `ttk.Treeview` aparte, en `Toplevel` transitorio.

### Pendiente / posibles mejoras

- No hay botón de cancelar durante la copia.
- El historial no se puede filtrar ni exportar.
- La barra de la ventana de historial está posicionada con `place` sobre un
  `relheight` fijo; si se cambia la altura del pie, hay que ajustarlo.

---

## 2026-07-21 — Favoritos y recientes con extension y nombre

Cambio de formato en `config.json`. Antes favoritos y recientes eran listas de
strings (rutas en crudo). Ahora son listas de diccionarios:

    {"nombre": str, "ruta": str, "extension": str}   # favoritos
    {"ruta": str, "extension": str}                  # recientes (sin nombre)

- **Identidad = ruta + extension.** La misma carpeta con `.py` y con `.java`
  son ahora dos entradas independientes. Todas las comprobaciones pasan por
  `_clave()`, que combina `_normalizar(ruta)` con la extension en minusculas.
- **Migracion automatica.** `_normalizar_lista()` acepta tanto strings del
  formato viejo como dicts del nuevo. A una entrada antigua se le asigna como
  extension la que hubiera configurada al cargar y como nombre la propia ruta.
  No hace falta borrar el `config.json` existente.
- **Al pulsar un favorito o reciente** se rellenan origen y extension a la vez
  (`_usar_ruta`).
- **Nombre editable.** Se pide con `simpledialog.askstring` al crear el
  favorito (por la estrella o por el boton `+`), con el nombre de la carpeta
  como valor inicial. Boton *Renombrar* en cada fila de favorito.
- La estrella de un reciente ahora abre el dialogo de nombre en vez de anadir
  en silencio; `_alternar_estrella` decide entre crear o quitar.
- Cada fila muestra una etiqueta con la extension en mayusculas a la izquierda
  del texto. Los favoritos muestran el nombre; los recientes, la ruta acortada.
- El boton `+` exige que haya extension escrita, no solo ruta.

`simpledialog` es biblioteca estandar, no anade dependencias.

---


## 2026-09-02 — Altura dinamica, favoritos sin tope y apertura del destino

Tres cambios pedidos: el boton *Extraer* quedaba tapado al acumular favoritos,
los favoritos estaban topados a tres, y habia que abrir el destino a mano.

### Reestructuracion del layout

La ventana estaba montada como un solo `grid` de 14 filas dentro de un marco
raiz. Con muchos favoritos el contenido crecia hacia abajo y el boton se salia
del alto fijo (`640x560`), que no se ajustaba nunca.

Ahora son tres bloques dentro del marco raiz:

- `superior` — cabecera, extension y carpeta de origen. `pack(side="top")`.
- `inferior` — destino, casilla, progreso, estado y boton *Extraer*.
  `pack(side="bottom")`.
- `medio` — favoritos y recientes, dentro de un `Canvas` desplazable.
  `pack(side="top", expand=True)`.

**El `inferior` se empaqueta antes que el `medio`.** Ese orden es lo que
garantiza que el boton nunca se tape: `pack` reserva primero el espacio de
arriba y de abajo, y lo que sobra va al bloque expansible del medio.

### Ajuste automatico de altura

`_ajustar_altura()`, llamado desde `_refrescar_rutas()`:

1. Fija el alto pedido del lienzo al alto real de su contenido.
2. Mide `winfo_reqheight()` de la ventana entera.
3. Si pasa del tope (`FRACCION_ALTO_MAX`, 80% del alto de pantalla), le recorta
   al lienzo exactamente lo que sobra, con suelo `ALTO_MINIMO_RUTAS`.
4. Aplica `geometry()`. El ancho se respeta si la ventana ya esta mapeada.

Se ha quitado la geometria inicial fija; queda `minsize(600, ALTO_MINIMO)`.

### Bucle infinito de `<Configure>` (importante)

Primer intento: los manejadores `<Configure>` del lienzo y del marco interior
llamaban directamente a la funcion que muestra u oculta la barra. Resultado:
cuelgue duro dentro de `update_idletasks()`. Empaquetar o desempaquetar la
barra cambia el ancho del lienzo → dispara `<Configure>` → vuelve a evaluar →
vuelve a empaquetar. Realimentacion sin fondo.

Solucion, separando responsabilidades:

- `_region_scroll()` — solo recalcula `scrollregion`. Es lo unico que corre
  dentro de un `<Configure>`. No toca el empaquetado.
- `_actualizar_scroll()` — decide si la barra se ve. Nunca se llama de forma
  sincrona desde un evento.
- `_programar_scroll()` — `after(120, ...)` con cancelacion de la tarea
  anterior. El retardo **real** (no `after_idle`) es lo que rompe el ciclo: el
  `<Configure>` que genera el propio cambio de barra programa otra revision,
  pero para entonces el estado ya es estable y no cambia nada.

Margen de 2 px en la comparacion como histeresis, para no oscilar en el limite.

Rueda del raton vinculada con `bind_all` al entrar en el lienzo y liberada al
salir, para no secuestrarla en el resto de la ventana.

### Favoritos sin limite

Fuera `MAX_FAVORITOS`. Afecta a: el recorte al cargar `config.json`, la
comprobacion en `anadir_favorito()`, el aviso en `_crear_favorito()` y
`_refrescar_boton_anadir()`, que desaparece (el boton `+` ya no se desactiva).
`MAX_RECIENTES` sigue en 3.

### Abrir la carpeta al terminar

- Nueva clave `abrir_al_terminar` en `config.json`, por defecto `True`. Si no
  existe se crea sola; las configuraciones antiguas siguen valiendo.
- Casilla en el bloque inferior. Se guarda al pulsarla, no solo al cerrar.
- `abrir_carpeta()` usa `os.startfile()` en Windows. Hay ramas `open` y
  `xdg-open` por si esto acaba corriendo fuera de Windows; `subprocess` es la
  unica importacion nueva y es de la biblioteca estandar.
- Se abre **despues** del aviso de resumen, para que el explorador no quede
  detras del dialogo modal, y solo si se ha copiado al menos un fichero. Si
  falla la apertura no se muestra otro dialogo: se refleja en la barra de
  estado.

### Detalle menor

Los botones de estrella usaban `self.cget("bg")` (el `COLOR_FONDO` del
`Toplevel`), que no coincide con el fondo real de los marcos `ttk` con el tema
`clam`. Ahora usan `estilo.lookup("TFrame", "background")`, igual que el
lienzo, y no se nota el recuadro.

## 2026-09-18 — Multi-ruta, filtro por nombre y favoritos de grupo

Cambio grande: la extraccion deja de ser "una carpeta, una extension" y pasa a
ser "varias carpetas, cada una con sus extensiones, filtradas por nombre".
Arrastra un cambio de formato en `config.json` y una reescritura del modelo de
favoritos.

### Formato de configuracion

`config.json` sube a `version: 2`. Favoritos y recientes pasan a ser **grupos**:

```json
{"nombre": "JAVAs", "rutas": [{"ruta": "C:\\...", "extensiones": [".java"]}]}
```

`_migrar_grupos()` acepta los tres formatos historicos y los normaliza al
cargar: cadena suelta con la ruta, dict de ruta + extension (formato 1), y el
grupo actual. Despues, `_fusionar_favoritos_repetidos()` une los favoritos que
comparten conjunto de rutas, que es lo que produce migrar del formato 1 cuando
la misma carpeta estaba guardada dos veces con extensiones distintas.

Claves nuevas: `version`, `sustituir_al_cargar`, `max_recientes`,
`filtro_modo`. Todas se crean solas si no existen.

### Identidad de un favorito

Dos niveles, y conviene no mezclarlos:

- `clave_rutas()` — solo el conjunto de rutas, ignorando extensiones. Decide si
  guardar es **alta o sobrescritura**. Mismo conjunto, aunque cambien las
  extensiones, es la misma entrada. Una ruta de mas o de menos ya es otra.
- `clave_completa()` — rutas **y** extensiones. Decide si la **estrella
  brilla**. Un favorito con las mismas carpetas pero otras extensiones no
  enciende nada.

La sobrescritura no acumula: el favorito viejo se sustituye entero por el
nuevo, con las extensiones que haya en pantalla en ese momento. El nombre viejo
se ofrece como valor inicial del dialogo y se puede cambiar.

### Extensiones por linea

Cada linea de origen lleva su propio campo de texto (`.java .jsp .css`,
separadas por espacios, comas o puntos y comas). `parsear_extensiones()`
devuelve dos listas, validas e invalidas, y la invalida conserva el texto tal
cual lo escribio el usuario para poder decirle exactamente que pieza falla.

La **extension global** de la cabecera es **aditiva**: se suma a las de cada
linea sin sustituirlas. Vacia, no aporta nada. Entra en el calculo de la
estrella, no solo en el del nombre del destino: cambiarla cambia las
extensiones efectivas de todas las lineas y por tanto puede apagar la estrella.

Si una linea tiene una extension con formato invalido, se aborta la extraccion
**entera** sin copiar un solo fichero, diciendo numero de linea y texto exacto.

### Filtro por nombre

Campo de inclusion con modo (contiene / empieza por / termina por) y campo de
exclusion aparte, combinables. Se comparan contra el nombre **sin extension**,
que es lo que hace util el modo "termina por": `holacocina.java` termina por
`cocina`. Todo en minusculas.

### Tres paneles desplazables

`PanelDesplazable` encapsula lienzo + marco interior + barra automatica, y se
usa tres veces: lineas de origen, favoritos y recientes. Cada uno con su tope
de filas visibles (6, 8, y el que marque el contador de recientes).

Se mantiene la leccion de la version anterior, ahora dentro de la clase: los
manejadores de `<Configure>` **solo** recalculan `scrollregion`. La visibilidad
de la barra se decide siempre con `after(120)` cancelando la tarea anterior,
porque empaquetar la barra cambia el ancho del lienzo y eso dispara otro
`<Configure>`. Con `after_idle` el bucle se reproduce igual: hace falta un
retardo real.

`_ajustar_altura()` reparte: cada panel pide su contenido limitado por su tope
de filas, y si la ventana entera se pasa del 80% de pantalla va recortando en
orden — favoritos, recientes y por ultimo origen, que es lo que el usuario esta
editando.

### Carga de grupos

Por defecto **anade** al pulsar un favorito o reciente; si la ruta ya esta en
pantalla se actualizan sus extensiones en vez de duplicar la linea. El
interruptor *Sustituir las lineas al cargar* cambia el comportamiento y es
persistente. El boton *Limpiar* vacia todas las lineas. Si las lineas estan
vacias, anadir y sustituir hacen lo mismo.

### Extraccion

`_buscar()` recorre cada origen con **sus** extensiones y aplica el filtro,
deduplicando por ruta normalizada. Rutas repetidas entre lineas se fusionan
antes de empezar en vez de recorrerse dos veces.

Destino: `CopiaJAVA` si todas las extensiones coinciden, `CopiaMIXTO` si hay
varias. El filtro no influye en el nombre. La comprobacion de "el destino no
puede estar dentro del origen" ahora se hace contra **todos** los origenes.

El historial guarda `origenes` (lista completa) ademas de `origen` (el primero,
por compatibilidad con las filas viejas) y muestra la primera ruta recortada
mas `(+N)`. Los recientes guardan una fila por extraccion, con contador de 1 a
10 en la interfaz.

### Probado

Migracion del `config.json` real; extraccion de dos carpetas con extensiones
distintas y filtro (5 ficheros de 10); extension invalida abortando limpiamente;
extension global sumando y apagando la estrella; sobrescritura de favorito por
conjunto de rutas; alta al anadir una ruta mas; los dos modos de carga; busqueda
de favoritos; 20 favoritos y 11 lineas con los tres scrolls activos y el boton
*Extraer* dentro de la ventana; arranque sin `config.json`; estrella de
recientes sincronizada; persistencia de todas las claves nuevas.
