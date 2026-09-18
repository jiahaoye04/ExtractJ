#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ExtraerFicheros
===============

Copia de forma recursiva los ficheros de una o varias carpetas de origen a una
unica carpeta destino plana (sin estructura de subcarpetas). Cada carpeta de
origen lleva su propio juego de extensiones, y se puede filtrar por nombre.

Solo usa la biblioteca estandar de Python (tkinter incluido).
"""

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog, ttk

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

TITULO = "Extraer Ficheros"
FICHERO_CONFIG = "config.json"
VERSION_CONFIG = 2

MAX_HISTORIAL = 200
TOPE_RECIENTES = 10          # maximo que admite el contador de la interfaz
RECIENTES_POR_DEFECTO = 3

# La ventana se ajusta al contenido hasta este porcentaje del alto de pantalla.
FRACCION_ALTO_MAX = 0.80
ANCHO_INICIAL = 780
ALTO_MINIMO = 420

# Filas visibles como maximo en cada panel antes de que aparezca su scroll.
FILAS_MAX_ORIGEN = 6
FILAS_MAX_FAVORITOS = 8
ALTO_MINIMO_PANEL = 34

PREFIJO_CARPETA = "Copia"
NOMBRE_MIXTO = PREFIJO_CARPETA + "MIXTO"

COLOR_FONDO = "#f4f4f4"
COLOR_ESTRELLA_ON = "#e8a800"
COLOR_ESTRELLA_OFF = "#9a9a9a"
COLOR_SUAVE = "#666666"

# Modos del filtro de nombre. La clave es lo que se guarda en config.json.
MODOS_FILTRO = [
    ("contiene", "Contiene"),
    ("empieza", "Empieza por"),
    ("termina", "Termina por"),
]

# Lista blanca de extensiones admitidas. Si la extension escrita no esta aqui,
# se considera invalida y no se lanza la extraccion.
EXTENSIONES_VALIDAS = {
    # Codigo fuente
    ".java", ".py", ".pyw", ".c", ".h", ".cpp", ".cc", ".hpp", ".cs", ".go",
    ".rs", ".rb", ".php", ".pl", ".lua", ".swift", ".kt", ".kts", ".scala",
    ".groovy", ".dart", ".r", ".m", ".vb", ".pas", ".asm", ".sql", ".ps1",
    ".sh", ".bat", ".cmd", ".js", ".jsx", ".ts", ".tsx", ".vue", ".css",
    ".scss", ".sass", ".less", ".html", ".htm", ".jsp", ".asp", ".aspx",
    # Datos y configuracion
    ".json", ".xml", ".yaml", ".yml", ".ini", ".cfg", ".conf", ".properties",
    ".toml", ".env", ".csv", ".tsv", ".log", ".md", ".rst", ".txt",
    # Documentos
    ".pdf", ".doc", ".docx", ".odt", ".rtf", ".xls", ".xlsx", ".ods",
    ".ppt", ".pptx", ".odp", ".epub", ".tex",
    # Imagenes
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tif",
    ".tiff", ".psd", ".ai",
    # Audio y video
    ".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".mp4", ".avi", ".mkv",
    ".mov", ".wmv", ".webm",
    # Comprimidos y binarios
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".jar",
    ".war", ".ear", ".dll", ".exe", ".so", ".bin", ".class", ".o", ".a",
    ".db", ".sqlite", ".bak",
    # Fuentes tipograficas
    ".ttf", ".otf", ".woff", ".woff2",
}


# ---------------------------------------------------------------------------
# Utilidades generales
# ---------------------------------------------------------------------------

def directorio_programa():
    """Devuelve la carpeta donde reside el programa (compatible con PyInstaller)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def normalizar_extension(texto):
    """Pasa 'java', '.JAVA', ' *.java ' a '.java'. Devuelve '' si no hay nada."""
    ext = (texto or "").strip().lower()
    if not ext:
        return ""
    if ext.startswith("*"):
        ext = ext[1:]
    if not ext.startswith("."):
        ext = "." + ext
    return ext


def trocear_extensiones(texto):
    """Parte '.java, .jsp css' en piezas sueltas, sin normalizar todavia."""
    bruto = (texto or "").replace(",", " ").replace(";", " ")
    return [pieza for pieza in bruto.split() if pieza]


def parsear_extensiones(texto):
    """Devuelve (lista_valida, lista_invalida) a partir de un campo de texto.

    La lista valida va normalizada, en minusculas y sin repetidos, conservando
    el orden en que se escribieron. La invalida guarda el texto tal cual lo
    escribio el usuario, para poder decirle exactamente que pieza falla.
    """
    validas = []
    invalidas = []
    for pieza in trocear_extensiones(texto):
        ext = normalizar_extension(pieza)
        if ext and ext in EXTENSIONES_VALIDAS:
            if ext not in validas:
                validas.append(ext)
        else:
            invalidas.append(pieza)
    return validas, invalidas


def formatear_extensiones(extensiones):
    """['.java', '.jsp'] -> '.java .jsp'."""
    return " ".join(extensiones)


def nombre_carpeta_destino(extensiones):
    """Una sola extension da 'CopiaJAVA'; varias dan 'CopiaMIXTO'."""
    unicas = sorted(set(extensiones))
    if len(unicas) == 1:
        return PREFIJO_CARPETA + unicas[0].lstrip(".").upper()
    return NOMBRE_MIXTO


def acortar(ruta, maximo=58):
    """Recorta una ruta larga por el centro para que quepa en la interfaz."""
    if len(ruta) <= maximo:
        return ruta
    mitad = (maximo - 3) // 2
    return ruta[:mitad] + "..." + ruta[-mitad:]


def coincide_filtro(nombre_fichero, inclusion, modo, exclusion):
    """Decide si un fichero pasa el filtro de nombre.

    Se compara siempre contra el nombre SIN extension, que es lo que hace util
    el modo 'termina por': 'holacocina.java' termina por 'cocina'.
    Todo se compara en minusculas.
    """
    base = os.path.splitext(nombre_fichero)[0].lower()

    if exclusion and exclusion in base:
        return False
    if not inclusion:
        return True
    if modo == "empieza":
        return base.startswith(inclusion)
    if modo == "termina":
        return base.endswith(inclusion)
    return inclusion in base


def abrir_carpeta(ruta):
    """Abre una carpeta en el explorador del sistema. Devuelve True si va bien.

    En Windows basta con os.startfile, que es biblioteca estandar. Los otros
    dos casos estan por si algun dia esto se ejecuta fuera de Windows.
    """
    if not ruta or not os.path.isdir(ruta):
        return False
    try:
        if hasattr(os, "startfile"):          # Windows
            os.startfile(ruta)                # noqa: S606
        elif sys.platform == "darwin":        # macOS
            subprocess.Popen(["open", ruta])
        else:                                 # Linux y similares
            subprocess.Popen(["xdg-open", ruta])
        return True
    except (OSError, ValueError):
        return False


def normalizar_ruta(ruta):
    return os.path.normcase(os.path.normpath(ruta))


def clave_rutas(rutas):
    """Identidad de un grupo: el CONJUNTO de rutas, sin mirar extensiones.

    Es lo que decide si guardar un favorito es una alta o una sobrescritura.
    """
    return frozenset(normalizar_ruta(r["ruta"]) for r in rutas if r.get("ruta"))


def clave_completa(rutas):
    """Identidad estricta: rutas Y extensiones. Decide si la estrella brilla."""
    piezas = []
    for entrada in rutas:
        if not entrada.get("ruta"):
            continue
        piezas.append((normalizar_ruta(entrada["ruta"]),
                       tuple(sorted(entrada.get("extensiones", [])))))
    return frozenset(piezas)


def resumen_rutas(rutas, maximo=52):
    """'C:\\...\\chift (+2)' para mostrar un grupo en una sola linea."""
    if not rutas:
        return "(sin rutas)"
    texto = acortar(rutas[0].get("ruta", ""), maximo)
    if len(rutas) > 1:
        texto += "  (+%d)" % (len(rutas) - 1)
    return texto


def resumen_extensiones(rutas):
    """Todas las extensiones de un grupo, sin repetir."""
    todas = []
    for entrada in rutas:
        for ext in entrada.get("extensiones", []):
            if ext not in todas:
                todas.append(ext)
    return formatear_extensiones(sorted(todas))


# ---------------------------------------------------------------------------
# Configuracion persistente
# ---------------------------------------------------------------------------

class Configuracion:
    """Lectura y escritura del config.json situado junto al programa.

    Formato 2: favoritos y recientes son GRUPOS.
        favorito  = {"nombre": str, "rutas": [{"ruta": str, "extensiones": []}]}
        reciente  = {"rutas": [...]}
    El formato 1 (una entrada = una ruta + una extension) se migra al cargar.
    """

    def __init__(self):
        self.ruta = os.path.join(directorio_programa(), FICHERO_CONFIG)
        self.extension = ""
        self.destino = directorio_programa()
        self.abrir_al_terminar = True
        self.max_recientes = RECIENTES_POR_DEFECTO
        self.sustituir_al_cargar = False     # False = anadir por encima
        self.filtro_modo = "contiene"
        self.favoritos = []
        self.recientes = []
        self.historial = []
        self.cargar()

    # -- persistencia -------------------------------------------------------

    def cargar(self):
        try:
            with open(self.ruta, "r", encoding="utf-8") as fichero:
                datos = json.load(fichero)
        except (OSError, ValueError):
            return

        self.extension = normalizar_extension(datos.get("extension", ""))
        self.destino = datos.get("destino", self.destino) or self.destino
        self.abrir_al_terminar = bool(datos.get("abrir_al_terminar", True))
        self.sustituir_al_cargar = bool(datos.get("sustituir_al_cargar", False))

        modo = datos.get("filtro_modo", "contiene")
        if modo in dict(MODOS_FILTRO):
            self.filtro_modo = modo

        try:
            tope = int(datos.get("max_recientes", RECIENTES_POR_DEFECTO))
        except (TypeError, ValueError):
            tope = RECIENTES_POR_DEFECTO
        self.max_recientes = max(1, min(tope, TOPE_RECIENTES))

        ext_defecto = self.extension or ".java"
        self.favoritos = self._migrar_grupos(datos.get("favoritos", []),
                                             ext_defecto, con_nombre=True)
        self.recientes = self._migrar_grupos(datos.get("recientes", []),
                                             ext_defecto, con_nombre=False)
        self.historial = [h for h in datos.get("historial", []) if isinstance(h, dict)]

        self._fusionar_favoritos_repetidos()
        del self.recientes[self.max_recientes:]
        del self.historial[MAX_HISTORIAL:]

    def guardar(self):
        datos = {
            "version": VERSION_CONFIG,
            "extension": self.extension,
            "destino": self.destino,
            "abrir_al_terminar": self.abrir_al_terminar,
            "sustituir_al_cargar": self.sustituir_al_cargar,
            "max_recientes": self.max_recientes,
            "filtro_modo": self.filtro_modo,
            "favoritos": self.favoritos,
            "recientes": self.recientes,
            "historial": self.historial,
        }
        try:
            with open(self.ruta, "w", encoding="utf-8") as fichero:
                json.dump(datos, fichero, indent=2, ensure_ascii=False)
        except OSError as error:
            messagebox.showwarning(
                TITULO,
                "No se ha podido guardar la configuracion:\n%s" % error,
            )

    # -- migracion de formatos ---------------------------------------------

    @staticmethod
    def _migrar_grupos(bruto, extension_defecto, con_nombre):
        """Acepta los tres formatos historicos y los deja como grupos.

        1. Cadena suelta con la ruta (lo mas viejo de todo).
        2. Dict con ruta + extension (formato 1).
        3. Dict con nombre + rutas (formato 2, el actual).
        """
        grupos = []
        for elemento in bruto:
            if isinstance(elemento, str):
                if not elemento:
                    continue
                grupo = {"rutas": [{"ruta": elemento,
                                    "extensiones": [extension_defecto]}]}
                if con_nombre:
                    grupo["nombre"] = elemento
                grupos.append(grupo)

            elif isinstance(elemento, dict) and isinstance(elemento.get("rutas"), list):
                rutas = []
                for entrada in elemento["rutas"]:
                    if not isinstance(entrada, dict) or not entrada.get("ruta"):
                        continue
                    exts, _ = parsear_extensiones(
                        formatear_extensiones(entrada.get("extensiones") or []))
                    rutas.append({"ruta": entrada["ruta"], "extensiones": exts})
                if not rutas:
                    continue
                grupo = {"rutas": rutas}
                if con_nombre:
                    grupo["nombre"] = elemento.get("nombre") or resumen_rutas(rutas)
                grupos.append(grupo)

            elif isinstance(elemento, dict) and elemento.get("ruta"):
                ext = normalizar_extension(elemento.get("extension", extension_defecto)) \
                    or extension_defecto
                grupo = {"rutas": [{"ruta": elemento["ruta"], "extensiones": [ext]}]}
                if con_nombre:
                    grupo["nombre"] = elemento.get("nombre") or elemento["ruta"]
                grupos.append(grupo)

        return grupos

    def _fusionar_favoritos_repetidos(self):
        """Tras migrar del formato 1 puede haber varios favoritos con la misma
        ruta (uno por extension). Se unen en uno solo, sumando extensiones y
        conservando el nombre del primero."""
        fusionados = []
        indice = {}
        for grupo in self.favoritos:
            clave = clave_rutas(grupo["rutas"])
            if not clave:
                continue
            if clave in indice:
                destino = indice[clave]
                for entrada in grupo["rutas"]:
                    gemela = next(
                        (r for r in destino["rutas"]
                         if normalizar_ruta(r["ruta"]) == normalizar_ruta(entrada["ruta"])),
                        None)
                    if gemela is None:
                        destino["rutas"].append(entrada)
                    else:
                        for ext in entrada.get("extensiones", []):
                            if ext not in gemela["extensiones"]:
                                gemela["extensiones"].append(ext)
            else:
                indice[clave] = grupo
                fusionados.append(grupo)
        self.favoritos = fusionados

    # -- favoritos ----------------------------------------------------------
    #
    # La identidad de un favorito es el CONJUNTO DE RUTAS. Guardar un grupo
    # cuyas rutas ya existen sobrescribe el viejo por completo: las extensiones
    # pasan a ser las nuevas, no se acumulan. Una ruta de mas o de menos ya es
    # otro favorito distinto.

    def buscar_favorito(self, rutas):
        clave = clave_rutas(rutas)
        for grupo in self.favoritos:
            if clave_rutas(grupo["rutas"]) == clave:
                return grupo
        return None

    def es_favorito_exacto(self, rutas):
        """True solo si coinciden rutas Y extensiones. Es lo que enciende la
        estrella: un favorito con otras extensiones no cuenta."""
        clave = clave_completa(rutas)
        if not clave:
            return False
        return any(clave_completa(g["rutas"]) == clave for g in self.favoritos)

    def guardar_favorito(self, rutas, nombre):
        """Alta o sobrescritura. Devuelve el grupo guardado."""
        clave = clave_rutas(rutas)
        copia = [{"ruta": r["ruta"], "extensiones": list(r["extensiones"])}
                 for r in rutas]
        nuevo = {"nombre": nombre, "rutas": copia}

        for indice, grupo in enumerate(self.favoritos):
            if clave_rutas(grupo["rutas"]) == clave:
                self.favoritos[indice] = nuevo   # el viejo desaparece entero
                return nuevo

        self.favoritos.append(nuevo)
        return nuevo

    def quitar_favorito(self, rutas):
        clave = clave_rutas(rutas)
        self.favoritos = [g for g in self.favoritos
                          if clave_rutas(g["rutas"]) != clave]

    def renombrar_favorito(self, rutas, nombre):
        grupo = self.buscar_favorito(rutas)
        if grupo is not None:
            grupo["nombre"] = nombre or resumen_rutas(grupo["rutas"])

    # -- recientes ----------------------------------------------------------

    def anadir_reciente(self, rutas):
        """Un reciente por extraccion. Se compara con rutas y extensiones, para
        que repetir la misma extraccion no genere dos filas."""
        clave = clave_completa(rutas)
        copia = [{"ruta": r["ruta"], "extensiones": list(r["extensiones"])}
                 for r in rutas]
        self.recientes = [g for g in self.recientes
                          if clave_completa(g["rutas"]) != clave]
        self.recientes.insert(0, {"rutas": copia})
        del self.recientes[self.max_recientes:]

    def recortar_recientes(self):
        del self.recientes[self.max_recientes:]

    # -- historial ----------------------------------------------------------

    def anadir_historial(self, extensiones, total, rutas, destino):
        ahora = datetime.now()
        origenes = [r["ruta"] for r in rutas]
        self.historial.insert(0, {
            "fecha": ahora.strftime("%d/%m/%Y"),
            "hora": ahora.strftime("%H:%M:%S"),
            "extension": formatear_extensiones(sorted(set(extensiones))),
            "total": total,
            "origen": origenes[0] if origenes else "",
            "origenes": origenes,
            "destino": destino,
        })
        del self.historial[MAX_HISTORIAL:]


# ---------------------------------------------------------------------------
# Panel con barra de desplazamiento propia
# ---------------------------------------------------------------------------

class PanelDesplazable(ttk.Frame):
    """Lienzo + marco interior + barra que solo aparece cuando hace falta.

    Cuidado al tocar esto: los manejadores de <Configure> NO pueden mostrar ni
    ocultar la barra. Hacerlo cambia el ancho del lienzo, lo que dispara otro
    <Configure>, y se entra en un bucle infinito de eventos que cuelga la
    aplicacion dentro de update_idletasks(). Por eso la visibilidad de la barra
    se decide siempre con retardo real (after) y cancelando la tarea anterior.
    """

    def __init__(self, padre, color_fondo, **kwargs):
        super().__init__(padre, **kwargs)

        self.lienzo = tk.Canvas(self, bg=color_fondo, highlightthickness=0,
                                bd=0, height=1)
        self.barra = ttk.Scrollbar(self, orient="vertical",
                                   command=self.lienzo.yview)
        self.lienzo.configure(yscrollcommand=self.barra.set)
        self.lienzo.pack(side="left", fill="both", expand=True)

        self.interior = ttk.Frame(self.lienzo)
        self._id_ventana = self.lienzo.create_window((0, 0), window=self.interior,
                                                     anchor="nw")

        self._barra_visible = False
        self._tarea = None

        self.lienzo.bind("<Configure>", self._al_redimensionar)
        self.interior.bind("<Configure>", lambda _e: self._region())
        self.lienzo.bind("<Enter>", self._activar_rueda)
        self.lienzo.bind("<Leave>", self._desactivar_rueda)

    # -- interno ------------------------------------------------------------

    def _al_redimensionar(self, evento):
        self.lienzo.itemconfigure(self._id_ventana, width=evento.width)
        self._region()
        self.programar_revision()

    def _region(self):
        self.lienzo.configure(scrollregion=self.lienzo.bbox("all"))

    def programar_revision(self):
        if self._tarea is not None:
            try:
                self.after_cancel(self._tarea)
            except tk.TclError:
                pass
        self._tarea = self.after(120, self._revisar_barra)

    def _revisar_barra(self):
        self._tarea = None
        self._region()
        hace_falta = self.alto_contenido() > self.lienzo.winfo_height() + 2

        if hace_falta and not self._barra_visible:
            self.barra.pack(side="right", fill="y")
            self._barra_visible = True
        elif not hace_falta and self._barra_visible:
            self.barra.pack_forget()
            self._barra_visible = False
            self.lienzo.yview_moveto(0)

    def _activar_rueda(self, _evento=None):
        self.lienzo.bind_all("<MouseWheel>", self._rueda)

    def _desactivar_rueda(self, _evento=None):
        self.lienzo.unbind_all("<MouseWheel>")

    def _rueda(self, evento):
        if self._barra_visible:
            self.lienzo.yview_scroll(-1 * (evento.delta // 120), "units")

    # -- uso desde fuera ----------------------------------------------------

    def alto_contenido(self):
        return max(self.interior.winfo_reqheight(), 1)

    def alto_fila(self, por_defecto=30):
        """Alto de la primera fila, para calcular cuantas caben."""
        hijos = self.interior.winfo_children()
        if not hijos:
            return por_defecto
        return max(hijos[0].winfo_reqheight(), 1)

    def fijar_alto(self, alto):
        self.lienzo.configure(height=max(int(alto), 1))

    def vaciar(self):
        for hijo in self.interior.winfo_children():
            hijo.destroy()

    @property
    def barra_visible(self):
        return self._barra_visible


# ---------------------------------------------------------------------------
# Ventana de historial
# ---------------------------------------------------------------------------

class VentanaHistorial(tk.Toplevel):

    def __init__(self, padre, config):
        super().__init__(padre)
        self.config_app = config

        self.title(TITULO + " - Historial")
        self.geometry("900x420")
        self.minsize(640, 300)
        self.transient(padre)

        marco = ttk.Frame(self, padding=10)
        marco.pack(fill="both", expand=True)

        columnas = ("fecha", "hora", "tipo", "total", "origen", "destino")
        self.tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=14)

        cabeceras = {
            "fecha": ("Fecha", 90, "center"),
            "hora": ("Hora", 80, "center"),
            "tipo": ("Tipo", 110, "center"),
            "total": ("Ficheros", 70, "center"),
            "origen": ("Origen", 280, "w"),
            "destino": ("Destino", 250, "w"),
        }
        for clave, (texto, ancho, alineacion) in cabeceras.items():
            self.tabla.heading(clave, text=texto)
            self.tabla.column(clave, width=ancho, anchor=alineacion)

        barra = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)

        self.tabla.pack(side="top", fill="both", expand=True)
        barra.place(relx=1.0, rely=0.0, relheight=0.88, anchor="ne")

        pie = ttk.Frame(marco)
        pie.pack(fill="x", pady=(10, 0))

        self.etiqueta_total = ttk.Label(pie, text="")
        self.etiqueta_total.pack(side="left")

        ttk.Button(pie, text="Cerrar", command=self.destroy).pack(side="right")
        ttk.Button(pie, text="Vaciar historial",
                   command=self.vaciar).pack(side="right", padx=(0, 6))

        self.rellenar()

    def rellenar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        for entrada in self.config_app.historial:
            origenes = entrada.get("origenes") or [entrada.get("origen", "")]
            origen = acortar(origenes[0], 44)
            if len(origenes) > 1:
                origen += "  (+%d)" % (len(origenes) - 1)

            self.tabla.insert("", "end", values=(
                entrada.get("fecha", ""),
                entrada.get("hora", ""),
                entrada.get("extension", ""),
                entrada.get("total", 0),
                origen,
                entrada.get("destino", ""),
            ))

        total = len(self.config_app.historial)
        if total == 0:
            self.etiqueta_total.config(text="No hay extracciones registradas.")
        elif total == 1:
            self.etiqueta_total.config(text="1 extraccion registrada.")
        else:
            self.etiqueta_total.config(text="%d extracciones registradas." % total)

    def vaciar(self):
        if not self.config_app.historial:
            return
        if not messagebox.askyesno(
            TITULO,
            "Se va a borrar todo el historial. Esta accion no se puede deshacer.\n\n"
            "Continuar?",
            parent=self,
        ):
            return
        self.config_app.historial = []
        self.config_app.guardar()
        self.rellenar()


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------

class Aplicacion(tk.Tk):

    def __init__(self):
        super().__init__()

        self.config_app = Configuracion()
        self.cola = queue.Queue()
        self.hilo = None

        # Cada linea de origen es un dict con sus dos StringVar y su marco.
        self.lineas = []

        self.title(TITULO)
        self.minsize(700, ALTO_MINIMO)
        self.configure(bg=COLOR_FONDO)

        self.var_extension = tk.StringVar(value=self.config_app.extension)
        self.var_destino = tk.StringVar(value=self.config_app.destino)
        self.var_estado = tk.StringVar(value="Listo.")
        self.var_contador = tk.StringVar(value="")
        self.var_abrir = tk.BooleanVar(value=self.config_app.abrir_al_terminar)
        self.var_sustituir = tk.BooleanVar(value=self.config_app.sustituir_al_cargar)
        self.var_incluir = tk.StringVar()
        self.var_excluir = tk.StringVar()
        self.var_modo_filtro = tk.StringVar(
            value=dict(MODOS_FILTRO)[self.config_app.filtro_modo])
        self.var_busqueda_fav = tk.StringVar()
        self.var_max_recientes = tk.StringVar(value=str(self.config_app.max_recientes))

        self._construir_interfaz()
        self._anadir_linea()
        self._refrescar_favoritos()
        self._refrescar_recientes()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

    # -- construccion de la interfaz ---------------------------------------

    def _construir_interfaz(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        self.color_marco = estilo.lookup("TFrame", "background") or COLOR_FONDO

        raiz = ttk.Frame(self, padding=12)
        raiz.pack(fill="both", expand=True)
        self.marco_raiz = raiz

        # El bloque inferior se empaqueta ANTES que el central: asi pack le
        # reserva su sitio y el boton Extraer nunca queda tapado por muchas
        # lineas, favoritos o recientes que haya.
        superior = ttk.Frame(raiz)
        superior.pack(side="top", fill="x")
        superior.columnconfigure(0, weight=1)

        inferior = ttk.Frame(raiz)
        inferior.pack(side="bottom", fill="x", pady=(10, 0))
        inferior.columnconfigure(0, weight=1)

        medio = ttk.Frame(raiz)
        medio.pack(side="top", fill="both", expand=True)
        medio.columnconfigure(0, weight=1)

        self._construir_cabecera(superior)
        self._construir_filtro(superior)
        self._construir_medio(medio)
        self._construir_inferior(inferior)

    def _construir_cabecera(self, padre):
        cabecera = ttk.Frame(padre)
        cabecera.grid(row=0, column=0, sticky="ew")
        cabecera.columnconfigure(0, weight=1)

        ttk.Label(cabecera, text=TITULO,
                  font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Button(cabecera, text="Historial",
                   command=self._abrir_historial).grid(row=0, column=1, sticky="e")

        ttk.Separator(padre).grid(row=1, column=0, sticky="ew", pady=10)

        marco_ext = ttk.Frame(padre)
        marco_ext.grid(row=2, column=0, sticky="ew")
        ttk.Label(marco_ext, text="Extension global:").pack(side="left")
        ttk.Entry(marco_ext, textvariable=self.var_extension,
                  width=18).pack(side="left", padx=(8, 8))
        ttk.Label(marco_ext,
                  text="se suma a la de cada linea; vacia no aporta nada",
                  foreground=COLOR_SUAVE).pack(side="left")

    def _construir_filtro(self, padre):
        ttk.Label(padre, text="Filtro por nombre",
                  font=("Segoe UI", 10, "bold")).grid(row=3, column=0,
                                                      sticky="w", pady=(14, 4))

        marco = ttk.Frame(padre)
        marco.grid(row=4, column=0, sticky="ew")
        marco.columnconfigure(1, weight=1)
        marco.columnconfigure(3, weight=1)

        self.combo_modo = ttk.Combobox(
            marco, textvariable=self.var_modo_filtro, state="readonly",
            values=[texto for _, texto in MODOS_FILTRO], width=12)
        self.combo_modo.grid(row=0, column=0)

        ttk.Entry(marco, textvariable=self.var_incluir).grid(
            row=0, column=1, sticky="ew", padx=(6, 12))

        ttk.Label(marco, text="Excluir:").grid(row=0, column=2)
        ttk.Entry(marco, textvariable=self.var_excluir).grid(
            row=0, column=3, sticky="ew", padx=(6, 0))

        ttk.Label(padre,
                  text="Se compara con el nombre sin extension y sin distinguir "
                       "mayusculas. Vacio, no filtra.",
                  foreground=COLOR_SUAVE).grid(row=5, column=0, sticky="w",
                                               pady=(4, 0))

    def _construir_medio(self, padre):
        # --- Carpetas de origen --------------------------------------------
        titulo_origen = ttk.Frame(padre)
        titulo_origen.pack(fill="x", pady=(12, 4))

        ttk.Label(titulo_origen, text="Carpetas de origen",
                  font=("Segoe UI", 10, "bold")).pack(side="left")

        self.boton_favorito = ttk.Button(titulo_origen, text="\u2606 Guardar como favorito",
                                         command=self._alternar_favorito_actual)
        self.boton_favorito.pack(side="right")
        ttk.Button(titulo_origen, text="Limpiar",
                   command=self._limpiar_lineas).pack(side="right", padx=(0, 6))
        ttk.Button(titulo_origen, text="+ Anadir linea",
                   command=self._anadir_linea).pack(side="right", padx=(0, 6))

        self.panel_origen = PanelDesplazable(padre, self.color_marco)
        self.panel_origen.pack(fill="x")

        ttk.Label(padre,
                  text="Extensiones de cada linea separadas por espacios; "
                       "por ejemplo: .java .jsp .css",
                  foreground=COLOR_SUAVE).pack(anchor="w", pady=(4, 0))

        # --- Favoritos ------------------------------------------------------
        titulo_fav = ttk.Frame(padre)
        titulo_fav.pack(fill="x", pady=(12, 4))

        ttk.Label(titulo_fav, text="Favoritos",
                  font=("Segoe UI", 10, "bold")).pack(side="left")

        ttk.Checkbutton(titulo_fav, text="Sustituir las lineas al cargar",
                        variable=self.var_sustituir,
                        command=self._cambiar_modo_carga).pack(side="right")

        self.entrada_busqueda = ttk.Entry(titulo_fav, textvariable=self.var_busqueda_fav,
                                          width=18)
        self.entrada_busqueda.pack(side="right", padx=(0, 10))
        ttk.Label(titulo_fav, text="Buscar:").pack(side="right", padx=(0, 4))
        self.var_busqueda_fav.trace_add("write",
                                        lambda *_: self._refrescar_favoritos())

        self.panel_favoritos = PanelDesplazable(padre, self.color_marco)
        self.panel_favoritos.pack(fill="x")

        # --- Recientes ------------------------------------------------------
        titulo_rec = ttk.Frame(padre)
        titulo_rec.pack(fill="x", pady=(12, 4))

        ttk.Label(titulo_rec, text="Recientes",
                  font=("Segoe UI", 10, "bold")).pack(side="left")

        ttk.Spinbox(titulo_rec, from_=1, to=TOPE_RECIENTES, width=4,
                    textvariable=self.var_max_recientes, state="readonly",
                    command=self._cambiar_max_recientes).pack(side="right")
        ttk.Label(titulo_rec, text="Filas a mostrar:",
                  foreground=COLOR_SUAVE).pack(side="right", padx=(0, 6))

        self.panel_recientes = PanelDesplazable(padre, self.color_marco)
        self.panel_recientes.pack(fill="x")

    def _construir_inferior(self, padre):
        ttk.Label(padre, text="Carpeta de destino",
                  font=("Segoe UI", 10, "bold")).grid(row=0, column=0,
                                                      sticky="w", pady=(6, 4))

        marco_destino = ttk.Frame(padre)
        marco_destino.grid(row=1, column=0, sticky="ew")
        marco_destino.columnconfigure(0, weight=1)

        ttk.Entry(marco_destino,
                  textvariable=self.var_destino).grid(row=0, column=0, sticky="ew")
        ttk.Button(marco_destino, text="Examinar...",
                   command=self._elegir_destino).grid(row=0, column=1, padx=(6, 0))

        self.etiqueta_destino_final = ttk.Label(padre, text="",
                                                foreground=COLOR_SUAVE)
        self.etiqueta_destino_final.grid(row=2, column=0, sticky="w", pady=(4, 0))
        # La extension global entra en el calculo de la estrella, no solo en el
        # del nombre del destino: cambiarla cambia las extensiones efectivas.
        self.var_extension.trace_add("write", lambda *_: self._refrescar_estrella())
        self.var_destino.trace_add("write", lambda *_: self._refrescar_destino_final())

        ttk.Checkbutton(padre, text="Abrir la carpeta al terminar",
                        variable=self.var_abrir,
                        command=self._cambiar_abrir).grid(row=3, column=0,
                                                          sticky="w", pady=(6, 0))

        marco_progreso = ttk.Frame(padre)
        marco_progreso.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        marco_progreso.columnconfigure(0, weight=1)

        self.barra = ttk.Progressbar(marco_progreso, mode="determinate", maximum=100)
        self.barra.grid(row=0, column=0, sticky="ew")
        ttk.Label(marco_progreso, textvariable=self.var_contador,
                  width=12, anchor="e").grid(row=0, column=1, padx=(8, 0))

        ttk.Label(padre, textvariable=self.var_estado,
                  foreground="#444444").grid(row=5, column=0, sticky="w", pady=(6, 0))

        self.boton_extraer = ttk.Button(padre, text="Extraer ficheros",
                                        command=self._iniciar_extraccion)
        self.boton_extraer.grid(row=6, column=0, sticky="ew", pady=(12, 0))

    # -- altura de la ventana -----------------------------------------------

    def _ajustar_altura(self):
        """Ajusta el alto de la ventana al contenido, con tope y scroll.

        Cada panel pide lo que ocupa su contenido, limitado por su maximo de
        filas. Si aun asi la ventana entera se pasa del tope de pantalla, se
        va recortando panel por panel en orden de prioridad hasta que quepa.
        """
        self.update_idletasks()

        paneles = [
            (self.panel_origen, FILAS_MAX_ORIGEN),
            (self.panel_favoritos, FILAS_MAX_FAVORITOS),
            (self.panel_recientes, self.config_app.max_recientes),
        ]

        altos = {}
        for panel, filas_max in paneles:
            tope = panel.alto_fila() * max(filas_max, 1) + 4
            altos[panel] = max(min(panel.alto_contenido(), tope), ALTO_MINIMO_PANEL)
            panel.fijar_alto(altos[panel])

        self.update_idletasks()
        alto_max = int(self.winfo_screenheight() * FRACCION_ALTO_MAX)
        alto_pedido = self.winfo_reqheight()

        # Se recorta primero favoritos, luego recientes y por ultimo origen:
        # las lineas de origen son lo que el usuario esta editando ahora.
        if alto_pedido > alto_max:
            orden = [self.panel_favoritos, self.panel_recientes, self.panel_origen]
            for panel in orden:
                if alto_pedido <= alto_max:
                    break
                sobra = alto_pedido - alto_max
                nuevo = max(altos[panel] - sobra, ALTO_MINIMO_PANEL)
                if nuevo == altos[panel]:
                    continue
                altos[panel] = nuevo
                panel.fijar_alto(nuevo)
                self.update_idletasks()
                alto_pedido = self.winfo_reqheight()

        alto = max(min(alto_pedido, alto_max), ALTO_MINIMO)
        ancho = self.winfo_width() if self.winfo_ismapped() else ANCHO_INICIAL
        ancho = max(ancho, ANCHO_INICIAL)
        self.geometry("%dx%d" % (ancho, alto))

        for panel, _ in paneles:
            panel.programar_revision()

    # -- lineas de origen ---------------------------------------------------

    def _anadir_linea(self, ruta="", extensiones=None):
        """Anade una fila de origen. Devuelve el dict de la linea."""
        var_ruta = tk.StringVar(value=ruta)
        var_ext = tk.StringVar(value=formatear_extensiones(extensiones or []))

        fila = ttk.Frame(self.panel_origen.interior)
        fila.pack(fill="x", pady=1)

        entrada_ruta = ttk.Entry(fila, textvariable=var_ruta)
        entrada_ruta.pack(side="left", fill="x", expand=True)

        entrada_ext = ttk.Entry(fila, textvariable=var_ext, width=22)
        entrada_ext.pack(side="left", padx=(6, 0))

        linea = {"marco": fila, "ruta": var_ruta, "extensiones": var_ext}

        ttk.Button(fila, text="...", width=3,
                   command=lambda l=linea: self._elegir_origen(l)).pack(
                       side="left", padx=(6, 0))
        ttk.Button(fila, text="\u00d7", width=3,
                   command=lambda l=linea: self._quitar_linea(l)).pack(
                       side="left", padx=(4, 0))

        var_ruta.trace_add("write", lambda *_: self._refrescar_estrella())
        var_ext.trace_add("write", lambda *_: self._refrescar_estrella())

        self.lineas.append(linea)
        self._refrescar_estrella()
        self._ajustar_altura()
        return linea

    def _quitar_linea(self, linea):
        if linea not in self.lineas:
            return
        self.lineas.remove(linea)
        linea["marco"].destroy()
        if not self.lineas:              # siempre queda al menos una linea
            self._anadir_linea()
        else:
            self._refrescar_estrella()
            self._ajustar_altura()

    def _limpiar_lineas(self):
        for linea in list(self.lineas):
            linea["marco"].destroy()
        self.lineas = []
        self._anadir_linea()

    def _lineas_vacias(self):
        """True si no hay nada escrito en ninguna linea."""
        return all(not linea["ruta"].get().strip() for linea in self.lineas)

    def _cargar_grupo(self, grupo):
        """Vuelca un favorito o reciente en las lineas de origen.

        Con el interruptor en 'sustituir' se borra lo que haya. En modo anadir
        (el de fabrica) se agregan las rutas que falten; si una ruta ya esta en
        pantalla se actualizan sus extensiones en vez de duplicar la linea.
        """
        if self.var_sustituir.get() or self._lineas_vacias():
            for linea in list(self.lineas):
                linea["marco"].destroy()
            self.lineas = []

        for entrada in grupo.get("rutas", []):
            ruta = entrada.get("ruta", "")
            exts = list(entrada.get("extensiones", []))
            gemela = next(
                (l for l in self.lineas
                 if l["ruta"].get().strip()
                 and normalizar_ruta(l["ruta"].get().strip()) == normalizar_ruta(ruta)),
                None)
            if gemela is None:
                self._anadir_linea(ruta, exts)
            else:
                gemela["extensiones"].set(formatear_extensiones(exts))

        if not self.lineas:
            self._anadir_linea()

        self._refrescar_estrella()
        self._ajustar_altura()

    def _rutas_actuales(self, solo_validas=True):
        """Las lineas escritas, como lista de grupos {ruta, extensiones}.

        Las extensiones invalidas se ignoran aqui: esto solo alimenta la
        estrella y el nombre del destino. La validacion de verdad, con su
        aviso, se hace al extraer.
        """
        rutas = []
        for linea in self.lineas:
            ruta = linea["ruta"].get().strip().strip('"')
            if solo_validas and not ruta:
                continue
            validas, _ = parsear_extensiones(linea["extensiones"].get())
            rutas.append({"ruta": os.path.normpath(ruta) if ruta else ruta,
                          "extensiones": self._con_global(validas)})
        return rutas

    def _con_global(self, extensiones):
        """Suma la extension global a las de una linea, sin repetir."""
        global_ext = normalizar_extension(self.var_extension.get())
        if not global_ext or global_ext not in EXTENSIONES_VALIDAS:
            return list(extensiones)
        if global_ext in extensiones:
            return list(extensiones)
        return list(extensiones) + [global_ext]

    # -- favoritos ----------------------------------------------------------

    def _refrescar_estrella(self):
        """La estrella del boton solo se enciende si rutas Y extensiones
        coinciden exactamente con un favorito guardado."""
        rutas = self._rutas_actuales()
        if rutas and self.config_app.es_favorito_exacto(rutas):
            self.boton_favorito.config(text="\u2605 En favoritos")
        else:
            self.boton_favorito.config(text="\u2606 Guardar como favorito")
        self._refrescar_destino_final()

    def _alternar_favorito_actual(self):
        rutas = self._rutas_actuales()
        if not rutas:
            messagebox.showinfo(TITULO, "Escribe o elige primero alguna carpeta de origen.")
            return
        if self.config_app.es_favorito_exacto(rutas):
            self.config_app.quitar_favorito(rutas)
            self.config_app.guardar()
            self._refrescar_favoritos()
            self._refrescar_recientes()
            self._refrescar_estrella()
            return
        self._guardar_como_favorito(rutas)

    def _guardar_como_favorito(self, rutas):
        """Alta o sobrescritura segun el conjunto de rutas.

        Si esas mismas rutas ya son favoritas, el viejo se elimina entero y el
        nuevo se queda con las extensiones actuales. El nombre viejo se ofrece
        como valor inicial, pero se puede cambiar.
        """
        for entrada in rutas:
            if not os.path.isdir(entrada["ruta"]):
                messagebox.showerror(TITULO,
                                     "Esta carpeta no existe:\n%s" % entrada["ruta"])
                return

        existente = self.config_app.buscar_favorito(rutas)
        if existente is not None:
            inicial = existente.get("nombre") or resumen_rutas(rutas)
            mensaje = ("Ya hay un favorito con esas mismas carpetas.\n"
                       "Se va a sustituir por el actual.\n\nNombre:")
        else:
            primera = rutas[0]["ruta"]
            inicial = os.path.basename(primera.rstrip("\\/")) or primera
            if len(rutas) > 1:
                inicial += " (+%d)" % (len(rutas) - 1)
            mensaje = "Nombre para este favorito:"

        nombre = simpledialog.askstring(TITULO, mensaje, initialvalue=inicial,
                                        parent=self)
        if nombre is None:
            return

        self.config_app.guardar_favorito(rutas, nombre.strip() or inicial)
        self.config_app.guardar()
        self._refrescar_favoritos()
        self._refrescar_recientes()
        self._refrescar_estrella()

    def _refrescar_favoritos(self):
        self.panel_favoritos.vaciar()

        busqueda = self.var_busqueda_fav.get().strip().lower()
        visibles = [g for g in self.config_app.favoritos
                    if not busqueda or busqueda in (g.get("nombre", "").lower())]

        if not visibles:
            texto = ("Ningun favorito coincide con la busqueda."
                     if busqueda else "Todavia no hay favoritos.")
            ttk.Label(self.panel_favoritos.interior, text=texto,
                      foreground=COLOR_SUAVE).pack(anchor="w", pady=2)
        else:
            for grupo in visibles:
                self._fila_favorito(grupo)

        self._ajustar_altura()

    def _fila_favorito(self, grupo):
        fila = ttk.Frame(self.panel_favoritos.interior)
        fila.pack(fill="x", pady=1)

        rutas = grupo["rutas"]

        ttk.Button(fila, text=grupo.get("nombre") or resumen_rutas(rutas),
                   width=22,
                   command=lambda g=grupo: self._cargar_grupo(g)).pack(side="left")

        ttk.Label(fila, text=resumen_extensiones(rutas), width=16, anchor="w",
                  foreground="#555555").pack(side="left", padx=(6, 4))

        ttk.Label(fila, text=resumen_rutas(rutas, 40), anchor="w",
                  foreground=COLOR_SUAVE).pack(side="left", fill="x", expand=True)

        ttk.Button(fila, text="Renombrar", width=10,
                   command=lambda g=grupo: self._renombrar_favorito(g)).pack(
                       side="left", padx=(6, 0))
        ttk.Button(fila, text="Quitar", width=7,
                   command=lambda g=grupo: self._quitar_favorito(g)).pack(
                       side="left", padx=(4, 0))

    def _renombrar_favorito(self, grupo):
        nombre = simpledialog.askstring(
            TITULO, "Nuevo nombre para este favorito:",
            initialvalue=grupo.get("nombre") or resumen_rutas(grupo["rutas"]),
            parent=self)
        if nombre is None:
            return
        self.config_app.renombrar_favorito(grupo["rutas"], nombre.strip())
        self.config_app.guardar()
        self._refrescar_favoritos()

    def _quitar_favorito(self, grupo):
        self.config_app.quitar_favorito(grupo["rutas"])
        self.config_app.guardar()
        self._refrescar_favoritos()
        self._refrescar_recientes()
        self._refrescar_estrella()

    # -- recientes ----------------------------------------------------------

    def _refrescar_recientes(self):
        self.panel_recientes.vaciar()

        if not self.config_app.recientes:
            ttk.Label(self.panel_recientes.interior,
                      text="Todavia no hay extracciones recientes.",
                      foreground=COLOR_SUAVE).pack(anchor="w", pady=2)
        else:
            for grupo in self.config_app.recientes:
                self._fila_reciente(grupo)

        self._ajustar_altura()

    def _fila_reciente(self, grupo):
        fila = ttk.Frame(self.panel_recientes.interior)
        fila.pack(fill="x", pady=1)

        rutas = grupo["rutas"]
        marcado = self.config_app.es_favorito_exacto(rutas)

        tk.Button(
            fila,
            text="\u2605" if marcado else "\u2606",
            fg=COLOR_ESTRELLA_ON if marcado else COLOR_ESTRELLA_OFF,
            font=("Segoe UI", 11),
            relief="flat", bd=0, cursor="hand2",
            bg=self.color_marco, activebackground=self.color_marco,
            command=lambda g=grupo: self._alternar_estrella_reciente(g),
        ).pack(side="left", padx=(0, 6))

        ttk.Label(fila, text=resumen_extensiones(rutas), width=16, anchor="w",
                  foreground="#555555").pack(side="left", padx=(0, 4))

        ttk.Button(fila, text=resumen_rutas(rutas, 56),
                   command=lambda g=grupo: self._cargar_grupo(g)).pack(
                       side="left", fill="x", expand=True)

    def _alternar_estrella_reciente(self, grupo):
        rutas = grupo["rutas"]
        if self.config_app.es_favorito_exacto(rutas):
            self.config_app.quitar_favorito(rutas)
            self.config_app.guardar()
            self._refrescar_favoritos()
            self._refrescar_recientes()
            self._refrescar_estrella()
        else:
            self._guardar_como_favorito(rutas)

    def _cambiar_max_recientes(self):
        try:
            valor = int(self.var_max_recientes.get())
        except (TypeError, ValueError):
            return
        self.config_app.max_recientes = max(1, min(valor, TOPE_RECIENTES))
        self.config_app.recortar_recientes()
        self.config_app.guardar()
        self._refrescar_recientes()

    # -- preferencias sueltas ----------------------------------------------

    def _cambiar_abrir(self):
        self.config_app.abrir_al_terminar = bool(self.var_abrir.get())
        self.config_app.guardar()

    def _cambiar_modo_carga(self):
        self.config_app.sustituir_al_cargar = bool(self.var_sustituir.get())
        self.config_app.guardar()

    def _modo_filtro_actual(self):
        texto = self.var_modo_filtro.get()
        for clave, etiqueta in MODOS_FILTRO:
            if etiqueta == texto:
                return clave
        return "contiene"

    # -- seleccion de carpetas ---------------------------------------------

    def _elegir_origen(self, linea):
        inicial = linea["ruta"].get().strip() or directorio_programa()
        ruta = filedialog.askdirectory(title="Selecciona la carpeta de origen",
                                       initialdir=inicial)
        if ruta:
            linea["ruta"].set(os.path.normpath(ruta))

    def _elegir_destino(self):
        inicial = self.var_destino.get().strip() or directorio_programa()
        ruta = filedialog.askdirectory(title="Selecciona la carpeta de destino",
                                       initialdir=inicial)
        if ruta:
            self.var_destino.set(os.path.normpath(ruta))
            self.config_app.destino = os.path.normpath(ruta)
            self.config_app.guardar()

    def _refrescar_destino_final(self):
        extensiones = []
        for entrada in self._rutas_actuales():
            extensiones.extend(entrada["extensiones"])

        base = self.var_destino.get().strip() or directorio_programa()
        if extensiones:
            carpeta = os.path.join(base, nombre_carpeta_destino(extensiones))
            self.etiqueta_destino_final.config(text="Se creara: " + acortar(carpeta, 70))
        else:
            self.etiqueta_destino_final.config(text="")

    def _abrir_historial(self):
        VentanaHistorial(self, self.config_app)

    # -- extraccion ---------------------------------------------------------

    def _recoger_lineas(self):
        """Valida las lineas y devuelve (rutas, error).

        Si error no es None, no se toca nada: se aborta la extraccion entera
        sin copiar un solo fichero, diciendo que linea y que texto falla.
        """
        global_ext = self.var_extension.get().strip()
        if global_ext:
            _, malas_globales = parsear_extensiones(global_ext)
            if malas_globales:
                return None, ("La extension global tiene un formato no valido: %s\n\n"
                              "Escribe extensiones conocidas, por ejemplo: .java .jsp"
                              % " ".join(malas_globales))

        recogidas = []
        for numero, linea in enumerate(self.lineas, start=1):
            ruta = linea["ruta"].get().strip().strip('"')
            texto_ext = linea["extensiones"].get().strip()

            if not ruta and not texto_ext:
                continue                          # linea vacia: se ignora
            if not ruta:
                return None, "La linea %d tiene extensiones pero no carpeta." % numero
            if not os.path.isdir(ruta):
                return None, "La carpeta de la linea %d no existe:\n%s" % (numero, ruta)

            validas, invalidas = parsear_extensiones(texto_ext)
            if invalidas:
                return None, ("Formato de extension no valido en la linea %d: %s\n\n"
                              "Separalas por espacios y usa extensiones conocidas, "
                              "por ejemplo: .java .jsp .css"
                              % (numero, " ".join(invalidas)))

            extensiones = self._con_global(validas)
            if not extensiones:
                return None, ("La linea %d no tiene ninguna extension.\n\n"
                              "Escribela en la linea o rellena la extension global."
                              % numero)

            recogidas.append({"ruta": os.path.normpath(ruta),
                              "extensiones": extensiones})

        if not recogidas:
            return None, "Indica al menos una carpeta de origen."

        # Misma carpeta en dos lineas: se fusionan en vez de recorrerla dos veces.
        fusionadas = []
        indice = {}
        for entrada in recogidas:
            clave = normalizar_ruta(entrada["ruta"])
            if clave in indice:
                destino = indice[clave]
                for ext in entrada["extensiones"]:
                    if ext not in destino["extensiones"]:
                        destino["extensiones"].append(ext)
            else:
                indice[clave] = entrada
                fusionadas.append(entrada)

        return fusionadas, None

    def _iniciar_extraccion(self):
        if self.hilo and self.hilo.is_alive():
            return

        rutas, error = self._recoger_lineas()
        if error:
            self.var_estado.set("Revisa los datos.")
            messagebox.showerror(TITULO, error)
            return

        base_destino = self.var_destino.get().strip().strip('"') or directorio_programa()
        if not os.path.isdir(base_destino):
            messagebox.showerror(TITULO,
                                 "La carpeta de destino no existe:\n%s" % base_destino)
            return

        base_destino = os.path.normpath(base_destino)
        todas_ext = []
        for entrada in rutas:
            todas_ext.extend(entrada["extensiones"])
        destino = os.path.join(base_destino, nombre_carpeta_destino(todas_ext))

        # El destino no puede estar dentro de ninguno de los origenes.
        for entrada in rutas:
            origen = normalizar_ruta(entrada["ruta"])
            if os.path.normcase(destino).startswith(origen + os.sep):
                messagebox.showerror(
                    TITULO,
                    "La carpeta de destino esta dentro de una de origen:\n\n%s\n\n"
                    "Elige otra ubicacion para evitar copiar sobre lo copiado."
                    % entrada["ruta"],
                )
                return

        inclusion = self.var_incluir.get().strip().lower()
        exclusion = self.var_excluir.get().strip().lower()
        modo = self._modo_filtro_actual()

        self.var_estado.set("Buscando ficheros...")
        self.update_idletasks()

        ficheros = self._buscar(rutas, inclusion, modo, exclusion)
        if not ficheros:
            self.var_estado.set("Listo.")
            detalle = "\n".join("- " + acortar(e["ruta"], 60) for e in rutas)
            aviso = "No se ha encontrado ningun fichero en:\n%s" % detalle
            if inclusion or exclusion:
                aviso += "\n\nQuiza el filtro de nombre es demasiado estricto."
            messagebox.showwarning(TITULO, aviso)
            return

        if os.path.isdir(destino):
            if not messagebox.askyesno(
                TITULO,
                "La carpeta de destino ya existe y se va a borrar por completo "
                "antes de copiar:\n\n%s\n\nContinuar?" % destino,
            ):
                self.var_estado.set("Cancelado.")
                return

        self.config_app.extension = normalizar_extension(self.var_extension.get())
        self.config_app.destino = base_destino
        self.config_app.filtro_modo = modo
        self.config_app.anadir_reciente(rutas)
        self.config_app.guardar()
        self._refrescar_recientes()
        self._refrescar_estrella()

        self.boton_extraer.config(state="disabled")
        self.barra.config(maximum=len(ficheros), value=0)
        self.var_contador.set("0/%d" % len(ficheros))

        self.hilo = threading.Thread(
            target=self._trabajo_copia,
            args=(ficheros, destino, todas_ext, rutas),
            daemon=True,
        )
        self.hilo.start()
        self.after(60, self._procesar_cola)

    @staticmethod
    def _buscar(rutas, inclusion, modo, exclusion):
        """Recorre cada origen con SUS extensiones y aplica el filtro."""
        encontrados = []
        vistos = set()
        for entrada in rutas:
            extensiones = set(entrada["extensiones"])
            for carpeta, _, ficheros in os.walk(entrada["ruta"]):
                for nombre in ficheros:
                    if os.path.splitext(nombre)[1].lower() not in extensiones:
                        continue
                    if not coincide_filtro(nombre, inclusion, modo, exclusion):
                        continue
                    completa = os.path.join(carpeta, nombre)
                    clave = normalizar_ruta(completa)
                    if clave in vistos:
                        continue
                    vistos.add(clave)
                    encontrados.append(completa)
        return encontrados

    def _trabajo_copia(self, ficheros, destino, extensiones, rutas):
        """Se ejecuta en un hilo aparte. Comunica el avance por la cola."""
        try:
            if os.path.isdir(destino):
                shutil.rmtree(destino)
            os.makedirs(destino, exist_ok=True)
        except OSError as error:
            self.cola.put(("error",
                           "No se ha podido preparar la carpeta de destino:\n%s" % error))
            return

        usados = set()
        copiados = 0
        fallidos = []

        for indice, ruta in enumerate(ficheros, start=1):
            nombre = os.path.basename(ruta)
            base, ext = os.path.splitext(nombre)

            # Solo hay colision si el nombre ya se ha usado en esta ejecucion.
            # Con varios origenes esto pasa mas a menudo que antes.
            candidato = nombre
            contador = 1
            while candidato.lower() in usados:
                candidato = "%s_%d%s" % (base, contador, ext)
                contador += 1
            usados.add(candidato.lower())

            try:
                shutil.copy2(ruta, os.path.join(destino, candidato))
                copiados += 1
            except OSError:
                fallidos.append(nombre)

            self.cola.put(("avance", indice, len(ficheros), nombre))

        self.cola.put(("fin", copiados, fallidos, destino, extensiones, rutas))

    def _procesar_cola(self):
        try:
            while True:
                mensaje = self.cola.get_nowait()
                tipo = mensaje[0]

                if tipo == "avance":
                    _, indice, total, nombre = mensaje
                    self.barra.config(value=indice)
                    self.var_contador.set("%d/%d" % (indice, total))
                    self.var_estado.set("Copiando: " + acortar(nombre, 60))

                elif tipo == "error":
                    self.boton_extraer.config(state="normal")
                    self.var_estado.set("Error.")
                    messagebox.showerror(TITULO, mensaje[1])
                    return

                elif tipo == "fin":
                    _, copiados, fallidos, destino, extensiones, rutas = mensaje
                    self._finalizar(copiados, fallidos, destino, extensiones, rutas)
                    return
        except queue.Empty:
            pass

        self.after(60, self._procesar_cola)

    def _finalizar(self, copiados, fallidos, destino, extensiones, rutas):
        self.boton_extraer.config(state="normal")
        self.var_estado.set("Hecho. %d ficheros copiados." % copiados)

        self.config_app.anadir_historial(extensiones, copiados, rutas, destino)
        self.config_app.guardar()

        tipos = formatear_extensiones(sorted(set(extensiones)))
        resumen = ("Se han copiado %d ficheros (%s) desde %d carpeta(s).\n\nDestino:\n%s"
                   % (copiados, tipos, len(rutas), destino))
        if fallidos:
            resumen += "\n\nNo se han podido copiar %d ficheros." % len(fallidos)
            messagebox.showwarning(TITULO, resumen)
        else:
            messagebox.showinfo(TITULO, resumen)

        # Se abre despues del aviso para que no quede el explorador tapado por
        # el dialogo modal. Solo si se ha copiado algo.
        if self.var_abrir.get() and copiados > 0:
            if not abrir_carpeta(destino):
                self.var_estado.set(
                    "Hecho. %d ficheros copiados. No se ha podido abrir la carpeta."
                    % copiados)

    # -- cierre --------------------------------------------------------------

    def _cerrar(self):
        self.config_app.extension = normalizar_extension(self.var_extension.get())
        destino = self.var_destino.get().strip()
        if destino:
            self.config_app.destino = os.path.normpath(destino)
        self.config_app.filtro_modo = self._modo_filtro_actual()
        self.config_app.guardar()
        self.destroy()


def main():
    Aplicacion().mainloop()


if __name__ == "__main__":
    main()
