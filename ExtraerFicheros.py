#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ExtraerFicheros
===============

Copia de forma recursiva los ficheros de una o varias carpetas de origen a una
unica carpeta destino plana (sin estructura de subcarpetas). Cada carpeta de
origen lleva su propio juego de extensiones y sus propios filtros (tamano,
texto en el nombre y muestra aleatoria), ademas del filtro global de nombre.
Opcionalmente conserva una copia de los ficheros de las ultimas extracciones.

Solo usa la biblioteca estandar de Python (tkinter incluido).
"""

import json
import math
import os
import queue
import random
import re
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
VERSION_CONFIG = 3

MAX_HISTORIAL = 200
TOPE_RECIENTES = 10          # maximo que admite el contador de la interfaz
RECIENTES_POR_DEFECTO = 3
GUARDADOS_POR_DEFECTO = 3    # nunca mas que recientes

# Copias de los ficheros de las ultimas extracciones.
NOMBRE_ALMACEN = "Extracciones guardadas"
# Fichero que ExtractJ deja dentro de cada copia guardada. Ademas de listar el
# contenido, es la firma que autoriza a borrarla: sin el, el borrado
# automatico no toca la carpeta, aunque el config apunte a ella.
MARCADOR_GUARDADO = "_contenido_extractj.json"
FIRMA_PROGRAMA = "ExtractJ"

# La ventana se ajusta al contenido hasta este porcentaje del alto de pantalla.
FRACCION_ALTO_MAX = 0.80
ANCHO_INICIAL = 1120
ANCHO_MINIMO = 940
ALTO_MINIMO = 460

# Filas visibles como maximo en cada panel antes de que aparezca su scroll.
FILAS_MAX_ORIGEN = 8
FILAS_MAX_FAVORITOS = 12
ALTO_MINIMO_PANEL = 60
PAD_FILA = 3                 # separacion vertical entre tarjetas

PREFIJO_CARPETA = "Copia"
NOMBRE_MIXTO = PREFIJO_CARPETA + "MIXTO"
NOMBRE_TODO = PREFIJO_CARPETA + "TODO"
TEXTO_TODOS = "todos los tipos"

# La extension global se escribe en las lineas este tiempo despues de la
# ultima tecla. Letra a letra, escribir '.cs' pasaria por '.c' (valida) y
# podria llevarse un '.c' que la linea tuviera escrito a mano.
MS_APLICAR_GLOBAL = 500

FUENTE = "Segoe UI"

# Temas. "sistema" sigue al de Windows; los otros dos lo fuerzan.
TEMAS = [
    ("sistema", "Sistema"),
    ("claro", "Claro"),
    ("oscuro", "Oscuro"),
]
SEGUNDOS_VIGILAR_SISTEMA = 3

PALETAS = {
    "claro": {
        "fondo": "#f2f2f2",
        "tarjeta": "#ffffff",
        "borde": "#d6d6d6",
        "texto": "#1e1e1e",
        "suave": "#6b6b6b",
        "muy_suave": "#9a9a9a",
        "estado": "#444444",
        "filtro": "#1f6fb2",        # resumen de filtros cuando hay alguno
        "estrella_on": "#e8a800",
        "estrella_off": "#a0a0a0",
        "ayuda_fondo": "#ffffe6",
        "ayuda_texto": "#222222",
        "campo": "#ffffff",
        "campo_borde": "#bdbdbd",
        "campo_off": "#ececec",
        "boton": "#e4e4e4",
        "boton_activo": "#d8d8d8",
        "boton_pulsado": "#c9c9c9",
        "boton_borde": "#b8b8b8",
        "acento": "#2f7fd1",
        "acento_activo": "#2770bb",
        "acento_texto": "#ffffff",
        "seleccion": "#cfe3f7",
        "seleccion_texto": "#1e1e1e",
        "canal": "#e2e2e2",         # fondo de barras de progreso y scroll
        "desactivado": "#a3a3a3",
    },
    # Gris carbon, no negro puro: el negro absoluto cansa y hace que los
    # bordes de las tarjetas se pierdan. Las tarjetas van un punto mas
    # claras que el fondo, que es lo que en oscuro marca la profundidad.
    "oscuro": {
        "fondo": "#1f2124",
        "tarjeta": "#2a2d31",
        "borde": "#3b3f45",
        "texto": "#e7e7e7",
        "suave": "#a4a9b0",
        "muy_suave": "#7b8189",
        "estado": "#c9c9c9",
        "filtro": "#74b8ff",
        "estrella_on": "#f2c14e",
        "estrella_off": "#6c727a",
        "ayuda_fondo": "#34373c",
        "ayuda_texto": "#eeeeee",
        "campo": "#17191b",
        "campo_borde": "#464a51",
        "campo_off": "#232528",
        "boton": "#353940",
        "boton_activo": "#3f444b",
        "boton_pulsado": "#4a4f57",
        "boton_borde": "#4b5058",
        "acento": "#3d8ee0",
        "acento_activo": "#4a9aea",
        "acento_texto": "#ffffff",
        "seleccion": "#2d5a8a",
        "seleccion_texto": "#ffffff",
        "canal": "#2a2d31",
        "desactivado": "#6a7078",
    },
}

# Paleta ACTIVA. Se modifica en sitio al cambiar de tema, asi que todo lo que
# lea de aqui al crearse (tarjetas, ayudas, dialogos) sale ya con el tema
# bueno, y lo ya creado se repinta desde Aplicacion._aplicar_tema.
P = dict(PALETAS["claro"])

# Modos del filtro global de nombre. La clave es lo que se guarda en config.
MODOS_FILTRO = [
    ("contiene", "Contiene"),
    ("empieza", "Empieza por"),
    ("termina", "Termina por"),
]

# Modos de la muestra aleatoria por carpeta.
MODOS_AZAR = [
    ("", "Todos los ficheros"),
    ("numero", "Numero fijo al azar"),
    ("porcentaje", "Porcentaje al azar"),
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


def nombre_carpeta_destino(rutas):
    """Nombre de la carpeta destino a partir de las lineas.

    Una linea SIN extensiones extrae todos los tipos. Si todas son asi, sale
    'CopiaTODO'; si se mezclan con lineas que si tienen, 'CopiaMIXTO'. Si
    todas comparten una unica extension, 'CopiaJAVA' y similares.
    """
    listas = [r.get("extensiones", []) for r in rutas]
    if not listas:
        return NOMBRE_MIXTO
    if all(not exts for exts in listas):
        return NOMBRE_TODO
    if any(not exts for exts in listas):
        return NOMBRE_MIXTO
    unicas = sorted({ext for exts in listas for ext in exts})
    if len(unicas) == 1:
        return PREFIJO_CARPETA + unicas[0].lstrip(".").upper()
    return NOMBRE_MIXTO


def sustituir_global(texto_linea, viejas, nuevas):
    """Cambia en el campo de una linea las extensiones de la global anterior
    por las de la global nueva, respetando lo que la linea tenga suyo.

    Lo que hay escrito se conserva tal cual, incluso piezas invalidas: si la
    linea tiene un error, que lo siga teniendo y el aviso al extraer lo diga.
    Cualquier pieza igual a una extension de la global anterior cuenta como
    puesta por la global y se quita.
    """
    viejas = set(viejas)
    piezas = [pieza for pieza in trocear_extensiones(texto_linea)
              if normalizar_extension(pieza) not in viejas]
    presentes = {normalizar_extension(pieza) for pieza in piezas}
    for ext in nuevas:
        if ext not in presentes:
            piezas.append(ext)
            presentes.add(ext)
    return " ".join(piezas)


def acortar(ruta, maximo=58):
    """Recorta una ruta larga por el centro para que quepa en la interfaz."""
    if len(ruta) <= maximo:
        return ruta
    mitad = (maximo - 3) // 2
    return ruta[:mitad] + "..." + ruta[-mitad:]


def nombre_base(nombre_fichero):
    """Nombre sin extension y en minusculas: contra esto se comparan los
    filtros de texto, por eso 'holacocina.java' termina por 'cocina'."""
    return os.path.splitext(nombre_fichero)[0].lower()


def coincide_filtro(nombre_fichero, inclusion, modo, exclusion):
    """Filtro GLOBAL de nombre (el de la cabecera, para todas las lineas)."""
    base = nombre_base(nombre_fichero)

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


def almacen_por_defecto():
    return os.path.join(directorio_programa(), NOMBRE_ALMACEN)


def formatear_tamano(octetos):
    try:
        octetos = int(octetos)
    except (TypeError, ValueError):
        return ""
    if octetos < 1024:
        return "%d B" % octetos
    if octetos < 1024 * 1024:
        return "%.1f KB" % (octetos / 1024.0)
    return "%.1f MB" % (octetos / (1024.0 * 1024.0))


def leer_contenido_guardado(carpeta):
    """El marcador de una copia guardada, o None si no esta o no es nuestro."""
    try:
        with open(os.path.join(carpeta, MARCADOR_GUARDADO), "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(datos, dict) or datos.get("programa") != FIRMA_PROGRAMA:
        return None
    return datos


def borrar_carpeta_guardada(carpeta):
    """Borra una copia guardada SOLO si lleva el marcador de ExtractJ.

    Es la unica funcion que borra copias. La comprobacion del marcador es la
    red de seguridad: un config editado a mano, o una ruta que apunte a otra
    cosa, nunca acaba en un rmtree de algo que no haya creado el programa.
    """
    if not carpeta or leer_contenido_guardado(carpeta) is None:
        return False
    shutil.rmtree(carpeta, ignore_errors=True)
    return True


def tema_de_windows():
    """'oscuro' o 'claro' segun Configuracion > Personalizacion > Colores.

    Lee AppsUseLightTheme del registro con winreg (biblioteca estandar).
    Fuera de Windows, o si la clave no existe, se asume claro.
    """
    if sys.platform != "win32":
        return "claro"
    try:
        import winreg
        clave = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        try:
            valor, _ = winreg.QueryValueEx(clave, "AppsUseLightTheme")
        finally:
            winreg.CloseKey(clave)
        return "claro" if valor else "oscuro"
    except (OSError, ImportError):
        return "claro"


def pintar_barra_titulo(ventana, oscuro):
    """Oscurece (o aclara) la barra de titulo nativa en Windows 10/11.

    Tk no controla esa barra: es de Windows. Se le pide al gestor de ventanas
    con DwmSetWindowAttribute via ctypes (biblioteca estandar). El atributo es
    el 20 en Windows 11 y en Windows 10 desde 20H1; en builds anteriores era el
    19, por eso se prueban los dos. Despues hay que forzar un repintado del
    marco, o el cambio no se ve hasta que la ventana pierde el foco.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ventana.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(ventana.winfo_id()) or ventana.winfo_id()
        valor = ctypes.c_int(1 if oscuro else 0)
        for atributo in (20, 19):
            resultado = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, atributo, ctypes.byref(valor), ctypes.sizeof(valor))
            if resultado == 0:
                break
        # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                                          0x0002 | 0x0001 | 0x0004 | 0x0020)
    except (AttributeError, OSError, tk.TclError):
        pass


def nombre_carpeta(ruta):
    """Ultimo tramo de una ruta, cortando por / y por \\ en cualquier sistema."""
    limpia = (ruta or "").rstrip("\\/")
    return re.split(r"[\\/]", limpia)[-1] or ruta


def formatear_numero(valor):
    """1.0 -> '1', 2.5 -> '2.5'. Para mostrar KB sin decimales inutiles."""
    if valor is None:
        return ""
    return ("%f" % valor).rstrip("0").rstrip(".")


def leer_numero(texto):
    """'1,5' o '1.5' -> 1.5. Vacio -> None. Lanza ValueError si no es numero."""
    texto = (texto or "").strip().replace(",", ".")
    if not texto:
        return None
    return float(texto)


# ---------------------------------------------------------------------------
# Filtros por carpeta
# ---------------------------------------------------------------------------
#
# Cada ruta de origen lleva un dict de filtros:
#   {"min_kb": float|None, "max_kb": float|None, "contiene": str,
#    "azar_modo": "" | "numero" | "porcentaje", "azar_valor": int}
# Se aplican DESPUES de la extension y del filtro global de nombre. La muestra
# aleatoria va la ultima, sobre lo que ya ha sobrevivido al resto.

def filtros_vacios():
    return {"min_kb": None, "max_kb": None, "contiene": "",
            "azar_modo": "", "azar_valor": 0}


def normalizar_filtros(bruto):
    """Limpia un dict de filtros venido del config o de la ventana.

    Todo valor raro se descarta en silencio: un config editado a mano no debe
    poder romper el arranque.
    """
    limpio = filtros_vacios()
    if not isinstance(bruto, dict):
        return limpio

    for clave in ("min_kb", "max_kb"):
        valor = bruto.get(clave)
        try:
            valor = leer_numero(str(valor)) if valor is not None else None
        except (TypeError, ValueError):
            valor = None
        if valor is not None and valor < 0:
            valor = None
        limpio[clave] = valor

    if (limpio["min_kb"] is not None and limpio["max_kb"] is not None
            and limpio["min_kb"] > limpio["max_kb"]):
        limpio["min_kb"], limpio["max_kb"] = None, None

    limpio["contiene"] = str(bruto.get("contiene") or "").strip().lower()

    modo = bruto.get("azar_modo") or ""
    try:
        valor = int(bruto.get("azar_valor") or 0)
    except (TypeError, ValueError):
        valor = 0
    if modo == "numero" and valor >= 1:
        limpio["azar_modo"], limpio["azar_valor"] = modo, valor
    elif modo == "porcentaje" and 1 <= valor <= 100:
        limpio["azar_modo"], limpio["azar_valor"] = modo, valor

    return limpio


def filtros_activos(filtros):
    f = normalizar_filtros(filtros)
    return bool(f["min_kb"] is not None or f["max_kb"] is not None
                or f["contiene"] or f["azar_modo"])


def resumen_filtros(filtros):
    """'>= 10 KB · <= 500 KB · "cocina" · 10 al azar'. Vacio si no hay nada."""
    f = normalizar_filtros(filtros)
    piezas = []
    if f["min_kb"] is not None and f["max_kb"] is not None:
        piezas.append("%s-%s KB" % (formatear_numero(f["min_kb"]),
                                    formatear_numero(f["max_kb"])))
    elif f["min_kb"] is not None:
        piezas.append(">= %s KB" % formatear_numero(f["min_kb"]))
    elif f["max_kb"] is not None:
        piezas.append("<= %s KB" % formatear_numero(f["max_kb"]))
    if f["contiene"]:
        piezas.append('nombre con "%s"' % f["contiene"])
    if f["azar_modo"] == "numero":
        piezas.append("%d al azar" % f["azar_valor"])
    elif f["azar_modo"] == "porcentaje":
        piezas.append("%d %% al azar" % f["azar_valor"])
    return " \u00b7 ".join(piezas)


def clave_filtros(filtros):
    f = normalizar_filtros(filtros)
    return (f["min_kb"], f["max_kb"], f["contiene"], f["azar_modo"], f["azar_valor"])


def pasa_filtros_carpeta(ruta_fichero, nombre_fichero, filtros):
    """Tamano y texto. La muestra aleatoria se aplica aparte, sobre el total."""
    if filtros["contiene"] and filtros["contiene"] not in nombre_base(nombre_fichero):
        return False
    if filtros["min_kb"] is None and filtros["max_kb"] is None:
        return True
    try:
        kb = os.path.getsize(ruta_fichero) / 1024.0
    except OSError:
        return False
    if filtros["min_kb"] is not None and kb < filtros["min_kb"]:
        return False
    if filtros["max_kb"] is not None and kb > filtros["max_kb"]:
        return False
    return True


def aplicar_muestra(ficheros, filtros):
    """Devuelve una muestra aleatoria segun el modo, o la lista tal cual."""
    total = len(ficheros)
    if not total or not filtros["azar_modo"]:
        return list(ficheros)
    if filtros["azar_modo"] == "numero":
        cuantos = min(filtros["azar_valor"], total)
    else:
        # Con porcentaje se redondea hacia arriba: un 10 % de 3 ficheros saca
        # 1, no 0. Una muestra vacia no le sirve a nadie.
        cuantos = min(total, max(1, int(math.ceil(total * filtros["azar_valor"] / 100.0))))
    return random.sample(list(ficheros), cuantos)


# ---------------------------------------------------------------------------
# Grupos de rutas (favoritos y recientes)
# ---------------------------------------------------------------------------

def copiar_entrada(entrada):
    """Copia profunda de una ruta de un grupo, para no compartir listas."""
    return {"ruta": entrada["ruta"],
            "extensiones": list(entrada.get("extensiones", [])),
            "filtros": normalizar_filtros(entrada.get("filtros"))}


def clave_rutas(rutas):
    """Identidad de un grupo: el CONJUNTO de rutas, sin mirar nada mas.

    Decide si guardar un favorito es una alta o una sobrescritura, y si un
    reciente nuevo sustituye a uno viejo.
    """
    return frozenset(normalizar_ruta(r["ruta"]) for r in rutas if r.get("ruta"))


def clave_completa(rutas):
    """Identidad estricta: rutas, extensiones Y filtros. Enciende la estrella."""
    piezas = []
    for entrada in rutas:
        if not entrada.get("ruta"):
            continue
        piezas.append((normalizar_ruta(entrada["ruta"]),
                       tuple(sorted(entrada.get("extensiones", []))),
                       clave_filtros(entrada.get("filtros"))))
    return frozenset(piezas)


def resumen_rutas(rutas, maximo=52):
    """'C:\\...\\chift  (+2)' para mostrar un grupo en una sola linea."""
    if not rutas:
        return "(sin rutas)"
    texto = acortar(rutas[0].get("ruta", ""), maximo)
    if len(rutas) > 1:
        texto += "  (+%d)" % (len(rutas) - 1)
    return texto


def resumen_extensiones(rutas):
    """Todas las extensiones de un grupo, sin repetir. Si alguna linea va sin
    extensiones (todos los tipos) se dice al final."""
    todas = []
    alguna_todas = False
    for entrada in rutas:
        exts = entrada.get("extensiones", [])
        if not exts:
            alguna_todas = True
        for ext in exts:
            if ext not in todas:
                todas.append(ext)
    texto = formatear_extensiones(sorted(todas))
    if alguna_todas:
        texto = (texto + " + " + TEXTO_TODOS) if texto else TEXTO_TODOS
    return texto


def detalle_grupo(rutas):
    """Texto largo con TODAS las rutas, para la ayuda emergente."""
    lineas = []
    for numero, entrada in enumerate(rutas, start=1):
        lineas.append("%d. %s" % (numero, entrada.get("ruta", "")))
        texto = "     " + (formatear_extensiones(entrada.get("extensiones", []))
                           or TEXTO_TODOS)
        filtros = resumen_filtros(entrada.get("filtros"))
        if filtros:
            texto += "  \u00b7  " + filtros
        lineas.append(texto)
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Configuracion persistente
# ---------------------------------------------------------------------------

class Configuracion:
    """Lectura y escritura del config.json situado junto al programa.

    Formato 3: favoritos y recientes son GRUPOS, y cada ruta lleva filtros.
        favorito = {"nombre": str,
                    "rutas": [{"ruta": str, "extensiones": [], "filtros": {}}]}
        reciente = {"rutas": [...]}
    Los formatos 1 y 2 se migran al cargar.
    """

    def __init__(self):
        self.ruta = os.path.join(directorio_programa(), FICHERO_CONFIG)
        self.extension = ""
        self.destino = directorio_programa()
        self.abrir_al_terminar = True
        self.max_recientes = RECIENTES_POR_DEFECTO
        self.max_guardados = GUARDADOS_POR_DEFECTO
        self.carpeta_guardados = ""          # vacio = junto al programa
        self.sustituir_al_cargar = False     # False = anadir por encima
        self.filtro_modo = "contiene"
        self.tema = "sistema"
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

        tema = datos.get("tema", "sistema")
        if tema in dict(TEMAS):
            self.tema = tema

        try:
            tope = int(datos.get("max_recientes", RECIENTES_POR_DEFECTO))
        except (TypeError, ValueError):
            tope = RECIENTES_POR_DEFECTO
        self.max_recientes = max(1, min(tope, TOPE_RECIENTES))

        try:
            guardados = int(datos.get("max_guardados", GUARDADOS_POR_DEFECTO))
        except (TypeError, ValueError):
            guardados = GUARDADOS_POR_DEFECTO
        self.max_guardados = max(0, min(guardados, self.max_recientes))
        carpeta = datos.get("carpeta_guardados") or ""
        self.carpeta_guardados = carpeta if isinstance(carpeta, str) else ""

        ext_defecto = self.extension or ".java"
        self.favoritos = self._migrar_grupos(datos.get("favoritos", []),
                                             ext_defecto, con_nombre=True)
        self.recientes = self._migrar_grupos(datos.get("recientes", []),
                                             ext_defecto, con_nombre=False)
        self.historial = [h for h in datos.get("historial", []) if isinstance(h, dict)]

        self._fusionar_favoritos_repetidos()
        self._deduplicar_recientes()
        antes = self._carpetas_guardadas()
        del self.recientes[self.max_recientes:]
        self._podar_guardados(antes)
        del self.historial[MAX_HISTORIAL:]

    def guardar(self):
        datos = {
            "version": VERSION_CONFIG,
            "extension": self.extension,
            "destino": self.destino,
            "abrir_al_terminar": self.abrir_al_terminar,
            "sustituir_al_cargar": self.sustituir_al_cargar,
            "max_recientes": self.max_recientes,
            "max_guardados": self.max_guardados,
            "carpeta_guardados": self.carpeta_guardados,
            "filtro_modo": self.filtro_modo,
            "tema": self.tema,
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
        """Acepta todos los formatos historicos y los deja como grupos v3.

        1. Cadena suelta con la ruta (lo mas viejo de todo).
        2. Dict con ruta + extension (formato 1).
        3. Dict con nombre + rutas (formato 2 y 3; el 2 no trae filtros).
        """
        grupos = []
        for elemento in bruto:
            if isinstance(elemento, str):
                if not elemento:
                    continue
                grupo = {"rutas": [{"ruta": elemento,
                                    "extensiones": [extension_defecto],
                                    "filtros": filtros_vacios()}]}
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
                    rutas.append({"ruta": entrada["ruta"], "extensiones": exts,
                                  "filtros": normalizar_filtros(entrada.get("filtros"))})
                if not rutas:
                    continue
                grupo = {"rutas": rutas}
                if con_nombre:
                    grupo["nombre"] = elemento.get("nombre") or resumen_rutas(rutas)
                else:
                    guardado = elemento.get("guardado")
                    if isinstance(guardado, dict) and guardado.get("carpeta"):
                        grupo["guardado"] = {
                            "carpeta": str(guardado["carpeta"]),
                            "fecha": str(guardado.get("fecha", "")),
                            "total": int(guardado.get("total") or 0),
                        }
                grupos.append(grupo)

            elif isinstance(elemento, dict) and elemento.get("ruta"):
                ext = normalizar_extension(elemento.get("extension", extension_defecto)) \
                    or extension_defecto
                grupo = {"rutas": [{"ruta": elemento["ruta"], "extensiones": [ext],
                                    "filtros": filtros_vacios()}]}
                if con_nombre:
                    grupo["nombre"] = elemento.get("nombre") or elemento["ruta"]
                grupos.append(grupo)

        return grupos

    def _fusionar_favoritos_repetidos(self):
        """Tras migrar del formato 1 puede haber varios favoritos con la misma
        ruta (uno por extension). Se unen en uno solo, sumando extensiones y
        conservando el nombre y los filtros del primero."""
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

    def _deduplicar_recientes(self):
        """Un config viejo puede traer la misma carpeta dos veces con distinta
        extension. Con la regla nueva es una sola fila: gana la mas reciente,
        que es la primera de la lista."""
        vistos = set()
        limpios = []
        for grupo in self.recientes:
            clave = clave_rutas(grupo["rutas"])
            if clave and clave not in vistos:
                vistos.add(clave)
                limpios.append(grupo)
        self.recientes = limpios

    # -- favoritos ----------------------------------------------------------
    #
    # La identidad de un favorito es el CONJUNTO DE RUTAS. Guardar un grupo
    # cuyas rutas ya existen sobrescribe el viejo por completo: extensiones y
    # filtros pasan a ser los nuevos, no se acumulan. Una ruta de mas o de
    # menos ya es otro favorito distinto.

    def buscar_favorito(self, rutas):
        clave = clave_rutas(rutas)
        for grupo in self.favoritos:
            if clave_rutas(grupo["rutas"]) == clave:
                return grupo
        return None

    def es_favorito_exacto(self, rutas):
        """True solo si coinciden rutas, extensiones y filtros."""
        clave = clave_completa(rutas)
        if not clave:
            return False
        return any(clave_completa(g["rutas"]) == clave for g in self.favoritos)

    def guardar_favorito(self, rutas, nombre):
        """Alta o sobrescritura. Devuelve el grupo guardado."""
        clave = clave_rutas(rutas)
        nuevo = {"nombre": nombre, "rutas": [copiar_entrada(r) for r in rutas]}

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
        """Una fila por CONJUNTO DE CARPETAS, aunque cambien las extensiones o
        los filtros. Repetir una extraccion sube su fila arriba con lo ultimo
        que se uso; no crea otra.

        Si la fila vieja tenia ficheros guardados, se los queda la nueva hasta
        que esta extraccion guarde los suyos. Asi, si falla o no copia nada, no
        se pierde la copia anterior de esas mismas carpetas.
        """
        clave = clave_rutas(rutas)
        antes = self._carpetas_guardadas()
        heredado = None
        restantes = []
        for grupo in self.recientes:
            if clave_rutas(grupo["rutas"]) == clave:
                heredado = heredado or grupo.get("guardado")
            else:
                restantes.append(grupo)
        nuevo = {"rutas": [copiar_entrada(r) for r in rutas]}
        if heredado:
            nuevo["guardado"] = heredado
        self.recientes = [nuevo] + restantes
        del self.recientes[self.max_recientes:]
        self._podar_guardados(antes)

    def recortar_recientes(self):
        antes = self._carpetas_guardadas()
        del self.recientes[self.max_recientes:]
        self.max_guardados = min(self.max_guardados, self.max_recientes)
        self._podar_guardados(antes)

    # -- ficheros guardados de las ultimas extracciones ------------------------
    #
    # Cada copia guardada cuelga de su reciente ("guardado": carpeta, fecha y
    # total). Solo conservan copia los max_guardados recientes mas nuevos, y
    # nunca hay mas guardados que recientes. Toda copia que deja de estar
    # referenciada se borra del disco en _podar_guardados.

    def almacen(self):
        return self.carpeta_guardados or almacen_por_defecto()

    def _carpetas_guardadas(self):
        return {g["guardado"]["carpeta"] for g in self.recientes if g.get("guardado")}

    def _podar_guardados(self, antes):
        """Quita la copia a los recientes que ya no caben y borra del disco
        todas las que estaban en 'antes' y ya no las referencia nadie."""
        for indice, grupo in enumerate(self.recientes):
            if indice >= self.max_guardados:
                grupo.pop("guardado", None)
        sobrantes = set(antes) - self._carpetas_guardadas()
        for carpeta in sobrantes:
            borrar_carpeta_guardada(carpeta)
        return sobrantes

    def cambiar_max_guardados(self, valor):
        antes = self._carpetas_guardadas()
        self.max_guardados = max(0, min(int(valor), self.max_recientes))
        self._podar_guardados(antes)

    def asignar_guardado(self, rutas, info):
        """Engancha una copia recien hecha a su reciente. Si ese reciente ya no
        tiene derecho a copia (por ejemplo, el contador esta en 0), la copia
        se borra en el acto."""
        antes = self._carpetas_guardadas() | {info["carpeta"]}
        clave = clave_rutas(rutas)
        for indice, grupo in enumerate(self.recientes):
            if clave_rutas(grupo["rutas"]) == clave and indice < self.max_guardados:
                grupo["guardado"] = info
                break
        self._podar_guardados(antes)

    def olvidar_guardado(self, grupo):
        """Para cuando la carpeta ya no existe: solo quita la referencia."""
        grupo.pop("guardado", None)

    # -- historial ----------------------------------------------------------

    def anadir_historial(self, total, rutas, destino):
        ahora = datetime.now()
        origenes = [r["ruta"] for r in rutas]
        self.historial.insert(0, {
            "fecha": ahora.strftime("%d/%m/%Y"),
            "hora": ahora.strftime("%H:%M:%S"),
            "extension": resumen_extensiones(rutas),
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

    La rueda del raton NO se gestiona aqui: la recoge la aplicacion con un
    unico manejador global (ver Aplicacion._rueda_global).
    """

    # El lienzo es un widget tk clasico, no ttk: no sigue a los estilos y hay
    # que repintarlo a mano al cambiar de tema. Por eso se lleva la cuenta.
    instancias = []

    def __init__(self, padre, **kwargs):
        super().__init__(padre, **kwargs)
        PanelDesplazable.instancias.append(self)

        self.lienzo = tk.Canvas(self, bg=P["fondo"], highlightthickness=0,
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
            self.barra.pack(side="right", fill="y", padx=(4, 0))
            self._barra_visible = True
        elif not hace_falta and self._barra_visible:
            self.barra.pack_forget()
            self._barra_visible = False
            self.lienzo.yview_moveto(0)

    # -- uso desde fuera ----------------------------------------------------

    def desplazar(self, pasos):
        if self._barra_visible:
            self.lienzo.yview_scroll(pasos, "units")

    def alto_contenido(self):
        return max(self.interior.winfo_reqheight(), 1)

    def alto_fila(self, por_defecto=48):
        """Alto de la primera fila con su separacion, para calcular cuantas caben."""
        hijos = self.interior.winfo_children()
        if not hijos:
            return por_defecto
        return max(hijos[0].winfo_reqheight(), 1) + 2 * PAD_FILA

    def fijar_alto(self, alto):
        self.lienzo.configure(height=max(int(alto), 1))

    def alto_fijado(self):
        try:
            return int(float(self.lienzo.cget("height")))
        except (TypeError, ValueError):
            return 1

    def vaciar(self):
        for hijo in self.interior.winfo_children():
            hijo.destroy()

    def repintar(self):
        self.lienzo.configure(bg=P["fondo"])

    @property
    def barra_visible(self):
        return self._barra_visible


# ---------------------------------------------------------------------------
# Ayuda emergente
# ---------------------------------------------------------------------------

class AyudaEmergente:
    """Recuadro que aparece al dejar el raton quieto sobre una tarjeta.

    Se usa para ver TODAS las rutas de un favorito o reciente, que en la
    tarjeta solo caben como 'primera ruta (+N)'. Un mismo objeto se vincula a
    la tarjeta y a sus hijos: al pasar de uno a otro, el Leave del primero y
    el Enter del segundo se compensan por el pequeno retardo al ocultar.
    """

    def __init__(self, app, propietario, texto):
        self.app = app
        self.propietario = propietario   # al destruirlo, la ayuda muere con el
        self.texto = texto
        self.ventana = None
        self._tarea = None

    def vincular(self, *widgets):
        for widget in widgets:
            widget.bind("<Enter>", self._entrar, add="+")
            widget.bind("<Leave>", self._salir, add="+")

    def _cancelar(self):
        if self._tarea is not None:
            try:
                self.app.after_cancel(self._tarea)
            except tk.TclError:
                pass
            self._tarea = None

    def _entrar(self, _evento=None):
        self._cancelar()
        if self.ventana is None:
            self._tarea = self.app.after(650, self._mostrar)

    def _salir(self, _evento=None):
        self._cancelar()
        self._tarea = self.app.after(80, self._ocultar)

    def _mostrar(self):
        self._tarea = None
        try:
            if not self.propietario.winfo_exists():
                return
        except tk.TclError:
            return
        x, y = self.app.winfo_pointerxy()
        ventana = tk.Toplevel(self.propietario)
        ventana.wm_overrideredirect(True)
        try:
            ventana.attributes("-topmost", True)
        except tk.TclError:
            pass
        tk.Label(ventana, text=self.texto, justify="left", bg=P["ayuda_fondo"],
                 fg=P["ayuda_texto"], relief="solid", bd=1, padx=8, pady=6,
                 highlightthickness=1, highlightbackground=P["borde"],
                 font=(FUENTE, 9)).pack()
        ventana.geometry("+%d+%d" % (x + 16, y + 14))
        self.ventana = ventana

    def _ocultar(self):
        self._tarea = None
        if self.ventana is not None:
            try:
                self.ventana.destroy()
            except tk.TclError:
                pass
            self.ventana = None


# ---------------------------------------------------------------------------
# Ventana de filtros de una carpeta
# ---------------------------------------------------------------------------

class VentanaFiltros(tk.Toplevel):
    """Dialogo modal con los filtros de UNA linea de origen.

    Tras cerrarse, self.resultado vale el dict de filtros elegido, o None si
    se ha cancelado. 'Quitar filtros' devuelve un dict vacio.
    """

    def __init__(self, padre, ruta, filtros):
        super().__init__(padre)
        self.resultado = None
        f = normalizar_filtros(filtros)

        self.title("Filtros de la carpeta")
        self.resizable(False, False)
        self.transient(padre)
        self.configure(bg=P["fondo"])

        marco = ttk.Frame(self, padding=16)
        marco.pack(fill="both", expand=True)
        marco.columnconfigure(1, weight=1)

        ttk.Label(marco, text="Filtros de esta carpeta",
                  font=(FUENTE, 11, "bold")).grid(row=0, column=0, columnspan=3,
                                                  sticky="w")
        ttk.Label(marco, text=acortar(ruta or "(sin carpeta todavia)", 64),
                  style="Suave.TLabel").grid(row=1, column=0, columnspan=3,
                                               sticky="w", pady=(2, 12))

        # --- Tamano ---------------------------------------------------------
        ttk.Label(marco, text="Tamano",
                  font=(FUENTE, 10, "bold")).grid(row=2, column=0, sticky="w")

        self.var_min = tk.StringVar(value=formatear_numero(f["min_kb"]))
        self.var_max = tk.StringVar(value=formatear_numero(f["max_kb"]))

        fila_tam = ttk.Frame(marco)
        fila_tam.grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 12))
        ttk.Label(fila_tam, text="Minimo").pack(side="left")
        ttk.Entry(fila_tam, textvariable=self.var_min, width=9).pack(side="left",
                                                                     padx=(6, 4))
        ttk.Label(fila_tam, text="KB").pack(side="left", padx=(0, 18))
        ttk.Label(fila_tam, text="Maximo").pack(side="left")
        ttk.Entry(fila_tam, textvariable=self.var_max, width=9).pack(side="left",
                                                                     padx=(6, 4))
        ttk.Label(fila_tam, text="KB").pack(side="left")

        # --- Nombre ---------------------------------------------------------
        ttk.Label(marco, text="El nombre contiene",
                  font=(FUENTE, 10, "bold")).grid(row=4, column=0, sticky="w")
        self.var_contiene = tk.StringVar(value=f["contiene"])
        ttk.Entry(marco, textvariable=self.var_contiene, width=34).grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=(4, 12))

        # --- Muestra aleatoria -----------------------------------------------
        ttk.Label(marco, text="Muestra aleatoria",
                  font=(FUENTE, 10, "bold")).grid(row=6, column=0, sticky="w")

        fila_azar = ttk.Frame(marco)
        fila_azar.grid(row=7, column=0, columnspan=3, sticky="w", pady=(4, 4))

        self.var_azar_modo = tk.StringVar(value=dict(MODOS_AZAR)[f["azar_modo"]])
        self.var_azar_valor = tk.StringVar(
            value=str(f["azar_valor"]) if f["azar_modo"] else "")
        self.combo_azar = ttk.Combobox(
            fila_azar, textvariable=self.var_azar_modo, state="readonly",
            values=[texto for _, texto in MODOS_AZAR], width=20)
        self.combo_azar.pack(side="left")
        self.entrada_azar = ttk.Entry(fila_azar, textvariable=self.var_azar_valor,
                                      width=7)
        self.entrada_azar.pack(side="left", padx=(8, 4))
        self.etiqueta_unidad = ttk.Label(fila_azar, text="")
        self.etiqueta_unidad.pack(side="left")
        self.combo_azar.bind("<<ComboboxSelected>>", lambda _e: self._refrescar_azar())
        self._refrescar_azar()

        ttk.Label(marco,
                  text="Se aplican tras la extension y el filtro global de nombre.\n"
                       "La muestra aleatoria va la ultima, sobre lo que quede.",
                  style="Suave.TLabel", justify="left").grid(
                      row=8, column=0, columnspan=3, sticky="w", pady=(8, 14))

        # --- Botones --------------------------------------------------------
        botones = ttk.Frame(marco)
        botones.grid(row=9, column=0, columnspan=3, sticky="ew")
        ttk.Button(botones, text="Quitar filtros",
                   command=self._quitar).pack(side="left")
        ttk.Button(botones, text="Aceptar",
                   command=self._aceptar).pack(side="right")
        ttk.Button(botones, text="Cancelar",
                   command=self.destroy).pack(side="right", padx=(0, 6))

        self.bind("<Return>", lambda _e: self._aceptar())
        self.bind("<Escape>", lambda _e: self.destroy())

        self.update_idletasks()
        x = padre.winfo_rootx() + (padre.winfo_width() - self.winfo_reqwidth()) // 2
        y = padre.winfo_rooty() + 80
        self.geometry("+%d+%d" % (max(x, 0), max(y, 0)))
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def _modo_azar(self):
        texto = self.var_azar_modo.get()
        for clave, etiqueta in MODOS_AZAR:
            if etiqueta == texto:
                return clave
        return ""

    def _refrescar_azar(self):
        modo = self._modo_azar()
        if modo == "numero":
            self.entrada_azar.config(state="normal")
            self.etiqueta_unidad.config(text="ficheros")
        elif modo == "porcentaje":
            self.entrada_azar.config(state="normal")
            self.etiqueta_unidad.config(text="%")
        else:
            self.var_azar_valor.set("")
            self.entrada_azar.config(state="disabled")
            self.etiqueta_unidad.config(text="")

    def _error(self, texto):
        messagebox.showerror(TITULO, texto, parent=self)

    def _aceptar(self):
        try:
            minimo = leer_numero(self.var_min.get())
            maximo = leer_numero(self.var_max.get())
        except ValueError:
            self._error("El tamano tiene que ser un numero, por ejemplo 500 o 1,5.")
            return
        if (minimo is not None and minimo < 0) or (maximo is not None and maximo < 0):
            self._error("El tamano no puede ser negativo.")
            return
        if minimo is not None and maximo is not None and minimo > maximo:
            self._error("El tamano minimo no puede ser mayor que el maximo.")
            return

        modo = self._modo_azar()
        valor = 0
        if modo:
            texto = self.var_azar_valor.get().strip()
            if not texto.isdigit():
                self._error("La cantidad de la muestra tiene que ser un numero entero.")
                return
            valor = int(texto)
            if modo == "numero" and valor < 1:
                self._error("Hay que sacar al menos 1 fichero.")
                return
            if modo == "porcentaje" and not 1 <= valor <= 100:
                self._error("El porcentaje tiene que estar entre 1 y 100.")
                return

        self.resultado = normalizar_filtros({
            "min_kb": minimo, "max_kb": maximo,
            "contiene": self.var_contiene.get(),
            "azar_modo": modo, "azar_valor": valor,
        })
        self.destroy()

    def _quitar(self):
        self.resultado = filtros_vacios()
        self.destroy()


# ---------------------------------------------------------------------------
# Ventana de historial
# ---------------------------------------------------------------------------

class VentanaContenido(tk.Toplevel):
    """Lista de los ficheros de una extraccion guardada.

    Se rellena con el marcador que ExtractJ deja dentro de cada copia, que
    recuerda de que carpeta original salio cada fichero.
    """

    def __init__(self, padre, carpeta, datos):
        super().__init__(padre)
        self.carpeta = carpeta

        self.title(TITULO + " - Ficheros guardados")
        self.geometry("900x480")
        self.minsize(640, 320)
        self.transient(padre)
        self.configure(bg=P["fondo"])

        marco = ttk.Frame(self, padding=14)
        marco.pack(fill="both", expand=True)

        ficheros = datos.get("ficheros") or []
        rutas = datos.get("rutas") or []

        ttk.Label(marco, text="Extraccion del %s" % datos.get("fecha", "?"),
                  style="Seccion.TLabel").pack(anchor="w")
        resumen = "%d ficheros   \u00b7   %s   \u00b7   %d carpeta(s) de origen" % (
            len(ficheros), resumen_extensiones(rutas) or TEXTO_TODOS, len(rutas))
        ttk.Label(marco, text=resumen, style="Suave.TLabel").pack(anchor="w", pady=(2, 0))
        ttk.Label(marco, text="Guardado en: " + acortar(carpeta, 100),
                  style="Suave.TLabel").pack(anchor="w", pady=(2, 10))

        pie = ttk.Frame(marco)
        pie.pack(side="bottom", fill="x", pady=(10, 0))
        ttk.Button(pie, text="Cerrar", command=self.destroy).pack(side="right")
        ttk.Button(pie, text="Abrir la carpeta",
                   command=self._abrir).pack(side="right", padx=(0, 6))

        columnas = ("nombre", "origen", "tamano")
        tabla = ttk.Treeview(marco, columns=columnas, show="headings")
        for clave, texto, ancho, alineacion in (
                ("nombre", "Fichero", 230, "w"),
                ("origen", "Carpeta de origen", 520, "w"),
                ("tamano", "Tamano", 90, "e")):
            tabla.heading(clave, text=texto)
            tabla.column(clave, width=ancho, anchor=alineacion)
        barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        tabla.pack(side="left", fill="both", expand=True)

        for fichero in sorted(ficheros, key=lambda f: str(f.get("nombre", "")).lower()):
            tabla.insert("", "end", values=(
                fichero.get("nombre", ""),
                os.path.dirname(str(fichero.get("origen", ""))),
                formatear_tamano(fichero.get("bytes")),
            ))

    def _abrir(self):
        if not abrir_carpeta(self.carpeta):
            messagebox.showerror(TITULO, "No se ha podido abrir la carpeta:\n%s"
                                 % self.carpeta, parent=self)


class VentanaHistorial(tk.Toplevel):

    def __init__(self, padre, config):
        super().__init__(padre)
        self.config_app = config

        self.title(TITULO + " - Historial")
        self.geometry("920x440")
        self.minsize(640, 300)
        self.transient(padre)
        self.configure(bg=P["fondo"])

        marco = ttk.Frame(self, padding=12)
        marco.pack(fill="both", expand=True)

        columnas = ("fecha", "hora", "tipo", "total", "origen", "destino")
        self.tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=14)

        cabeceras = {
            "fecha": ("Fecha", 90, "center"),
            "hora": ("Hora", 80, "center"),
            "tipo": ("Tipo", 110, "center"),
            "total": ("Ficheros", 70, "center"),
            "origen": ("Origen", 290, "w"),
            "destino": ("Destino", 250, "w"),
        }
        for clave, (texto, ancho, alineacion) in cabeceras.items():
            self.tabla.heading(clave, text=texto)
            self.tabla.column(clave, width=ancho, anchor=alineacion)

        barra = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)

        pie = ttk.Frame(marco)
        pie.pack(side="bottom", fill="x", pady=(10, 0))
        barra.pack(side="right", fill="y")
        self.tabla.pack(side="left", fill="both", expand=True)

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

        self._ancho_fijado = False

        # Extensiones que la global escribio en las lineas la ultima vez que se
        # aplico. Al arrancar no se ha aplicado nada, aunque el campo traiga
        # un valor guardado del config.
        self._global_aplicada = []
        self._tarea_global = None

        # Cada linea de origen es un dict: marco, StringVar de ruta y de
        # extensiones, dict de filtros y la etiqueta que los resume.
        self.lineas = []

        self.title(TITULO)
        self.minsize(ANCHO_MINIMO, ALTO_MINIMO)

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
        self.var_max_guardados = tk.StringVar(value=str(self.config_app.max_guardados))
        self.var_tema = tk.StringVar(value=dict(TEMAS)[self.config_app.tema])
        self._tema_aplicado = None

        # El tema se aplica ANTES de construir nada, para que todo nazca ya
        # con sus colores y no haya un parpadeo en claro al arrancar.
        self.estilo = ttk.Style(self)
        try:
            self.estilo.theme_use("clam")
        except tk.TclError:
            pass
        self._aplicar_tema(repintar=False)
        self._construir_interfaz()
        self._anadir_linea()
        self._refrescar_favoritos()
        self._refrescar_recientes()

        # Un solo manejador de rueda para los tres paneles: mira que hay bajo
        # el puntero y desplaza el panel que lo contiene.
        self.bind_all("<MouseWheel>", self._rueda_global)
        self.bind_all("<Button-4>", self._rueda_global)    # Linux
        self.bind_all("<Button-5>", self._rueda_global)

        # Cualquier Toplevel que se abra (filtros, historial, el dialogo de
        # nombre de favorito) recibe la barra de titulo del tema al mostrarse.
        self.bind_class("Toplevel", "<Map>", self._al_mostrar_toplevel, add="+")
        self.after(50, lambda: pintar_barra_titulo(self, self._tema_aplicado == "oscuro"))
        self.after(SEGUNDOS_VIGILAR_SISTEMA * 1000, self._vigilar_tema_sistema)

        self.protocol("WM_DELETE_WINDOW", self._cerrar)

    # -- estilos ------------------------------------------------------------

    def _tema_efectivo(self):
        """'claro' u 'oscuro': resuelve 'sistema' leyendo Windows."""
        if self.config_app.tema == "sistema":
            return tema_de_windows()
        return self.config_app.tema

    def _aplicar_tema(self, repintar=True):
        """Carga la paleta del tema efectivo y repinta lo que haga falta.

        Los widgets ttk se actualizan solos al reconfigurar sus estilos. Lo que
        NO es ttk hay que tocarlo a mano: la ventana raiz, los lienzos de los
        paneles, las estrellas de recientes y los Toplevel abiertos.
        """
        nombre = self._tema_efectivo()
        P.clear()
        P.update(PALETAS[nombre])
        self._tema_aplicado = nombre

        self.configure(bg=P["fondo"])
        self._configurar_estilos()
        self._opciones_tk_clasico()

        if not repintar:
            return
        for panel in list(PanelDesplazable.instancias):
            try:
                panel.repintar()
            except tk.TclError:
                PanelDesplazable.instancias.remove(panel)
        self._refrescar_recientes()          # las estrellas son tk.Button
        pintar_barra_titulo(self, nombre == "oscuro")
        for hijo in self.winfo_children():
            if isinstance(hijo, tk.Toplevel) and not hijo.overrideredirect():
                hijo.configure(bg=P["fondo"])
                pintar_barra_titulo(hijo, nombre == "oscuro")

    def _opciones_tk_clasico(self):
        """Colores por defecto para widgets tk clasicos que crea tkinter por su
        cuenta: el dialogo de simpledialog (nombre de favorito) y la lista
        desplegable de los Combobox. Solo afecta a los que se creen despues,
        que es justo lo que se quiere: se crean al abrirlos."""
        opciones = {
            "*Background": P["fondo"],
            "*Foreground": P["texto"],
            "*highlightBackground": P["fondo"],
            "*Entry.Background": P["campo"],
            "*Entry.Foreground": P["texto"],
            "*Entry.insertBackground": P["texto"],
            "*Entry.selectBackground": P["seleccion"],
            "*Entry.selectForeground": P["seleccion_texto"],
            "*Button.Background": P["boton"],
            "*Button.Foreground": P["texto"],
            "*Button.activeBackground": P["boton_activo"],
            "*Button.activeForeground": P["texto"],
            "*TCombobox*Listbox.background": P["campo"],
            "*TCombobox*Listbox.foreground": P["texto"],
            "*TCombobox*Listbox.selectBackground": P["seleccion"],
            "*TCombobox*Listbox.selectForeground": P["seleccion_texto"],
        }
        for patron, valor in opciones.items():
            self.option_add(patron, valor)

    def _cambiar_tema(self, _evento=None):
        texto = self.var_tema.get()
        for clave, etiqueta in TEMAS:
            if etiqueta == texto:
                self.config_app.tema = clave
        self.config_app.guardar()
        self._aplicar_tema()

    def _vigilar_tema_sistema(self):
        """En modo Sistema, mira cada pocos segundos si Windows ha cambiado.

        Windows no avisa a Tk del cambio de tema, asi que se sondea. Leer una
        clave del registro cuesta microsegundos; no se nota.
        """
        try:
            if (self.config_app.tema == "sistema"
                    and tema_de_windows() != self._tema_aplicado):
                self._aplicar_tema()
        finally:
            self.after(SEGUNDOS_VIGILAR_SISTEMA * 1000, self._vigilar_tema_sistema)

    def _al_mostrar_toplevel(self, evento):
        ventana = evento.widget
        if not isinstance(ventana, tk.Toplevel):
            return
        try:
            if ventana.overrideredirect():       # ayudas emergentes: sin barra
                return
        except tk.TclError:
            return
        pintar_barra_titulo(ventana, self._tema_aplicado == "oscuro")

    def _configurar_estilos(self):
        """Todos los estilos ttk a partir de la paleta activa P.

        Se puede llamar las veces que haga falta: reconfigurar un estilo
        repinta al momento todos los widgets que lo usan.
        """
        e = self.estilo

        # -- base --------------------------------------------------------------
        e.configure(".", font=(FUENTE, 10), background=P["fondo"],
                    foreground=P["texto"], bordercolor=P["borde"],
                    troughcolor=P["canal"], focuscolor=P["acento"],
                    selectbackground=P["seleccion"],
                    selectforeground=P["seleccion_texto"],
                    insertcolor=P["texto"], fieldbackground=P["campo"])
        e.map(".", foreground=[("disabled", P["desactivado"])])
        e.configure("TFrame", background=P["fondo"])
        e.configure("TLabel", background=P["fondo"], foreground=P["texto"])
        e.configure("TSeparator", background=P["borde"])
        self.color_marco = P["fondo"]

        # -- botones -----------------------------------------------------------
        # En clam, lightcolor/darkcolor son el biselado 3D. Igualarlos al fondo
        # del boton lo deja plano, que encaja mejor con las tarjetas.
        e.configure("TButton", background=P["boton"], foreground=P["texto"],
                    bordercolor=P["boton_borde"], lightcolor=P["boton"],
                    darkcolor=P["boton"], focuscolor=P["boton"])
        e.map("TButton",
              background=[("disabled", P["campo_off"]), ("pressed", P["boton_pulsado"]),
                          ("active", P["boton_activo"])],
              lightcolor=[("pressed", P["boton_pulsado"]), ("active", P["boton_activo"])],
              darkcolor=[("pressed", P["boton_pulsado"]), ("active", P["boton_activo"])],
              foreground=[("disabled", P["desactivado"])])

        e.configure("Nombre.TButton", anchor="w", font=(FUENTE, 10, "bold"),
                    padding=(8, 3), width=0)
        e.configure("Ruta.TButton", anchor="w", padding=(8, 3), width=0)
        # clam impone a TButton un ancho minimo de 11 caracteres; en los
        # botones pequenos eso los vuelve enormes y estruja las rutas.
        e.configure("Pequeno.TButton", padding=(7, 2), font=(FUENTE, 9), width=0)
        e.configure("Barra.TButton", padding=(9, 3), width=0)

        e.configure("Principal.TButton", font=(FUENTE, 11, "bold"), padding=(10, 8),
                    background=P["acento"], foreground=P["acento_texto"],
                    bordercolor=P["acento"], lightcolor=P["acento"],
                    darkcolor=P["acento"], focuscolor=P["acento"])
        e.map("Principal.TButton",
              background=[("disabled", P["campo_off"]), ("pressed", P["acento"]),
                          ("active", P["acento_activo"])],
              lightcolor=[("active", P["acento_activo"])],
              darkcolor=[("active", P["acento_activo"])],
              foreground=[("disabled", P["desactivado"])])

        # -- campos de texto ---------------------------------------------------
        campos = dict(fieldbackground=P["campo"], foreground=P["texto"],
                      bordercolor=P["campo_borde"], lightcolor=P["campo"],
                      darkcolor=P["campo"], insertcolor=P["texto"],
                      selectbackground=P["seleccion"],
                      selectforeground=P["seleccion_texto"])
        mapa_campos = dict(
            fieldbackground=[("disabled", P["campo_off"]), ("readonly", P["campo"])],
            bordercolor=[("focus", P["acento"])],
            lightcolor=[("focus", P["acento"])],
            foreground=[("disabled", P["desactivado"])])
        e.configure("TEntry", **campos)
        e.map("TEntry", **mapa_campos)

        # Combobox y Spinbox de solo lectura: sin esto clam resalta el texto
        # como si estuviera seleccionado al darles el foco.
        for clase in ("TCombobox", "TSpinbox"):
            e.configure(clase, background=P["boton"], arrowcolor=P["texto"], **campos)
            e.map(clase,
                  selectbackground=[("readonly", P["campo"])],
                  selectforeground=[("readonly", P["texto"])],
                  background=[("active", P["boton_activo"]), ("pressed", P["boton_pulsado"])],
                  arrowcolor=[("disabled", P["desactivado"])],
                  **mapa_campos)

        # -- casillas ----------------------------------------------------------
        e.configure("TCheckbutton", background=P["fondo"], foreground=P["texto"],
                    indicatorbackground=P["campo"], indicatorforeground=P["texto"],
                    focuscolor=P["fondo"])
        e.map("TCheckbutton",
              background=[("active", P["fondo"])],
              indicatorbackground=[("pressed", P["boton_pulsado"]),
                                   ("active", P["campo"])])

        # -- barras ------------------------------------------------------------
        for orientacion in ("Vertical", "Horizontal"):
            e.configure("%s.TScrollbar" % orientacion, background=P["boton"],
                        troughcolor=P["fondo"], bordercolor=P["fondo"],
                        lightcolor=P["boton"], darkcolor=P["boton"],
                        arrowcolor=P["suave"])
            e.map("%s.TScrollbar" % orientacion,
                  background=[("pressed", P["boton_pulsado"]),
                              ("active", P["boton_activo"])],
                  lightcolor=[("active", P["boton_activo"])],
                  darkcolor=[("active", P["boton_activo"])])
        e.configure("Horizontal.TProgressbar", background=P["acento"],
                    troughcolor=P["canal"], bordercolor=P["borde"],
                    lightcolor=P["acento"], darkcolor=P["acento"])

        # -- tabla del historial -----------------------------------------------
        e.configure("Treeview", background=P["tarjeta"], fieldbackground=P["tarjeta"],
                    foreground=P["texto"], bordercolor=P["borde"],
                    lightcolor=P["tarjeta"], darkcolor=P["tarjeta"])
        e.map("Treeview", background=[("selected", P["seleccion"])],
              foreground=[("selected", P["seleccion_texto"])])
        e.configure("Treeview.Heading", background=P["boton"], foreground=P["texto"],
                    bordercolor=P["borde"], lightcolor=P["boton"], darkcolor=P["boton"])
        e.map("Treeview.Heading", background=[("active", P["boton_activo"])])

        # -- textos ------------------------------------------------------------
        e.configure("Titulo.TLabel", font=(FUENTE, 15, "bold"))
        e.configure("Seccion.TLabel", font=(FUENTE, 11, "bold"))
        e.configure("Suave.TLabel", foreground=P["suave"])
        e.configure("Estado.TLabel", foreground=P["estado"])
        e.configure("Contador.TLabel", foreground=P["muy_suave"], font=(FUENTE, 10))

        # -- tarjetas ----------------------------------------------------------
        # Fondo propio con borde fino: es lo que separa visualmente cada
        # favorito, reciente o linea de origen.
        e.configure("Tarjeta.TFrame", background=P["tarjeta"],
                    bordercolor=P["borde"], lightcolor=P["borde"],
                    darkcolor=P["borde"], relief="solid", borderwidth=1)
        e.configure("Tarjeta.TLabel", background=P["tarjeta"], foreground=P["texto"])
        e.configure("TarjetaNumero.TLabel", background=P["tarjeta"],
                    foreground=P["muy_suave"], font=(FUENTE, 10, "bold"))
        e.configure("TarjetaSuave.TLabel", background=P["tarjeta"],
                    foreground=P["suave"], font=(FUENTE, 9))
        e.configure("TarjetaVacia.TLabel", background=P["tarjeta"],
                    foreground=P["muy_suave"], font=(FUENTE, 9))
        e.configure("TarjetaFiltro.TLabel", background=P["tarjeta"],
                    foreground=P["filtro"], font=(FUENTE, 9))

    # -- construccion de la interfaz ---------------------------------------

    def _construir_interfaz(self):
        raiz = ttk.Frame(self, padding=(18, 14, 18, 14))
        raiz.pack(fill="both", expand=True)
        self.marco_raiz = raiz

        # El bloque inferior se empaqueta ANTES que el central: asi pack le
        # reserva su sitio y el boton Extraer nunca queda tapado por muchas
        # lineas, favoritos o recientes que haya.
        superior = ttk.Frame(raiz)
        superior.pack(side="top", fill="x")
        superior.columnconfigure(0, weight=1)

        inferior = ttk.Frame(raiz)
        inferior.pack(side="bottom", fill="x", pady=(14, 0))
        inferior.columnconfigure(0, weight=1)

        medio = ttk.Frame(raiz)
        medio.pack(side="top", fill="both", expand=True, pady=(14, 0))

        self._construir_cabecera(superior)
        self._construir_medio(medio)
        self._construir_inferior(inferior)

    def _construir_cabecera(self, padre):
        cabecera = ttk.Frame(padre)
        cabecera.grid(row=0, column=0, sticky="ew")
        cabecera.columnconfigure(0, weight=1)

        ttk.Label(cabecera, text=TITULO,
                  style="Titulo.TLabel").grid(row=0, column=0, sticky="w")

        ttk.Label(cabecera, text="Tema", style="Suave.TLabel").grid(
            row=0, column=1, padx=(0, 6))
        self.combo_tema = ttk.Combobox(
            cabecera, textvariable=self.var_tema, state="readonly",
            values=[texto for _, texto in TEMAS], width=9)
        self.combo_tema.grid(row=0, column=2, padx=(0, 14))
        self.combo_tema.bind("<<ComboboxSelected>>", self._cambiar_tema)

        ttk.Button(cabecera, text="Historial",
                   command=self._abrir_historial).grid(row=0, column=3, sticky="e")

        ttk.Separator(padre).grid(row=1, column=0, sticky="ew", pady=(10, 12))

        # Las dos opciones globales en una sola franja: aplican a TODAS las
        # lineas, por eso van fuera de las columnas.
        opciones = ttk.Frame(padre)
        opciones.grid(row=2, column=0, sticky="ew")
        opciones.columnconfigure(5, weight=1)
        opciones.columnconfigure(7, weight=1)

        ttk.Label(opciones, text="Extension global").grid(row=0, column=0, sticky="w")
        ttk.Entry(opciones, textvariable=self.var_extension,
                  width=14).grid(row=0, column=1, padx=(8, 0))

        ttk.Separator(opciones, orient="vertical").grid(row=0, column=2, sticky="ns",
                                                        padx=18)

        ttk.Label(opciones, text="Filtro global de nombre").grid(row=0, column=3)
        self.combo_modo = ttk.Combobox(
            opciones, textvariable=self.var_modo_filtro, state="readonly",
            values=[texto for _, texto in MODOS_FILTRO], width=12)
        self.combo_modo.grid(row=0, column=4, padx=(8, 6))
        ttk.Entry(opciones, textvariable=self.var_incluir).grid(
            row=0, column=5, sticky="ew")
        ttk.Label(opciones, text="Excluir").grid(row=0, column=6, padx=(14, 6))
        ttk.Entry(opciones, textvariable=self.var_excluir).grid(
            row=0, column=7, sticky="ew")

        ttk.Label(opciones, text="Al modificarla se escribe en todas las lineas",
                  style="Suave.TLabel").grid(row=1, column=0, columnspan=2,
                                             sticky="w", pady=(3, 0))
        ttk.Label(opciones,
                  text="Contra el nombre sin extension, sin distinguir mayusculas",
                  style="Suave.TLabel").grid(row=1, column=3, columnspan=5,
                                             sticky="w", pady=(3, 0))

    def _construir_medio(self, padre):
        # Dos columnas. Izquierda: lo que se esta editando (origen) y, debajo,
        # lo que se ha extraido antes (recientes). Derecha: favoritos con todo
        # el alto, que es la lista que mas crece.
        padre.columnconfigure(0, weight=11, uniform="columnas")
        padre.columnconfigure(1, weight=9, uniform="columnas")
        padre.rowconfigure(0, weight=1)

        izquierda = ttk.Frame(padre)
        izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        derecha = ttk.Frame(padre)
        derecha.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self.columna_izquierda = izquierda
        self.columna_derecha = derecha

        # Recientes se empaqueta antes que origen, anclado abajo, para que el
        # panel de origen pueda expandirse en el hueco que quede.
        self._construir_recientes(izquierda)
        self._construir_origen(izquierda)
        self._construir_favoritos(derecha)

    def _construir_origen(self, padre):
        titulo = ttk.Frame(padre)
        titulo.pack(side="top", fill="x", pady=(0, 6))

        ttk.Label(titulo, text="Carpetas de origen",
                  style="Seccion.TLabel").pack(side="left")
        self.etiqueta_num_lineas = ttk.Label(titulo, text="", style="Contador.TLabel")
        self.etiqueta_num_lineas.pack(side="left", padx=(6, 0))

        self.boton_favorito = ttk.Button(titulo, text="\u2606 Guardar favorito",
                                         style="Barra.TButton",
                                         command=self._alternar_favorito_actual)
        self.boton_favorito.pack(side="right")
        ttk.Button(titulo, text="Limpiar", style="Barra.TButton",
                   command=self._limpiar_lineas).pack(side="right", padx=(0, 6))
        ttk.Button(titulo, text="+ Anadir carpeta", style="Barra.TButton",
                   command=self._anadir_linea).pack(side="right", padx=(0, 6))

        ttk.Label(padre,
                  text="Extensiones separadas por espacios: .java .jsp .css   "
                       "\u00b7   Vacio = todos los tipos",
                  style="Suave.TLabel").pack(side="bottom", anchor="w", pady=(6, 0))

        self.panel_origen = PanelDesplazable(padre)
        self.panel_origen.pack(side="top", fill="both", expand=True)

    def _construir_favoritos(self, padre):
        titulo = ttk.Frame(padre)
        titulo.pack(side="top", fill="x", pady=(0, 6))
        ttk.Label(titulo, text="Favoritos",
                  style="Seccion.TLabel").pack(side="left")
        self.etiqueta_num_favoritos = ttk.Label(titulo, text="",
                                                style="Contador.TLabel")
        self.etiqueta_num_favoritos.pack(side="left", padx=(6, 0))
        ttk.Checkbutton(titulo, text="Sustituir al cargar",
                        variable=self.var_sustituir,
                        command=self._cambiar_modo_carga).pack(side="right")

        busqueda = ttk.Frame(padre)
        busqueda.pack(side="top", fill="x", pady=(0, 6))
        ttk.Label(busqueda, text="Buscar").pack(side="left")
        self.entrada_busqueda = ttk.Entry(busqueda, textvariable=self.var_busqueda_fav)
        self.entrada_busqueda.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.var_busqueda_fav.trace_add("write",
                                        lambda *_: self._refrescar_favoritos())

        self.panel_favoritos = PanelDesplazable(padre)
        self.panel_favoritos.pack(side="top", fill="both", expand=True)

    def _construir_recientes(self, padre):
        # Orden inverso a proposito: todo esto va con side="bottom".
        self.panel_recientes = PanelDesplazable(padre)
        self.panel_recientes.pack(side="bottom", fill="x")

        almacen = ttk.Frame(padre)
        almacen.pack(side="bottom", fill="x", pady=(0, 6))
        self.etiqueta_almacen = ttk.Label(almacen, text="", style="Suave.TLabel")
        self.etiqueta_almacen.pack(side="left")
        ttk.Button(almacen, text="Cambiar...", style="Pequeno.TButton",
                   command=self._elegir_almacen).pack(side="right")

        titulo = ttk.Frame(padre)
        titulo.pack(side="bottom", fill="x", pady=(16, 4))
        ttk.Label(titulo, text="Recientes",
                  style="Seccion.TLabel").pack(side="left")

        ttk.Spinbox(titulo, from_=0, to=TOPE_RECIENTES, width=4,
                    textvariable=self.var_max_guardados, state="readonly",
                    command=self._cambiar_max_guardados).pack(side="right")
        ttk.Label(titulo, text="Guardar ficheros de",
                  style="Suave.TLabel").pack(side="right", padx=(0, 6))
        ttk.Spinbox(titulo, from_=1, to=TOPE_RECIENTES, width=4,
                    textvariable=self.var_max_recientes, state="readonly",
                    command=self._cambiar_max_recientes).pack(side="right", padx=(0, 16))
        ttk.Label(titulo, text="Recordar",
                  style="Suave.TLabel").pack(side="right", padx=(0, 6))

        self._pintar_almacen()

    def _construir_inferior(self, padre):
        ttk.Separator(padre).grid(row=0, column=0, sticky="ew", pady=(0, 12))

        fila_destino = ttk.Frame(padre)
        fila_destino.grid(row=1, column=0, sticky="ew")
        fila_destino.columnconfigure(1, weight=1)

        ttk.Label(fila_destino, text="Destino",
                  style="Seccion.TLabel").grid(row=0, column=0, padx=(0, 10))
        ttk.Entry(fila_destino,
                  textvariable=self.var_destino).grid(row=0, column=1, sticky="ew")
        ttk.Button(fila_destino, text="Examinar...",
                   command=self._elegir_destino).grid(row=0, column=2, padx=(6, 0))

        fila_info = ttk.Frame(padre)
        fila_info.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        self.etiqueta_destino_final = ttk.Label(fila_info, text="",
                                                style="Suave.TLabel")
        self.etiqueta_destino_final.pack(side="left")
        ttk.Checkbutton(fila_info, text="Abrir la carpeta al terminar",
                        variable=self.var_abrir,
                        command=self._cambiar_abrir).pack(side="right")

        # La extension global solo actua cuando se MODIFICA su campo: entonces
        # se escribe en todas las lineas. Cargar un favorito, anadir una linea
        # o arrancar el programa no la aplican.
        self.var_extension.trace_add("write", lambda *_: self._programar_global())
        self.var_destino.trace_add("write", lambda *_: self._refrescar_destino_final())

        fila_progreso = ttk.Frame(padre)
        fila_progreso.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        fila_progreso.columnconfigure(1, weight=1)

        ttk.Label(fila_progreso, textvariable=self.var_estado,
                  style="Estado.TLabel", width=40).grid(row=0, column=0, sticky="w")
        self.barra = ttk.Progressbar(fila_progreso, mode="determinate", maximum=100)
        self.barra.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        ttk.Label(fila_progreso, textvariable=self.var_contador,
                  width=12, anchor="e").grid(row=0, column=2, padx=(8, 0))

        self.boton_extraer = ttk.Button(padre, text="Extraer ficheros",
                                        style="Principal.TButton",
                                        command=self._iniciar_extraccion)
        self.boton_extraer.grid(row=4, column=0, sticky="ew", pady=(12, 0))

    # -- rueda del raton ----------------------------------------------------

    def _rueda_global(self, evento):
        """Desplaza el panel que hay bajo el puntero, si lo hay.

        Antes cada panel enlazaba la rueda al entrar en su lienzo y la soltaba
        al salir. Pero Tk tambien genera <Leave> al pasar del lienzo a una de
        sus filas, asi que encima de las filas la rueda dejaba de responder.
        """
        try:
            widget = self.winfo_containing(evento.x_root, evento.y_root)
        except (KeyError, tk.TclError):
            return
        while widget is not None:
            if isinstance(widget, PanelDesplazable):
                if getattr(evento, "num", None) == 4:
                    pasos = -1
                elif getattr(evento, "num", None) == 5:
                    pasos = 1
                else:
                    pasos = -1 * int(evento.delta / 120) if evento.delta else 0
                if pasos:
                    widget.desplazar(pasos)
                return
            widget = getattr(widget, "master", None)

    # -- altura de la ventana -----------------------------------------------

    def _ajustar_altura(self):
        """Ajusta el alto de la ventana al contenido, con tope y scroll.

        Con dos columnas, el alto de la ventana lo marca la columna MAS ALTA.
        Cada panel pide lo que ocupa su contenido, limitado por su maximo de
        filas. Si aun asi se pasa del tope de pantalla, se recorta cada
        columna por separado hasta el mismo objetivo: a la izquierda las
        recientes y luego las lineas de origen; a la derecha, favoritos.
        """
        self.update_idletasks()

        topes = [
            (self.panel_origen, FILAS_MAX_ORIGEN),
            (self.panel_favoritos, FILAS_MAX_FAVORITOS),
            (self.panel_recientes, self.config_app.max_recientes),
        ]
        for panel, filas_max in topes:
            tope = panel.alto_fila() * max(filas_max, 1) + 4
            panel.fijar_alto(max(min(panel.alto_contenido() + 2, tope),
                                 ALTO_MINIMO_PANEL))

        self.update_idletasks()
        alto_max = int(self.winfo_screenheight() * FRACCION_ALTO_MAX)
        alto_pedido = self.winfo_reqheight()

        if alto_pedido > alto_max:
            exceso = alto_pedido - alto_max
            izq = self.columna_izquierda.winfo_reqheight()
            der = self.columna_derecha.winfo_reqheight()
            objetivo = max(izq, der) - exceso

            # Primera pasada: nadie baja de 2 filas. Solo si con eso no basta,
            # segunda pasada hasta el minimo absoluto.
            for suelo_filas in (2, 0):
                if izq > objetivo:
                    falta = izq - objetivo
                    resto = self._recortar(self.panel_recientes, falta, suelo_filas)
                    resto = self._recortar(self.panel_origen, resto, suelo_filas)
                    izq -= falta - resto
                if der > objetivo:
                    falta = der - objetivo
                    resto = self._recortar(self.panel_favoritos, falta, suelo_filas)
                    der -= falta - resto

            self.update_idletasks()
            alto_pedido = self.winfo_reqheight()

        alto = max(min(alto_pedido, alto_max), ALTO_MINIMO)
        # El ancho solo se impone la primera vez; despues se respeta el que
        # haya dejado el usuario al redimensionar.
        if not self._ancho_fijado:
            ancho = min(ANCHO_INICIAL, int(self.winfo_screenwidth() * 0.95))
            self._ancho_fijado = True
        else:
            ancho = max(self.winfo_width(), ANCHO_MINIMO)
        self.geometry("%dx%d" % (ancho, alto))

        for panel, _ in topes:
            panel.programar_revision()

    @staticmethod
    def _recortar(panel, cuanto, suelo_filas=0):
        """Quita hasta 'cuanto' pixeles a un panel sin bajar de 'suelo_filas'
        filas (ni del minimo absoluto). Devuelve lo que no ha podido quitar."""
        if cuanto <= 0:
            return 0
        actual = panel.alto_fijado()
        suelo = max(ALTO_MINIMO_PANEL,
                    min(panel.alto_contenido(), panel.alto_fila() * suelo_filas))
        nuevo = max(actual - cuanto, suelo)
        if nuevo >= actual:
            return cuanto
        panel.fijar_alto(nuevo)
        return cuanto - (actual - nuevo)

    # -- lineas de origen ---------------------------------------------------

    def _anadir_linea(self, ruta="", extensiones=None, filtros=None):
        """Anade una tarjeta de origen. Devuelve el dict de la linea."""
        var_ruta = tk.StringVar(value=ruta)
        var_ext = tk.StringVar(value=formatear_extensiones(extensiones or []))

        tarjeta = ttk.Frame(self.panel_origen.interior, style="Tarjeta.TFrame",
                            padding=(10, 7, 8, 6))
        tarjeta.pack(fill="x", pady=PAD_FILA, padx=(0, 2))
        tarjeta.columnconfigure(1, weight=1)

        numero = ttk.Label(tarjeta, text="", width=2, anchor="e",
                           style="TarjetaNumero.TLabel")
        numero.grid(row=0, column=0, rowspan=2, sticky="n", padx=(0, 8), pady=(3, 0))

        entrada_ruta = ttk.Entry(tarjeta, textvariable=var_ruta)
        entrada_ruta.grid(row=0, column=1, sticky="ew")
        # Si el campo cambia de ancho (aparece la barra, se redimensiona la
        # ventana) se vuelve a ensenar el final, salvo que se este escribiendo.
        entrada_ruta.bind(
            "<Configure>",
            lambda _e, w=entrada_ruta: None if self.focus_get() is w else w.xview_moveto(1.0),
            add="+")
        ttk.Entry(tarjeta, textvariable=var_ext, width=13).grid(row=0, column=2,
                                                                padx=(6, 0))

        linea = {"marco": tarjeta, "ruta": var_ruta, "extensiones": var_ext,
                 "filtros": normalizar_filtros(filtros), "numero": numero,
                 "entrada_ruta": entrada_ruta}

        ttk.Button(tarjeta, text="Filtros...", style="Pequeno.TButton",
                   command=lambda l=linea: self._editar_filtros(l)).grid(
                       row=0, column=3, padx=(6, 0))
        ttk.Button(tarjeta, text="...", style="Pequeno.TButton",
                   command=lambda l=linea: self._elegir_origen(l)).grid(
                       row=0, column=4, padx=(4, 0))
        ttk.Button(tarjeta, text="\u00d7", style="Pequeno.TButton",
                   command=lambda l=linea: self._quitar_linea(l)).grid(
                       row=0, column=5, padx=(4, 0))

        linea["resumen"] = ttk.Label(tarjeta, text="", style="TarjetaVacia.TLabel")
        linea["resumen"].grid(row=1, column=1, columnspan=5, sticky="w", pady=(4, 0))
        self._pintar_resumen_linea(linea)

        var_ruta.trace_add("write", lambda *_: self._refrescar_estrella())
        var_ext.trace_add("write", lambda *_, l=linea: (self._pintar_resumen_linea(l),
                                                       self._refrescar_estrella()))

        self.lineas.append(linea)
        self._renumerar_lineas()
        self._refrescar_estrella()
        self._ajustar_altura()
        self._mostrar_final_ruta(linea)
        return linea

    def _mostrar_final_ruta(self, linea):
        """Las rutas largas no caben: se ensena el final, que es donde esta el
        nombre de la carpeta que importa. Solo al cargar, no mientras se escribe."""
        entrada = linea["entrada_ruta"]
        self.after_idle(lambda: entrada.winfo_exists() and entrada.xview_moveto(1.0))

    def _pintar_resumen_linea(self, linea):
        """Linea gris bajo la ruta: si extrae todos los tipos y sus filtros.

        Decir 'Todos los tipos' cuando el campo esta vacio evita que parezca
        un olvido: vacio es una opcion, no un error.
        """
        if "resumen" not in linea:
            return
        filtros = resumen_filtros(linea["filtros"])
        validas, invalidas = parsear_extensiones(linea["extensiones"].get())
        todos = not validas and not invalidas

        piezas = []
        if todos:
            piezas.append("Todos los tipos")
        piezas.append(("Filtros: " + filtros) if filtros else "Sin filtros")
        linea["resumen"].config(
            text="   \u00b7   ".join(piezas),
            style="TarjetaFiltro.TLabel" if filtros else "TarjetaVacia.TLabel")

    def _renumerar_lineas(self):
        """El numero de cada tarjeta es el que citan los avisos de error."""
        for numero, linea in enumerate(self.lineas, start=1):
            linea["numero"].config(text=str(numero))
        total = len(self.lineas)
        self.etiqueta_num_lineas.config(text="(%d)" % total if total > 1 else "")

    def _editar_filtros(self, linea):
        dialogo = VentanaFiltros(self, linea["ruta"].get().strip(), linea["filtros"])
        self.wait_window(dialogo)
        if dialogo.resultado is None:
            return
        linea["filtros"] = dialogo.resultado
        self._pintar_resumen_linea(linea)
        self._refrescar_estrella()

    def _quitar_linea(self, linea):
        if linea not in self.lineas:
            return
        self.lineas.remove(linea)
        linea["marco"].destroy()
        if not self.lineas:              # siempre queda al menos una linea
            self._anadir_linea()
        else:
            self._renumerar_lineas()
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
        pantalla se le actualizan extensiones y filtros en vez de duplicarla.
        """
        if self.var_sustituir.get() or self._lineas_vacias():
            for linea in list(self.lineas):
                linea["marco"].destroy()
            self.lineas = []

        for entrada in grupo.get("rutas", []):
            ruta = entrada.get("ruta", "")
            exts = list(entrada.get("extensiones", []))
            filtros = normalizar_filtros(entrada.get("filtros"))
            gemela = next(
                (l for l in self.lineas
                 if l["ruta"].get().strip()
                 and normalizar_ruta(l["ruta"].get().strip()) == normalizar_ruta(ruta)),
                None)
            if gemela is None:
                self._anadir_linea(ruta, exts, filtros)
            else:
                gemela["extensiones"].set(formatear_extensiones(exts))
                gemela["filtros"] = filtros
                self._pintar_resumen_linea(gemela)

        if not self.lineas:
            self._anadir_linea()

        self._renumerar_lineas()
        self._refrescar_estrella()
        self._ajustar_altura()

    def _rutas_actuales(self):
        """Las lineas escritas, como lista {ruta, extensiones, filtros}.

        Las extensiones invalidas se ignoran aqui: esto solo alimenta la
        estrella y el nombre del destino. La validacion de verdad, con su
        aviso, se hace al extraer.
        """
        rutas = []
        for linea in self.lineas:
            ruta = linea["ruta"].get().strip().strip('"')
            if not ruta:
                continue
            validas, _ = parsear_extensiones(linea["extensiones"].get())
            rutas.append({"ruta": os.path.normpath(ruta),
                          "extensiones": validas,
                          "filtros": normalizar_filtros(linea["filtros"])})
        return rutas

    def _programar_global(self):
        """Cada tecla en la global reprograma su aplicacion. Aunque el valor
        final sea el mismo que antes (escribir una letra y borrarla), cuenta
        como modificacion y se aplica: es la forma de repartirla de nuevo."""
        if self._tarea_global is not None:
            try:
                self.after_cancel(self._tarea_global)
            except tk.TclError:
                pass
        self._tarea_global = self.after(MS_APLICAR_GLOBAL, self._aplicar_global)

    def _aplicar_global(self):
        """Escribe la extension global en todas las lineas.

        En cada linea se quita lo que puso la global anterior y se anade lo de
        la nueva; lo que la linea tenga suyo se respeta. Solo se escriben las
        extensiones validas de la global: si tiene alguna invalida, el aviso
        sale al extraer.
        """
        self._tarea_global = None
        nuevas, _ = parsear_extensiones(self.var_extension.get())
        for linea in self.lineas:
            actual = linea["extensiones"].get()
            nuevo = sustituir_global(actual, self._global_aplicada, nuevas)
            if nuevo != actual:
                linea["extensiones"].set(nuevo)
        self._global_aplicada = nuevas
        self._refrescar_estrella()

    # -- favoritos ----------------------------------------------------------

    def _refrescar_estrella(self):
        """La estrella solo se enciende si rutas, extensiones y filtros
        coinciden exactamente con un favorito guardado."""
        rutas = self._rutas_actuales()
        if rutas and self.config_app.es_favorito_exacto(rutas):
            self.boton_favorito.config(text="\u2605 En favoritos")
        else:
            self.boton_favorito.config(text="\u2606 Guardar favorito")
        self._refrescar_destino_final()

    def _alternar_favorito_actual(self):
        rutas = self._rutas_actuales()
        if not rutas:
            messagebox.showinfo(TITULO, "Escribe o elige primero alguna carpeta de origen.")
            return
        if self.config_app.es_favorito_exacto(rutas):
            self.config_app.quitar_favorito(rutas)
            self.config_app.guardar()
            self._tras_cambiar_favoritos()
            return
        self._guardar_como_favorito(rutas)

    def _guardar_como_favorito(self, rutas):
        """Alta o sobrescritura segun el conjunto de rutas.

        Si esas mismas rutas ya son favoritas, el viejo se elimina entero y el
        nuevo se queda con las extensiones y filtros actuales. El nombre viejo
        se ofrece como valor inicial, pero se puede cambiar.
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
            inicial = nombre_carpeta(rutas[0]["ruta"])
            if len(rutas) > 1:
                inicial += " (+%d)" % (len(rutas) - 1)
            mensaje = "Nombre para este favorito:"

        nombre = simpledialog.askstring(TITULO, mensaje, initialvalue=inicial,
                                        parent=self)
        if nombre is None:
            return

        self.config_app.guardar_favorito(rutas, nombre.strip() or inicial)
        self.config_app.guardar()
        self._tras_cambiar_favoritos()

    def _tras_cambiar_favoritos(self):
        self._refrescar_favoritos()
        self._refrescar_recientes()
        self._refrescar_estrella()

    def _refrescar_favoritos(self):
        self.panel_favoritos.vaciar()

        total = len(self.config_app.favoritos)
        busqueda = self.var_busqueda_fav.get().strip().lower()
        visibles = [g for g in self.config_app.favoritos
                    if not busqueda or busqueda in (g.get("nombre", "").lower())]

        if busqueda and total:
            self.etiqueta_num_favoritos.config(text="(%d de %d)" % (len(visibles), total))
        else:
            self.etiqueta_num_favoritos.config(text="(%d)" % total if total else "")

        if not visibles:
            texto = ("Ningun favorito coincide con la busqueda."
                     if busqueda else "Todavia no hay favoritos.")
            ttk.Label(self.panel_favoritos.interior, text=texto,
                      style="Suave.TLabel").pack(anchor="w", pady=6)
        else:
            for grupo in visibles:
                self._tarjeta_favorito(grupo)

        self._ajustar_altura()

    def _tarjeta_favorito(self, grupo):
        rutas = grupo["rutas"]

        tarjeta = ttk.Frame(self.panel_favoritos.interior, style="Tarjeta.TFrame",
                            padding=(8, 6, 8, 6))
        tarjeta.pack(fill="x", pady=PAD_FILA, padx=(0, 2))
        tarjeta.columnconfigure(0, weight=1)

        ttk.Button(tarjeta, text=grupo.get("nombre") or resumen_rutas(rutas),
                   style="Nombre.TButton",
                   command=lambda g=grupo: self._cargar_grupo(g)).grid(
                       row=0, column=0, sticky="ew")
        ttk.Button(tarjeta, text="Renombrar", style="Pequeno.TButton",
                   command=lambda g=grupo: self._renombrar_favorito(g)).grid(
                       row=0, column=1, padx=(6, 0))
        ttk.Button(tarjeta, text="Quitar", style="Pequeno.TButton",
                   command=lambda g=grupo: self._quitar_favorito(g)).grid(
                       row=0, column=2, padx=(4, 0))

        info = self._texto_info_grupo(rutas)
        etiqueta = ttk.Label(tarjeta, text=info, style="TarjetaSuave.TLabel")
        etiqueta.grid(row=1, column=0, columnspan=3, sticky="w", padx=(2, 0),
                      pady=(5, 0))

        ayuda = AyudaEmergente(self, tarjeta, detalle_grupo(rutas))
        ayuda.vincular(tarjeta, etiqueta)

    @staticmethod
    def _texto_info_grupo(rutas):
        """'.java .jsp  ·  3 carpetas  ·  con filtros' en gris bajo el nombre."""
        piezas = [resumen_extensiones(rutas)]
        if len(rutas) == 1:
            piezas.append(acortar(rutas[0]["ruta"], 46))
        else:
            piezas.append("%d carpetas" % len(rutas))
        if any(filtros_activos(r.get("filtros")) for r in rutas):
            piezas.append("con filtros")
        return "   \u00b7   ".join(piezas)

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
        self._tras_cambiar_favoritos()

    # -- recientes ----------------------------------------------------------

    def _refrescar_recientes(self):
        self.panel_recientes.vaciar()

        if not self.config_app.recientes:
            ttk.Label(self.panel_recientes.interior,
                      text="Todavia no hay extracciones recientes.",
                      style="Suave.TLabel").pack(anchor="w", pady=6)
        else:
            for grupo in self.config_app.recientes:
                self._tarjeta_reciente(grupo)

        self._ajustar_altura()

    def _tarjeta_reciente(self, grupo):
        rutas = grupo["rutas"]
        marcado = self.config_app.es_favorito_exacto(rutas)

        tarjeta = ttk.Frame(self.panel_recientes.interior, style="Tarjeta.TFrame",
                            padding=(6, 5, 8, 5))
        tarjeta.pack(fill="x", pady=PAD_FILA, padx=(0, 2))
        tarjeta.columnconfigure(1, weight=1)

        tk.Button(
            tarjeta,
            text="\u2605" if marcado else "\u2606",
            fg=P["estrella_on"] if marcado else P["estrella_off"],
            font=(FUENTE, 13),
            relief="flat", bd=0, cursor="hand2", padx=4, highlightthickness=0,
            bg=P["tarjeta"], activebackground=P["tarjeta"],
            activeforeground=P["estrella_on"],
            command=lambda g=grupo: self._alternar_estrella_reciente(g),
        ).grid(row=0, column=0, rowspan=2, sticky="n", padx=(0, 6))

        texto_boton = nombre_carpeta(rutas[0]["ruta"])
        if len(rutas) > 1:
            texto_boton += "  (+%d)" % (len(rutas) - 1)
        ttk.Button(tarjeta, text=texto_boton, style="Ruta.TButton",
                   command=lambda g=grupo: self._cargar_grupo(g)).grid(
                       row=0, column=1, sticky="ew")

        guardado = grupo.get("guardado")
        if guardado:
            ttk.Button(tarjeta, text="Ver ficheros (%d)" % guardado.get("total", 0),
                       style="Pequeno.TButton",
                       command=lambda g=grupo: self._ver_guardado(g)).grid(
                           row=0, column=2, padx=(6, 0))

        info = self._texto_info_grupo(rutas)
        if guardado and guardado.get("fecha"):
            info += "   \u00b7   guardado " + guardado["fecha"]
        etiqueta = ttk.Label(tarjeta, text=info, style="TarjetaSuave.TLabel")
        etiqueta.grid(row=1, column=1, columnspan=2, sticky="w", padx=(2, 0), pady=(4, 0))

        ayuda = AyudaEmergente(self, tarjeta, detalle_grupo(rutas))
        ayuda.vincular(tarjeta, etiqueta)

    def _alternar_estrella_reciente(self, grupo):
        rutas = grupo["rutas"]
        if self.config_app.es_favorito_exacto(rutas):
            self.config_app.quitar_favorito(rutas)
            self.config_app.guardar()
            self._tras_cambiar_favoritos()
        else:
            self._guardar_como_favorito(rutas)

    def _cambiar_max_recientes(self):
        try:
            valor = int(self.var_max_recientes.get())
        except (TypeError, ValueError):
            return
        self.config_app.max_recientes = max(1, min(valor, TOPE_RECIENTES))
        self.config_app.recortar_recientes()
        # Guardar nunca puede pasar de Recordar: si se ha bajado Recordar por
        # debajo, el otro contador baja con el (y se borran las copias que
        # sobren).
        self.var_max_guardados.set(str(self.config_app.max_guardados))
        self.config_app.guardar()
        self._refrescar_recientes()

    def _cambiar_max_guardados(self):
        try:
            valor = int(self.var_max_guardados.get())
        except (TypeError, ValueError):
            return
        self.config_app.cambiar_max_guardados(valor)
        self.var_max_guardados.set(str(self.config_app.max_guardados))
        self.config_app.guardar()
        self._pintar_almacen()
        self._refrescar_recientes()

    def _pintar_almacen(self):
        if self.config_app.max_guardados == 0:
            texto = "No se guardan ficheros de las extracciones"
        else:
            texto = "Copias en: " + acortar(self.config_app.almacen(), 58)
        self.etiqueta_almacen.config(text=texto)

    def _elegir_almacen(self):
        ruta = filedialog.askdirectory(
            title="Carpeta donde guardar los ficheros de las ultimas extracciones",
            initialdir=self.config_app.almacen()
            if os.path.isdir(self.config_app.almacen()) else directorio_programa())
        if not ruta:
            return
        ruta = os.path.normpath(ruta)
        # Elegir la de por defecto la deja como "por defecto", para que siga
        # al programa si algun dia se cambia de sitio.
        if normalizar_ruta(ruta) == normalizar_ruta(almacen_por_defecto()):
            ruta = ""
        self.config_app.carpeta_guardados = ruta
        self.config_app.guardar()
        self._pintar_almacen()

    def _ver_guardado(self, grupo):
        guardado = grupo.get("guardado") or {}
        carpeta = guardado.get("carpeta", "")
        datos = leer_contenido_guardado(carpeta) if carpeta else None
        if datos is None:
            messagebox.showinfo(
                TITULO,
                "La copia guardada de esta extraccion ya no esta en el disco:\n\n%s"
                % (carpeta or "(sin ruta)"))
            self.config_app.olvidar_guardado(grupo)
            self.config_app.guardar()
            self._refrescar_recientes()
            return
        VentanaContenido(self, carpeta, datos)

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
            self._mostrar_final_ruta(linea)

    def _elegir_destino(self):
        inicial = self.var_destino.get().strip() or directorio_programa()
        ruta = filedialog.askdirectory(title="Selecciona la carpeta de destino",
                                       initialdir=inicial)
        if ruta:
            self.var_destino.set(os.path.normpath(ruta))
            self.config_app.destino = os.path.normpath(ruta)
            self.config_app.guardar()

    def _refrescar_destino_final(self):
        rutas = self._rutas_actuales()
        base = self.var_destino.get().strip() or directorio_programa()
        if rutas:
            carpeta = os.path.join(base, nombre_carpeta_destino(rutas))
            self.etiqueta_destino_final.config(text="Se creara: " + acortar(carpeta, 80))
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

            # Sin extensiones = todos los tipos. No es un error.
            recogidas.append({"ruta": os.path.normpath(ruta),
                              "extensiones": validas,
                              "filtros": normalizar_filtros(linea["filtros"])})

        if not recogidas:
            return None, "Indica al menos una carpeta de origen."

        # Misma carpeta en dos lineas CON LOS MISMOS FILTROS: se fusionan
        # sumando extensiones; si una de las dos es de todos los tipos, gana
        # esa. Si los filtros difieren se dejan como dos pasadas distintas (por
        # ejemplo, 10 al azar de una y todo lo pequeno de otra) y los ficheros
        # repetidos se descartan al buscar.
        fusionadas = []
        indice = {}
        for entrada in recogidas:
            clave = (normalizar_ruta(entrada["ruta"]), clave_filtros(entrada["filtros"]))
            if clave in indice:
                destino = indice[clave]
                if not destino["extensiones"] or not entrada["extensiones"]:
                    destino["extensiones"] = []
                    continue
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
        destino = os.path.join(base_destino, nombre_carpeta_destino(rutas))

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

        # Igual con el almacen de copias: si estuviera dentro de un origen, la
        # siguiente extraccion de ese origen se llevaria tambien las copias.
        almacen = self.config_app.almacen() if self.config_app.max_guardados else None
        if almacen:
            normal = normalizar_ruta(almacen)
            for entrada in rutas:
                origen = normalizar_ruta(entrada["ruta"])
                if normal == origen or normal.startswith(origen + os.sep):
                    messagebox.showerror(
                        TITULO,
                        "La carpeta donde se guardan las copias esta dentro de una "
                        "de origen:\n\n%s\n\nCambiala en Recientes > Cambiar... o pon "
                        "'Guardar ficheros de' a 0." % entrada["ruta"])
                    return

        inclusion = self.var_incluir.get().strip().lower()
        exclusion = self.var_excluir.get().strip().lower()
        modo = self._modo_filtro_actual()

        self.var_estado.set("Buscando ficheros...")
        self.update_idletasks()

        ficheros, muestras = self._buscar(rutas, inclusion, modo, exclusion)
        if not ficheros:
            self.var_estado.set("Listo.")
            detalle = "\n".join("- " + acortar(e["ruta"], 60) for e in rutas)
            aviso = "No se ha encontrado ningun fichero en:\n%s" % detalle
            if inclusion or exclusion or any(filtros_activos(e["filtros"]) for e in rutas):
                aviso += "\n\nQuiza algun filtro es demasiado estricto."
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
            args=(ficheros, destino, rutas, muestras, almacen),
            daemon=True,
        )
        self.hilo.start()
        self.after(60, self._procesar_cola)

    @staticmethod
    def _buscar(rutas, inclusion, modo, exclusion):
        """Recorre cada origen con SUS extensiones y SUS filtros.

        Orden por fichero: extension, filtro global de nombre, filtros de la
        carpeta (texto y tamano). La muestra aleatoria se aplica al final, por
        carpeta, sobre lo que haya sobrevivido. Devuelve (ficheros, muestras),
        donde muestras lista (ruta, elegidos, candidatos) de las carpetas en
        las que se ha sacado muestra.
        """
        encontrados = []
        vistos = set()
        muestras = []

        for entrada in rutas:
            extensiones = set(entrada["extensiones"])   # vacio = todos los tipos
            filtros = normalizar_filtros(entrada.get("filtros"))
            candidatos = []

            for carpeta, _, ficheros in os.walk(entrada["ruta"]):
                for nombre in ficheros:
                    if (extensiones
                            and os.path.splitext(nombre)[1].lower() not in extensiones):
                        continue
                    if not coincide_filtro(nombre, inclusion, modo, exclusion):
                        continue
                    completa = os.path.join(carpeta, nombre)
                    if not pasa_filtros_carpeta(completa, nombre, filtros):
                        continue
                    candidatos.append(completa)

            elegidos = aplicar_muestra(candidatos, filtros)
            if filtros["azar_modo"] and candidatos:
                muestras.append((entrada["ruta"], len(elegidos), len(candidatos)))

            for completa in elegidos:
                clave = normalizar_ruta(completa)
                if clave in vistos:
                    continue
                vistos.add(clave)
                encontrados.append(completa)

        return encontrados, muestras

    def _trabajo_copia(self, ficheros, destino, rutas, muestras, almacen=None):
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
        contenido = []          # para el marcador de la copia guardada

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
                try:
                    octetos = os.path.getsize(ruta)
                except OSError:
                    octetos = 0
                contenido.append({"nombre": candidato, "origen": ruta, "bytes": octetos})
            except OSError:
                fallidos.append(nombre)

            self.cola.put(("avance", indice, len(ficheros), nombre))

        guardado, error_guardado = None, None
        if almacen and copiados:
            self.cola.put(("estado", "Guardando copia de la extraccion..."))
            guardado, error_guardado = self._guardar_copia(destino, almacen, rutas, contenido)

        self.cola.put(("fin", copiados, fallidos, destino, rutas, muestras,
                       guardado, error_guardado))

    @staticmethod
    def _guardar_copia(destino, almacen, rutas, contenido):
        """Copia el resultado al almacen con su marcador. Devuelve (info, error).

        Se copia desde la carpeta destino recien llenada, no otra vez desde los
        origenes: asi la copia es exactamente lo que se extrajo, con los
        nombres _1, _2 ya resueltos y la misma muestra aleatoria.
        """
        ahora = datetime.now()
        nombre = ahora.strftime("%Y-%m-%d_%H-%M-%S") + "_" + os.path.basename(destino)
        carpeta = os.path.join(almacen, nombre)
        sufijo = 2
        while os.path.exists(carpeta):
            carpeta = os.path.join(almacen, "%s_%d" % (nombre, sufijo))
            sufijo += 1
        try:
            os.makedirs(almacen, exist_ok=True)
            shutil.copytree(destino, carpeta)
            with open(os.path.join(carpeta, MARCADOR_GUARDADO), "w", encoding="utf-8") as f:
                json.dump({
                    "programa": FIRMA_PROGRAMA,
                    "version": 1,
                    "fecha": ahora.strftime("%d/%m/%Y %H:%M:%S"),
                    "destino": destino,
                    "rutas": [copiar_entrada(r) for r in rutas],
                    "ficheros": contenido,
                }, f, indent=2, ensure_ascii=False)
        except OSError as error:
            # A medio copiar no sirve: se limpia. Aqui si se puede borrar sin
            # marcador porque la carpeta la acaba de crear este mismo metodo.
            if os.path.isdir(carpeta):
                shutil.rmtree(carpeta, ignore_errors=True)
            return None, str(error)
        return {"carpeta": carpeta, "fecha": ahora.strftime("%d/%m/%Y %H:%M"),
                "total": len(contenido)}, None

    def _procesar_cola(self):
        try:
            while True:
                mensaje = self.cola.get_nowait()
                tipo = mensaje[0]

                if tipo == "avance":
                    _, indice, total, nombre = mensaje
                    self.barra.config(value=indice)
                    self.var_contador.set("%d/%d" % (indice, total))
                    self.var_estado.set("Copiando: " + acortar(nombre, 40))

                elif tipo == "estado":
                    self.var_estado.set(mensaje[1])

                elif tipo == "error":
                    self.boton_extraer.config(state="normal")
                    self.var_estado.set("Error.")
                    messagebox.showerror(TITULO, mensaje[1])
                    return

                elif tipo == "fin":
                    self._finalizar(*mensaje[1:])
                    return
        except queue.Empty:
            pass

        self.after(60, self._procesar_cola)

    def _finalizar(self, copiados, fallidos, destino, rutas, muestras,
                   guardado=None, error_guardado=None):
        self.boton_extraer.config(state="normal")
        self.var_estado.set("Hecho. %d ficheros copiados." % copiados)

        self.config_app.anadir_historial(copiados, rutas, destino)
        if guardado:
            self.config_app.asignar_guardado(rutas, guardado)
        self.config_app.guardar()
        self._refrescar_recientes()

        tipos = resumen_extensiones(rutas)
        resumen = ("Se han copiado %d ficheros (%s) desde %d carpeta(s).\n\nDestino:\n%s"
                   % (copiados, tipos, len(rutas), destino))
        if muestras:
            resumen += "\n\nMuestra aleatoria:"
            for ruta, elegidos, candidatos in muestras:
                resumen += "\n- %s: %d de %d" % (acortar(ruta, 46), elegidos, candidatos)
        if guardado:
            resumen += "\n\nCopia guardada en:\n%s" % guardado["carpeta"]
        elif error_guardado:
            resumen += ("\n\nLa extraccion es correcta, pero no se ha podido guardar "
                        "la copia:\n%s" % error_guardado)
        if fallidos:
            resumen += "\n\nNo se han podido copiar %d ficheros." % len(fallidos)
        if fallidos or error_guardado:
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
