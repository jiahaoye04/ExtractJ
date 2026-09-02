#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ExtraerFicheros
===============

Copia de forma recursiva todos los ficheros de una extension concreta desde una
carpeta de origen a una carpeta destino plana (sin estructura de subcarpetas).

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

# Los favoritos ya no tienen tope: la ventana crece sola y, si no cabe,
# la zona de rutas gana barra de desplazamiento.
MAX_RECIENTES = 3
MAX_HISTORIAL = 200

# La ventana se ajusta al contenido hasta este porcentaje del alto de pantalla.
FRACCION_ALTO_MAX = 0.80
ANCHO_INICIAL = 640
ALTO_MINIMO = 380
# Alto minimo que se le deja a la zona de favoritos/recientes cuando hay que
# recortar porque el resto de la interfaz ya se come toda la pantalla.
ALTO_MINIMO_RUTAS = 90

PREFIJO_CARPETA = "Copia"

COLOR_FONDO = "#f4f4f4"
COLOR_ESTRELLA_ON = "#e8a800"
COLOR_ESTRELLA_OFF = "#9a9a9a"

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


def nombre_carpeta_destino(extension):
    """'.java' -> 'CopiaJAVA'."""
    return PREFIJO_CARPETA + extension.lstrip(".").upper()


def acortar(ruta, maximo=58):
    """Recorta una ruta larga por el centro para que quepa en la interfaz."""
    if len(ruta) <= maximo:
        return ruta
    mitad = (maximo - 3) // 2
    return ruta[:mitad] + "..." + ruta[-mitad:]


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


# ---------------------------------------------------------------------------
# Configuracion persistente
# ---------------------------------------------------------------------------

class Configuracion:
    """Lectura y escritura del config.json situado junto al programa."""

    def __init__(self):
        self.ruta = os.path.join(directorio_programa(), FICHERO_CONFIG)
        self.extension = ".java"
        self.destino = directorio_programa()
        self.abrir_al_terminar = True
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

        self.extension = datos.get("extension", self.extension) or self.extension
        self.destino = datos.get("destino", self.destino) or self.destino
        self.abrir_al_terminar = bool(datos.get("abrir_al_terminar", True))
        ext_actual = self.extension
        self.favoritos = self._normalizar_lista(datos.get("favoritos", []),
                                                ext_actual, con_nombre=True)
        self.recientes = self._normalizar_lista(datos.get("recientes", []),
                                                ext_actual, con_nombre=False)
        self.historial = [h for h in datos.get("historial", []) if isinstance(h, dict)]

        del self.recientes[MAX_RECIENTES:]
        del self.historial[MAX_HISTORIAL:]

    def guardar(self):
        datos = {
            "extension": self.extension,
            "destino": self.destino,
            "abrir_al_terminar": self.abrir_al_terminar,
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

    # -- favoritos y recientes ---------------------------------------------
    #
    # Cada entrada es un diccionario:
    #   {"nombre": str, "ruta": str, "extension": str}
    # En recientes el nombre no se usa. La identidad de una entrada es la
    # combinacion ruta + extension: la misma carpeta con dos extensiones
    # distintas son dos entradas diferentes.

    @staticmethod
    def _normalizar_lista(bruto, extension_defecto, con_nombre):
        """Convierte una lista guardada (formato viejo o nuevo) en dicts."""
        limpio = []
        for elemento in bruto:
            if isinstance(elemento, str):
                # Formato antiguo: solo la ruta en crudo.
                ruta = elemento
                ext = extension_defecto
                nombre = elemento
            elif isinstance(elemento, dict) and elemento.get("ruta"):
                ruta = elemento["ruta"]
                ext = normalizar_extension(elemento.get("extension", extension_defecto)) \
                    or extension_defecto
                nombre = elemento.get("nombre") or ruta
            else:
                continue
            entrada = {"ruta": ruta, "extension": ext}
            if con_nombre:
                entrada["nombre"] = nombre
            limpio.append(entrada)
        return limpio

    def _clave(self, ruta, extension):
        return (self._normalizar(ruta), (extension or "").lower())

    def buscar_favorito(self, ruta, extension):
        clave = self._clave(ruta, extension)
        for fav in self.favoritos:
            if self._clave(fav["ruta"], fav["extension"]) == clave:
                return fav
        return None

    def es_favorito(self, ruta, extension):
        return self.buscar_favorito(ruta, extension) is not None

    def quitar_favorito(self, ruta, extension):
        clave = self._clave(ruta, extension)
        self.favoritos = [f for f in self.favoritos
                          if self._clave(f["ruta"], f["extension"]) != clave]

    def anadir_favorito(self, ruta, extension, nombre):
        """Anade un favorito. No hay limite de cantidad."""
        self.favoritos.append({
            "nombre": nombre or ruta,
            "ruta": ruta,
            "extension": extension,
        })
        return True

    def renombrar_favorito(self, ruta, extension, nombre):
        fav = self.buscar_favorito(ruta, extension)
        if fav is not None:
            fav["nombre"] = nombre or ruta

    def anadir_reciente(self, ruta, extension):
        clave = self._clave(ruta, extension)
        self.recientes = [r for r in self.recientes
                          if self._clave(r["ruta"], r["extension"]) != clave]
        self.recientes.insert(0, {"ruta": ruta, "extension": extension})
        del self.recientes[MAX_RECIENTES:]

    # -- historial ----------------------------------------------------------

    def anadir_historial(self, extension, total, origen, destino):
        ahora = datetime.now()
        self.historial.insert(0, {
            "fecha": ahora.strftime("%d/%m/%Y"),
            "hora": ahora.strftime("%H:%M:%S"),
            "extension": extension,
            "total": total,
            "origen": origen,
            "destino": destino,
        })
        del self.historial[MAX_HISTORIAL:]

    @staticmethod
    def _normalizar(ruta):
        return os.path.normcase(os.path.normpath(ruta))


# ---------------------------------------------------------------------------
# Ventana de historial
# ---------------------------------------------------------------------------

class VentanaHistorial(tk.Toplevel):

    def __init__(self, padre, config):
        super().__init__(padre)
        self.config_app = config

        self.title(TITULO + " - Historial")
        self.geometry("860x420")
        self.minsize(640, 300)
        self.transient(padre)

        marco = ttk.Frame(self, padding=10)
        marco.pack(fill="both", expand=True)

        columnas = ("fecha", "hora", "tipo", "total", "origen", "destino")
        self.tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=14)

        cabeceras = {
            "fecha": ("Fecha", 90, "center"),
            "hora": ("Hora", 80, "center"),
            "tipo": ("Tipo", 70, "center"),
            "total": ("Ficheros", 70, "center"),
            "origen": ("Origen", 270, "w"),
            "destino": ("Destino", 270, "w"),
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
            self.tabla.insert("", "end", values=(
                entrada.get("fecha", ""),
                entrada.get("hora", ""),
                entrada.get("extension", ""),
                entrada.get("total", 0),
                entrada.get("origen", ""),
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

        self.title(TITULO)
        self.minsize(600, ALTO_MINIMO)
        self.configure(bg=COLOR_FONDO)

        self.var_extension = tk.StringVar(value=self.config_app.extension)
        self.var_origen = tk.StringVar()
        self.var_destino = tk.StringVar(value=self.config_app.destino)
        self.var_estado = tk.StringVar(value="Listo.")
        self.var_contador = tk.StringVar(value="")
        self.var_abrir = tk.BooleanVar(value=self.config_app.abrir_al_terminar)

        # Estado interno del area desplazable de favoritos/recientes.
        self._scroll_visible = False
        self._tarea_scroll = None

        self._construir_interfaz()
        self._refrescar_rutas()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

    # -- construccion de la interfaz ---------------------------------------

    def _construir_interfaz(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        # Color de fondo real de los marcos ttk, para que el lienzo y los
        # botones de estrella no canten sobre el resto.
        self.color_marco = estilo.lookup("TFrame", "background") or COLOR_FONDO

        raiz = ttk.Frame(self, padding=12)
        raiz.pack(fill="both", expand=True)
        self.marco_raiz = raiz

        # La interfaz se divide en tres bloques:
        #   superior -> fijo arriba
        #   inferior -> fijo abajo (destino, progreso y boton Extraer)
        #   medio    -> favoritos y recientes, desplazable si no caben
        # El inferior se empaqueta antes que el medio para que nunca lo tape.
        superior = ttk.Frame(raiz)
        superior.pack(side="top", fill="x")
        superior.columnconfigure(0, weight=1)

        inferior = ttk.Frame(raiz)
        inferior.pack(side="bottom", fill="x", pady=(10, 0))
        inferior.columnconfigure(0, weight=1)

        medio = ttk.Frame(raiz)
        medio.pack(side="top", fill="both", expand=True)

        # --- Cabecera ------------------------------------------------------
        cabecera = ttk.Frame(superior)
        cabecera.grid(row=0, column=0, sticky="ew")
        cabecera.columnconfigure(0, weight=1)

        ttk.Label(cabecera, text=TITULO,
                  font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Button(cabecera, text="Historial",
                   command=self._abrir_historial).grid(row=0, column=1, sticky="e")

        ttk.Separator(superior).grid(row=1, column=0, sticky="ew", pady=10)

        # --- Extension -----------------------------------------------------
        marco_ext = ttk.Frame(superior)
        marco_ext.grid(row=2, column=0, sticky="ew")
        ttk.Label(marco_ext, text="Extension:").pack(side="left")
        ttk.Entry(marco_ext, textvariable=self.var_extension,
                  width=12).pack(side="left", padx=(8, 8))
        ttk.Label(marco_ext, text="por ejemplo .java, .py, .txt",
                  foreground="#666666").pack(side="left")

        # --- Origen --------------------------------------------------------
        ttk.Label(superior, text="Carpeta de origen",
                  font=("Segoe UI", 10, "bold")).grid(row=3, column=0,
                                                      sticky="w", pady=(14, 4))

        marco_origen = ttk.Frame(superior)
        marco_origen.grid(row=4, column=0, sticky="ew")
        marco_origen.columnconfigure(0, weight=1)

        ttk.Entry(marco_origen,
                  textvariable=self.var_origen).grid(row=0, column=0, sticky="ew")
        ttk.Button(marco_origen, text="Examinar...",
                   command=self._elegir_origen).grid(row=0, column=1, padx=(6, 0))
        self.boton_anadir_fav = ttk.Button(marco_origen, text="+", width=3,
                                           command=self._anadir_favorito_actual)
        self.boton_anadir_fav.grid(row=0, column=2, padx=(6, 0))

        # --- Zona desplazable: favoritos y recientes ------------------------
        self.lienzo_rutas = tk.Canvas(medio, bg=self.color_marco,
                                      highlightthickness=0, bd=0, height=1)
        self.barra_rutas = ttk.Scrollbar(medio, orient="vertical",
                                         command=self.lienzo_rutas.yview)
        self.lienzo_rutas.configure(yscrollcommand=self.barra_rutas.set)
        self.lienzo_rutas.pack(side="left", fill="both", expand=True,
                               pady=(10, 0))

        self.marco_rutas = ttk.Frame(self.lienzo_rutas)
        self._id_ventana_rutas = self.lienzo_rutas.create_window(
            (0, 0), window=self.marco_rutas, anchor="nw")

        # El marco interior debe ocupar todo el ancho del lienzo.
        #
        # Ojo: estos manejadores NO pueden mostrar ni ocultar la barra. Si lo
        # hicieran, el cambio de empaquetado dispararia otro <Configure> y se
        # entra en un bucle infinito de eventos. Aqui solo se recalcula la
        # region visible; la barra se decide aparte y con retardo.
        self.lienzo_rutas.bind(
            "<Configure>",
            lambda ev: (self.lienzo_rutas.itemconfigure(self._id_ventana_rutas,
                                                        width=ev.width),
                        self._region_scroll()))
        self.marco_rutas.bind("<Configure>", lambda _ev: self._region_scroll())
        self.bind("<Configure>", lambda _ev: self._programar_scroll())

        # Rueda del raton: solo mientras el puntero esta sobre la zona.
        self.lienzo_rutas.bind("<Enter>", self._activar_rueda)
        self.lienzo_rutas.bind("<Leave>", self._desactivar_rueda)

        self.marco_favoritos = ttk.Frame(self.marco_rutas)
        self.marco_favoritos.pack(fill="x")
        self.marco_recientes = ttk.Frame(self.marco_rutas)
        self.marco_recientes.pack(fill="x", pady=(10, 0))

        # --- Destino -------------------------------------------------------
        ttk.Label(inferior, text="Carpeta de destino",
                  font=("Segoe UI", 10, "bold")).grid(row=0, column=0,
                                                      sticky="w", pady=(6, 4))

        marco_destino = ttk.Frame(inferior)
        marco_destino.grid(row=1, column=0, sticky="ew")
        marco_destino.columnconfigure(0, weight=1)

        ttk.Entry(marco_destino,
                  textvariable=self.var_destino).grid(row=0, column=0, sticky="ew")
        ttk.Button(marco_destino, text="Examinar...",
                   command=self._elegir_destino).grid(row=0, column=1, padx=(6, 0))

        self.etiqueta_destino_final = ttk.Label(inferior, text="",
                                                foreground="#666666")
        self.etiqueta_destino_final.grid(row=2, column=0, sticky="w", pady=(4, 0))
        self.var_extension.trace_add("write", lambda *_: self._refrescar_destino_final())
        self.var_destino.trace_add("write", lambda *_: self._refrescar_destino_final())
        self._refrescar_destino_final()

        ttk.Checkbutton(inferior,
                        text="Abrir la carpeta al terminar",
                        variable=self.var_abrir,
                        command=self._cambiar_abrir).grid(row=3, column=0,
                                                          sticky="w", pady=(6, 0))

        # --- Progreso ------------------------------------------------------
        marco_progreso = ttk.Frame(inferior)
        marco_progreso.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        marco_progreso.columnconfigure(0, weight=1)

        self.barra = ttk.Progressbar(marco_progreso, mode="determinate", maximum=100)
        self.barra.grid(row=0, column=0, sticky="ew")
        ttk.Label(marco_progreso, textvariable=self.var_contador,
                  width=12, anchor="e").grid(row=0, column=1, padx=(8, 0))

        ttk.Label(inferior, textvariable=self.var_estado,
                  foreground="#444444").grid(row=5, column=0, sticky="w", pady=(6, 0))

        # --- Boton principal ------------------------------------------------
        self.boton_extraer = ttk.Button(inferior, text="Extraer ficheros",
                                        command=self._iniciar_extraccion)
        self.boton_extraer.grid(row=6, column=0, sticky="ew", pady=(12, 0))

    # -- altura de la ventana y desplazamiento ------------------------------

    def _ajustar_altura(self):
        """Ajusta el alto de la ventana al contenido, con tope y scroll.

        Se llama cada vez que cambian las listas de favoritos o recientes. La
        idea: el lienzo pide exactamente lo que ocupa su contenido, se mide
        cuanto pide la ventana entera y, si pasa del tope, se le recorta al
        lienzo justo lo que sobra (y ahi aparece la barra).
        """
        self.update_idletasks()

        alto_contenido = max(self.marco_rutas.winfo_reqheight(), 1)
        self.lienzo_rutas.configure(height=alto_contenido)
        self.update_idletasks()

        alto_max = int(self.winfo_screenheight() * FRACCION_ALTO_MAX)
        alto_pedido = self.winfo_reqheight()

        if alto_pedido > alto_max:
            sobra = alto_pedido - alto_max
            self.lienzo_rutas.configure(
                height=max(alto_contenido - sobra, ALTO_MINIMO_RUTAS))
            self.update_idletasks()
            alto_pedido = self.winfo_reqheight()

        alto = max(min(alto_pedido, alto_max), ALTO_MINIMO)
        ancho = self.winfo_width() if self.winfo_ismapped() else ANCHO_INICIAL
        ancho = max(ancho, ANCHO_INICIAL)
        self.geometry("%dx%d" % (ancho, alto))

        self._programar_scroll()

    def _region_scroll(self):
        """Recalcula el area desplazable. No cambia el empaquetado."""
        self.lienzo_rutas.configure(scrollregion=self.lienzo_rutas.bbox("all"))

    def _programar_scroll(self):
        """Revisa la barra con un pequeno retardo.

        El retardo real (no after_idle) es lo que rompe la realimentacion:
        mostrar u ocultar la barra genera <Configure>, que vuelve a programar
        una revision, pero para entonces el estado ya es estable y no cambia
        nada mas.
        """
        pendiente = getattr(self, "_tarea_scroll", None)
        if pendiente is not None:
            try:
                self.after_cancel(pendiente)
            except tk.TclError:
                pass
        self._tarea_scroll = self.after(120, self._actualizar_scroll)

    def _actualizar_scroll(self):
        """Muestra la barra de desplazamiento solo cuando hace falta."""
        self._tarea_scroll = None
        self._region_scroll()
        hace_falta = (self.marco_rutas.winfo_reqheight()
                      > self.lienzo_rutas.winfo_height() + 2)

        if hace_falta and not self._scroll_visible:
            self.barra_rutas.pack(side="right", fill="y", pady=(10, 0))
            self._scroll_visible = True
        elif not hace_falta and self._scroll_visible:
            self.barra_rutas.pack_forget()
            self._scroll_visible = False
            self.lienzo_rutas.yview_moveto(0)

    def _activar_rueda(self, _evento=None):
        self.lienzo_rutas.bind_all("<MouseWheel>", self._rueda)

    def _desactivar_rueda(self, _evento=None):
        self.lienzo_rutas.unbind_all("<MouseWheel>")

    def _rueda(self, evento):
        if self._scroll_visible:
            self.lienzo_rutas.yview_scroll(-1 * (evento.delta // 120), "units")

    # -- favoritos y recientes ---------------------------------------------

    def _refrescar_rutas(self):
        for hijo in self.marco_favoritos.winfo_children():
            hijo.destroy()
        for hijo in self.marco_recientes.winfo_children():
            hijo.destroy()

        if self.config_app.favoritos:
            ttk.Label(self.marco_favoritos, text="Favoritos",
                      font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
            for entrada in list(self.config_app.favoritos):
                self._fila_ruta(self.marco_favoritos, entrada, favorito=True)

        if self.config_app.recientes:
            ttk.Label(self.marco_recientes, text="Recientes",
                      font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
            for entrada in list(self.config_app.recientes):
                self._fila_ruta(self.marco_recientes, entrada, favorito=False)

        self._ajustar_altura()

    def _fila_ruta(self, contenedor, entrada, favorito):
        ruta = entrada["ruta"]
        extension = entrada["extension"]

        fila = ttk.Frame(contenedor)
        fila.pack(fill="x", pady=1)

        marcado = self.config_app.es_favorito(ruta, extension)
        estrella = tk.Button(
            fila,
            text="\u2605" if marcado else "\u2606",
            fg=COLOR_ESTRELLA_ON if marcado else COLOR_ESTRELLA_OFF,
            font=("Segoe UI", 11),
            relief="flat", bd=0, cursor="hand2",
            bg=self.color_marco, activebackground=self.color_marco,
            command=lambda r=ruta, e=extension: self._alternar_estrella(r, e),
        )
        estrella.pack(side="left", padx=(0, 6))

        # Etiqueta de extension a la izquierda del texto.
        ttk.Label(fila, text=extension.upper().lstrip("."),
                  width=6, anchor="w",
                  foreground="#555555").pack(side="left", padx=(0, 4))

        if favorito:
            texto = entrada.get("nombre") or ruta
        else:
            texto = acortar(ruta)

        boton = ttk.Button(fila, text=texto,
                           command=lambda r=ruta, e=extension: self._usar_ruta(r, e))
        boton.pack(side="left", fill="x", expand=True)

        if favorito:
            ttk.Button(fila, text="Renombrar", width=10,
                       command=lambda r=ruta, e=extension: self._renombrar_favorito(r, e)).pack(
                           side="left", padx=(6, 0))
            ttk.Button(fila, text="Quitar", width=7,
                       command=lambda r=ruta, e=extension: self._quitar_favorito(r, e)).pack(
                           side="left", padx=(4, 0))

    def _usar_ruta(self, ruta, extension):
        """Rellena origen y extension desde un favorito o reciente."""
        self.var_origen.set(ruta)
        if extension:
            self.var_extension.set(extension)

    def _alternar_estrella(self, ruta, extension):
        """Estrella: si es favorito lo quita, si no lo anade pidiendo nombre."""
        if self.config_app.es_favorito(ruta, extension):
            self._quitar_favorito(ruta, extension)
        else:
            self._crear_favorito(ruta, extension)

    def _crear_favorito(self, ruta, extension):
        if self.config_app.es_favorito(ruta, extension):
            messagebox.showinfo(TITULO, "Esa carpeta ya esta en favoritos con esa extension.")
            return
        nombre = simpledialog.askstring(
            TITULO,
            "Nombre para este favorito:",
            initialvalue=os.path.basename(ruta.rstrip("\\/")) or ruta,
            parent=self,
        )
        if nombre is None:  # el usuario cancelo
            return
        self.config_app.anadir_favorito(ruta, extension, nombre.strip())
        self.config_app.guardar()
        self._refrescar_rutas()

    def _quitar_favorito(self, ruta, extension):
        self.config_app.quitar_favorito(ruta, extension)
        self.config_app.guardar()
        self._refrescar_rutas()

    def _renombrar_favorito(self, ruta, extension):
        fav = self.config_app.buscar_favorito(ruta, extension)
        if fav is None:
            return
        nombre = simpledialog.askstring(
            TITULO,
            "Nuevo nombre para este favorito:",
            initialvalue=fav.get("nombre") or ruta,
            parent=self,
        )
        if nombre is None:
            return
        self.config_app.renombrar_favorito(ruta, extension, nombre.strip())
        self.config_app.guardar()
        self._refrescar_rutas()

    def _anadir_favorito_actual(self):
        ruta = self.var_origen.get().strip().strip('"')
        extension = normalizar_extension(self.var_extension.get())
        if not ruta:
            messagebox.showinfo(TITULO, "Escribe o elige primero una carpeta de origen.")
            return
        if not os.path.isdir(ruta):
            messagebox.showerror(TITULO, "La carpeta indicada no existe:\n%s" % ruta)
            return
        if not extension:
            messagebox.showinfo(TITULO, "Indica primero la extension a extraer.")
            return
        self._crear_favorito(os.path.normpath(ruta), extension)

    def _cambiar_abrir(self):
        """La casilla se guarda al momento, no solo al cerrar."""
        self.config_app.abrir_al_terminar = bool(self.var_abrir.get())
        self.config_app.guardar()

    # -- seleccion de carpetas ---------------------------------------------

    def _elegir_origen(self):
        inicial = self.var_origen.get().strip() or directorio_programa()
        ruta = filedialog.askdirectory(title="Selecciona la carpeta de origen",
                                       initialdir=inicial)
        if ruta:
            self.var_origen.set(os.path.normpath(ruta))

    def _elegir_destino(self):
        inicial = self.var_destino.get().strip() or directorio_programa()
        ruta = filedialog.askdirectory(title="Selecciona la carpeta de destino",
                                       initialdir=inicial)
        if ruta:
            self.var_destino.set(os.path.normpath(ruta))
            self.config_app.destino = os.path.normpath(ruta)
            self.config_app.guardar()

    def _refrescar_destino_final(self):
        extension = normalizar_extension(self.var_extension.get())
        base = self.var_destino.get().strip() or directorio_programa()
        if extension:
            carpeta = os.path.join(base, nombre_carpeta_destino(extension))
            self.etiqueta_destino_final.config(text="Se creara: " + acortar(carpeta, 70))
        else:
            self.etiqueta_destino_final.config(text="")

    def _abrir_historial(self):
        VentanaHistorial(self, self.config_app)

    # -- extraccion ---------------------------------------------------------

    def _iniciar_extraccion(self):
        if self.hilo and self.hilo.is_alive():
            return

        extension = normalizar_extension(self.var_extension.get())
        origen = self.var_origen.get().strip().strip('"')
        base_destino = self.var_destino.get().strip().strip('"') or directorio_programa()

        if not extension:
            messagebox.showerror(TITULO, "Indica una extension, por ejemplo .java")
            return
        if extension not in EXTENSIONES_VALIDAS:
            messagebox.showerror(
                TITULO,
                "La extension '%s' no es valida.\n\n"
                "Debe ser una extension de fichero conocida, como .java, .py, "
                ".txt o .pdf." % extension,
            )
            return
        if not origen:
            messagebox.showerror(TITULO, "Indica la carpeta de origen.")
            return
        if not os.path.isdir(origen):
            messagebox.showerror(TITULO, "La carpeta de origen no existe:\n%s" % origen)
            return
        if not os.path.isdir(base_destino):
            messagebox.showerror(TITULO, "La carpeta de destino no existe:\n%s" % base_destino)
            return

        origen = os.path.normpath(origen)
        base_destino = os.path.normpath(base_destino)
        destino = os.path.join(base_destino, nombre_carpeta_destino(extension))

        # El destino no puede estar dentro del origen: se copiaria a si mismo.
        if os.path.normcase(destino).startswith(os.path.normcase(origen) + os.sep):
            messagebox.showerror(
                TITULO,
                "La carpeta de destino esta dentro de la de origen.\n"
                "Elige otra ubicacion para evitar copiar sobre lo copiado.",
            )
            return

        self.var_estado.set("Buscando ficheros %s..." % extension)
        self.update_idletasks()

        ficheros = self._buscar(origen, extension)
        if not ficheros:
            self.var_estado.set("Listo.")
            messagebox.showwarning(
                TITULO,
                "No se han encontrado ficheros %s en:\n%s" % (extension, origen),
            )
            return

        if os.path.isdir(destino):
            if not messagebox.askyesno(
                TITULO,
                "La carpeta de destino ya existe y se va a borrar por completo "
                "antes de copiar:\n\n%s\n\nContinuar?" % destino,
            ):
                self.var_estado.set("Cancelado.")
                return

        # Persistimos las preferencias antes de empezar.
        self.config_app.extension = extension
        self.config_app.destino = base_destino
        self.config_app.anadir_reciente(origen, extension)
        self.config_app.guardar()
        self._refrescar_rutas()

        self.boton_extraer.config(state="disabled")
        self.barra.config(maximum=len(ficheros), value=0)
        self.var_contador.set("0/%d" % len(ficheros))

        self.hilo = threading.Thread(
            target=self._trabajo_copia,
            args=(ficheros, destino, extension, origen, base_destino),
            daemon=True,
        )
        self.hilo.start()
        self.after(60, self._procesar_cola)

    @staticmethod
    def _buscar(origen, extension):
        encontrados = []
        for carpeta, _, ficheros in os.walk(origen):
            for nombre in ficheros:
                if os.path.splitext(nombre)[1].lower() == extension:
                    encontrados.append(os.path.join(carpeta, nombre))
        return encontrados

    def _trabajo_copia(self, ficheros, destino, extension, origen, base_destino):
        """Se ejecuta en un hilo aparte. Comunica el avance por la cola."""
        try:
            if os.path.isdir(destino):
                shutil.rmtree(destino)
            os.makedirs(destino, exist_ok=True)
        except OSError as error:
            self.cola.put(("error", "No se ha podido preparar la carpeta de destino:\n%s" % error))
            return

        usados = set()
        copiados = 0
        fallidos = []

        for indice, ruta in enumerate(ficheros, start=1):
            nombre = os.path.basename(ruta)
            base, ext = os.path.splitext(nombre)

            # Solo hay colision si el nombre ya se ha usado en esta ejecucion.
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

        self.cola.put(("fin", copiados, fallidos, destino, extension, origen, base_destino))

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
                    _, copiados, fallidos, destino, extension, origen, base = mensaje
                    self._finalizar(copiados, fallidos, destino, extension, origen, base)
                    return
        except queue.Empty:
            pass

        self.after(60, self._procesar_cola)

    def _finalizar(self, copiados, fallidos, destino, extension, origen, base_destino):
        self.boton_extraer.config(state="normal")
        self.var_estado.set("Hecho. %d ficheros copiados." % copiados)

        self.config_app.anadir_historial(extension, copiados, origen, destino)
        self.config_app.guardar()

        resumen = ("Se han copiado %d ficheros %s.\n\nDestino:\n%s"
                   % (copiados, extension, destino))
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
        self.config_app.extension = normalizar_extension(self.var_extension.get()) \
            or self.config_app.extension
        destino = self.var_destino.get().strip()
        if destino:
            self.config_app.destino = os.path.normpath(destino)
        self.config_app.guardar()
        self.destroy()


def main():
    Aplicacion().mainloop()


if __name__ == "__main__":
    main()