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
