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

---

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

---

## 2026-10-29 — Filtros por carpeta, dos columnas, modo oscuro y copias guardadas

Sesión larga, con cuatro cambios grandes y una corrección. Todo sigue en
biblioteca estándar; las importaciones nuevas son `math`, `random`, `re`,
`ctypes` y `winreg` (estas dos solo se usan en Windows y siempre dentro de un
`try`).

### Formato de configuración (version 3)

- Cada ruta de un grupo lleva ahora `"filtros"`. Un reciente puede llevar además
  `"guardado"` (carpeta, fecha y total de su copia guardada).
- Claves nuevas: `tema`, `max_guardados`, `carpeta_guardados`.
- `_migrar_grupos()` sigue aceptando los cuatro formatos (cadena suelta,
  formato 1, 2 y 3). A lo que viene sin filtros se le ponen filtros vacíos, y
  en los recientes conserva `"guardado"`, que antes se habría perdido al cargar.
- `normalizar_filtros()` es la **única puerta** de entrada de los filtros,
  venga del config, de la ventana o de un favorito: cualquier valor raro se
  descarta en silencio en vez de romper el arranque. Acepta coma decimal.

### Recientes: uno por conjunto de carpetas

La deduplicación pasa de `clave_completa()` (rutas + extensiones) a
`clave_rutas()` (solo rutas). Extraer path1 con `.java` y luego con `.jsp` ya
no ocupa dos filas: queda una con lo último. Al cargar, `_deduplicar_recientes()`
limpia los configs viejos que tuvieran la misma carpeta dos veces.

**Malentendido apuntado para no repetirlo:** cuando se pidió "guardar las
últimas extracciones" con el ejemplo path3, path1, path2, path1, path1, path2,
lo leí como una regla de deduplicación de la lista y no como lo que era:
conservar los **ficheros** copiados. Lo segundo está más abajo, en *Ficheros de
las últimas extracciones*.

### Filtros por carpeta y muestra aleatoria

- Ventana modal `VentanaFiltros` por línea: tamaño mínimo y máximo en KB,
  texto que debe contener el nombre, y muestra aleatoria por número fijo o por
  porcentaje. Valida al aceptar (número, no negativo, mín ≤ máx, entero, 1–100).
- Orden por fichero en `_buscar()`: extensión → filtro global de nombre →
  texto de la carpeta → tamaño. El `getsize` va el último porque es el único
  que toca el disco.
- La muestra aleatoria se aplica **por carpeta y al final**, sobre lo que haya
  sobrevivido. `random.sample` es uniforme. El porcentaje redondea hacia arriba
  (`ceil`): un 10 % de 3 ficheros saca 1, no 0.
- `clave_completa()` incluye ahora los filtros, así que la estrella solo brilla
  si coinciden rutas, extensiones **y** filtros. Si no, diría "guardado" cuando
  volver a guardar cambiaría algo.
- Misma carpeta en dos líneas: solo se fusionan si tienen los mismos filtros.
  Con filtros distintos son dos pasadas y los repetidos se descartan por ruta
  normalizada (`vistos`), así que se puede pedir "10 al azar" y además "todo lo
  de menos de 3 KB" de la misma carpeta.

### Corrección: líneas sin extensión y extensión global sincronizada

Antes una línea sin extensiones daba error ("no tiene ninguna extensión") y la
global se sumaba por detrás, sin verse. Ahora:

- **Línea vacía = todos los tipos**, incluidos ficheros sin extensión
  (`Makefile`, `LICENSE`). La tarjeta lo dice ("Todos los tipos") para que no
  parezca un olvido.
- **La global solo actúa al modificar su campo.** Entonces se escribe de verdad
  en cada línea: `sustituir_global()` quita lo que puso la global anterior
  (`_global_aplicada`) y añade lo de la nueva, respetando lo que la línea tenga
  suyo, incluidas piezas inválidas para que el aviso al extraer las siga viendo.
  Cargar un favorito o reciente, añadir una línea o arrancar con una global
  guardada **no** la aplican; `_global_aplicada` empieza vacía.
- Se aplica con **500 ms de retardo** desde la última tecla (`MS_APLICAR_GLOBAL`).
  Letra a letra, escribir `.cs` pasaría por `.c`, que es válida, y se llevaría
  un `.c` escrito a mano en una línea. Escribir y borrar una letra cuenta como
  modificación y la vuelve a repartir aunque el valor final no cambie.
- Al extraer cuenta solo lo que hay escrito en cada línea. Una global con una
  pieza inválida no se escribe en ninguna línea, pero sigue bloqueando la
  extracción con su aviso.
- `nombre_carpeta_destino()` recibe ahora las líneas, no una lista plana de
  extensiones: `CopiaTODO` si todas son de todos los tipos, `CopiaMIXTO` si se
  mezclan, `CopiaJAVA` y similares si todo es una sola extensión.
- Al fusionar la misma carpeta con los mismos filtros, gana *todos los tipos*.

### Interfaz a dos columnas

- Izquierda: líneas de origen y, debajo, recientes. Derecha: favoritos con todo
  el alto. Primera versión con recientes a la derecha: favoritos enseñaba 3 de
  6 mientras a la izquierda sobraba hueco. Recientes encaja bajo origen porque
  es lo que se extrajo antes.
- `_ajustar_altura()` trabaja por columnas: el alto de la ventana lo marca la
  más alta, y si se pasa del tope se recortan las dos hasta el mismo objetivo
  (izquierda: recientes y luego origen; derecha: favoritos). Dos pasadas: en la
  primera nadie baja de 2 filas, y solo si no basta se baja al mínimo absoluto.
- El ancho inicial (1120) solo se impone la primera vez; después se respeta el
  que deje el usuario.
- Tarjetas (`Tarjeta.TFrame`): fondo propio con borde fino para cada línea,
  favorito y reciente. Es lo que quita la sensación de "todo pegado".
- **`clam` impone a `TButton` un ancho mínimo de 11 caracteres.** En los
  botones pequeños eso los volvía enormes y estrujaba las rutas. Los estilos
  `Pequeno`, `Barra`, `Nombre` y `Ruta` llevan `width=0`.
- `AyudaEmergente`: al dejar el ratón quieto sobre un favorito o reciente,
  recuadro con todas sus carpetas, extensiones y filtros. El `Toplevel` cuelga
  de la tarjeta, así que muere con ella cuando se reconstruye la lista.
- Las rutas largas enseñan el final (`xview_moveto(1.0)`), que es donde está el
  nombre de la carpeta. Se repite en cada `<Configure>` del campo salvo que
  tenga el foco, para no mover el cursor mientras se escribe.
- `nombre_carpeta()` corta por `/` y por `\` en cualquier sistema;
  `os.path.basename` no corta por `\` fuera de Windows.

### Rueda del ratón (bug desde septiembre)

Cada panel enlazaba la rueda al `<Enter>` de su lienzo y la soltaba en el
`<Leave>`. Pero Tk también genera `<Leave>` (con detalle `NotifyInferior`) al
pasar del lienzo a uno de sus hijos, así que sobre las filas la rueda dejaba de
responder: solo funcionaba en los huecos vacíos. Ahora hay un único manejador
global, `_rueda_global()`, que mira con `winfo_containing()` qué hay bajo el
puntero y sube por los padres hasta encontrar un `PanelDesplazable`. Atiende
`<MouseWheel>` (Windows) y `<Button-4>`/`<Button-5>` (Linux).

### Historial

La barra de scroll pasa de `place` con `relheight` fijo a `pack`. Resuelve el
pendiente de julio: ya no hay que ajustarla al cambiar la altura del pie.

### Modo oscuro

- Dos paletas en `PALETAS`. `P` es la **activa** y se modifica en sitio al
  cambiar de tema, así que todo lo que lee de `P` al crearse nace ya con los
  colores buenos. Gris carbón, no negro puro: el negro absoluto cansa y hace
  que los bordes de las tarjetas se pierdan.
- Los widgets `ttk` se repintan solos al reconfigurar sus estilos
  (`_configurar_estilos()` se puede llamar las veces que haga falta). Lo que
  **no** es ttk se toca a mano en `_aplicar_tema()`: la raíz, los lienzos de
  los paneles (`PanelDesplazable.instancias`), las estrellas de recientes, que
  son `tk.Button`, y los `Toplevel` abiertos.
- `option_add` para los widgets tk clásicos que tkinter crea por su cuenta: el
  diálogo de `simpledialog` y la lista desplegable de los `Combobox`. Solo
  afecta a los que se crean después, que es justo lo que hace falta.
- El tema se aplica **antes** de construir la interfaz, para que no haya un
  parpadeo en claro al arrancar.
- *Sistema* lee `AppsUseLightTheme` de
  `HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize` con
  `winreg`, y lo sondea cada 3 s (Windows no avisa a Tk del cambio).
- Barra de título: `DwmSetWindowAttribute` con el atributo 20 (Windows 11 y
  10 desde 20H1) o el 19 (builds anteriores), y después `SetWindowPos` con
  `SWP_FRAMECHANGED`, o el cambio no se ve hasta que la ventana pierde el
  foco. `bind_class("Toplevel", "<Map>")` lo aplica a cualquier ventana que se
  abra.
- Límite: `messagebox` y `filedialog` son nativos y siguen el tema de Windows,
  no el de ExtractJ.
- El botón *Extraer ficheros* pasa a color de acento en los dos temas.

### Ficheros de las últimas extracciones

- Tras copiar, el resultado se copia también a un almacén
  (`carpeta_guardados`, vacío = `Extracciones guardadas` junto al programa), en
  una subcarpeta `AAAA-MM-DD_HH-MM-SS_CopiaXXX`. Se copia **desde la carpeta
  destino recién llenada**, no otra vez desde los orígenes: así la copia es
  exactamente lo extraído, con los `_1`, `_2` resueltos y la misma muestra
  aleatoria.
- Dentro de cada copia va `_contenido_extractj.json` con la firma
  `"programa": "ExtractJ"`, las rutas y la lista de ficheros con su origen y
  tamaño. `VentanaContenido` lo lee para mostrar la lista.
- **El marcador es la red de seguridad del borrado.** `borrar_carpeta_guardada()`
  es la única función que borra copias y solo hace `rmtree` si encuentra la
  firma. Un config editado a mano o una ruta que apunte a otra cosa nunca acaba
  borrando algo que no haya creado el programa. Probado con una carpeta ajena
  referenciada en el config: sobrevive.
- Modelo: cada copia cuelga de su reciente (`"guardado"`). Solo la conservan
  los `max_guardados` recientes más nuevos, y `max_guardados ≤ max_recientes`
  siempre. Toda copia que deja de estar referenciada se borra en
  `_podar_guardados(antes)`, que compara el conjunto de carpetas antes y
  después de cada cambio. Así se cubren de una vez los cuatro casos: repetir
  las mismas carpetas, que una extracción nueva empuje fuera a otra, bajar el
  contador y bajar *Recordar*.
- `anadir_reciente()` **hereda** la copia de la fila vieja de las mismas
  carpetas hasta que la extracción nueva guarde la suya. Si la nueva falla o no
  copia nada, no se pierde la copia anterior.
- El almacén no puede estar dentro de un origen (la siguiente extracción se
  llevaría las copias); se comprueba al extraer, como con el destino.
- Si el guardado falla, la extracción vale igual: se limpia la copia a medias y
  se avisa como advertencia. Si la carpeta de una copia se borra a mano,
  *Ver ficheros* lo detecta y quita la referencia.

### Probado (Xvfb, Python 3.12)

Migración del `config.json` real (formato 1 → 3, 44 entradas de historial);
filtros de tamaño y texto; muestra de 7 al azar y del 50 %; el ejemplo
path3, path1, path2, path1, path1, path2 guardando 3 (quedan exactamente 3
copias en disco, las de la última extracción de cada conjunto); bajar y subir
los dos contadores; tope de guardados por *Recordar*; carpeta ajena sin
marcador intacta; ventana de contenido; copia borrada a mano; almacén dentro
de un origen; almacén imposible de crear; validación de la ventana de filtros;
sincronización de la global en 13 casos, incluido `.c` → `.cs` rápido; línea
vacía extrayendo ficheros sin extensión; 13 líneas y 16 favoritos con los tres
scrolls y *Extraer* visible; rueda sobre una fila; ayuda emergente; cambio de
tema en caliente en las dos direcciones; modo *Sistema* siguiendo a Windows
(simulado) y dejando de seguirlo al forzar un tema; arranque directo en oscuro.

### No probado (hace falta Windows)

`os.startfile`, la lectura real de `winreg`, la barra de título con
`DwmSetWindowAttribute`, la rueda con un ratón físico y el aspecto con la
fuente Segoe UI de verdad.

### Pendiente / posibles mejoras

- Sigue sin haber botón de cancelar durante la copia.
- El historial no se puede filtrar ni exportar.
- `_buscar()` corre en el hilo de la interfaz, antes de lanzar el hilo de
  copia. Con árboles muy grandes la ventana se queda congelada mientras busca.
- Las copias guardadas no se pueden restaurar al destino; solo verlas y abrir
  su carpeta. Se descartó a propósito, pero sería fácil de añadir con el
  marcador que ya existe.
