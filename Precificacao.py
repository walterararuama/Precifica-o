# Apenas os módulos leves necessários para exibir o splash imediatamente
import sys
import os
import tkinter as tk
import ctypes
import configparser
import sqlite3 as _sqlite3_cfg

# --- ATIVAÇÃO DE ALTA RESOLUÇÃO ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

if getattr(sys, 'frozen', False):
    diretorio_atual = os.path.dirname(sys.executable)
else:
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))

_CONFIG_INI_NOVO = False

# Config local por máquina/usuário — nunca na pasta de rede
_CONFIG_LOCAL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", diretorio_atual), "Precificacao")
_CONFIG_LOCAL_INI = os.path.join(_CONFIG_LOCAL_DIR, "config.ini")

def _ler_pasta_base():
    """Le a pasta base de trabalho do config.ini local (AppData do usuário).
    Tudo fica dentro dela: fornecedores.db, ARQUIVO, FRETES.
    O config.ini fica em %LOCALAPPDATA%\\Precificacao\\ em cada maquina."""
    global _CONFIG_INI_NOVO
    _cfg = configparser.ConfigParser()
    if os.path.exists(_CONFIG_LOCAL_INI):
        _cfg.read(_CONFIG_LOCAL_INI, encoding='utf-8')
        # suporta chave nova 'pasta' e chave antiga 'caminho' (compatibilidade)
        pasta = _cfg.get("banco", "pasta", fallback=None)
        if not pasta:
            caminho_antigo = _cfg.get("banco", "caminho", fallback=None)
            pasta = os.path.dirname(caminho_antigo) if caminho_antigo else None
        return pasta
    else:
        _CONFIG_INI_NOVO = True
        return None  # Sem padrão — vai pedir ao usuário

def _aplicar_pasta_base(pasta):
    """Define DB_PATH, pasta_arquivo e pasta_fretes a partir da pasta base."""
    global DB_PATH, pasta_arquivo, pasta_fretes
    if not pasta:
        DB_PATH = ""
        pasta_arquivo = ""
        pasta_fretes = ""
        return
    DB_PATH = os.path.join(pasta, "fornecedores.db")
    for _p, _attr in [(os.path.join(pasta, "ARQUIVO"), "pasta_arquivo"),
                      (os.path.join(pasta, "FRETES"),  "pasta_fretes")]:
        try:
            os.makedirs(_p, exist_ok=True)
            globals()[_attr] = _p
        except Exception:
            _local = os.path.join(diretorio_atual, os.path.basename(_p))
            os.makedirs(_local, exist_ok=True)
            globals()[_attr] = _local

DB_PATH       = ""
pasta_arquivo = ""
pasta_fretes  = ""
_aplicar_pasta_base(_ler_pasta_base())

def _ler_pasta_fdc():
    cfg = configparser.ConfigParser()
    if os.path.exists(_CONFIG_LOCAL_INI):
        cfg.read(_CONFIG_LOCAL_INI, encoding='utf-8')
    return cfg.get("fdc", "pasta", fallback=None)

def _salvar_pasta_fdc(pasta):
    cfg = configparser.ConfigParser()
    if os.path.exists(_CONFIG_LOCAL_INI):
        cfg.read(_CONFIG_LOCAL_INI, encoding='utf-8')
    if "fdc" not in cfg:
        cfg["fdc"] = {}
    cfg["fdc"]["pasta"] = pasta
    os.makedirs(_CONFIG_LOCAL_DIR, exist_ok=True)
    with open(_CONFIG_LOCAL_INI, "w", encoding="utf-8") as _f:
        cfg.write(_f)

def _ler_grupo_whatsapp():
    cfg = configparser.ConfigParser()
    if os.path.exists(_CONFIG_LOCAL_INI):
        cfg.read(_CONFIG_LOCAL_INI, encoding='utf-8')
    return cfg.get("whatsapp", "grupo", fallback=None)

def _salvar_grupo_whatsapp(nome):
    cfg = configparser.ConfigParser()
    if os.path.exists(_CONFIG_LOCAL_INI):
        cfg.read(_CONFIG_LOCAL_INI, encoding='utf-8')
    if "whatsapp" not in cfg:
        cfg["whatsapp"] = {}
    cfg["whatsapp"]["grupo"] = nome
    os.makedirs(_CONFIG_LOCAL_DIR, exist_ok=True)
    with open(_CONFIG_LOCAL_INI, "w", encoding="utf-8") as _f:
        cfg.write(_f)

def _ler_contato_chefe():
    cfg = configparser.ConfigParser()
    if os.path.exists(_CONFIG_LOCAL_INI):
        cfg.read(_CONFIG_LOCAL_INI, encoding='utf-8')
    return cfg.get("whatsapp", "chefe", fallback=None)

def _salvar_contato_chefe(nome):
    cfg = configparser.ConfigParser()
    if os.path.exists(_CONFIG_LOCAL_INI):
        cfg.read(_CONFIG_LOCAL_INI, encoding='utf-8')
    if "whatsapp" not in cfg:
        cfg["whatsapp"] = {}
    cfg["whatsapp"]["chefe"] = nome
    os.makedirs(_CONFIG_LOCAL_DIR, exist_ok=True)
    with open(_CONFIG_LOCAL_INI, "w", encoding="utf-8") as _f:
        cfg.write(_f)

def _copiar_imagem_clipboard(img):
    import tempfile as _tmp, subprocess as _sp2
    f = _tmp.NamedTemporaryFile(suffix=".png", delete=False)
    path = f.name; f.close()
    img.save(path, "PNG")
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        "Add-Type -AssemblyName System.Drawing;"
        f"$i=[System.Drawing.Image]::FromFile('{path.replace(chr(92),chr(47))}');"
        "[System.Windows.Forms.Clipboard]::SetImage($i);$i.Dispose()"
    )
    _sp2.run(["powershell", "-NonInteractive", "-Command", ps],
             capture_output=True, timeout=12)
    try: os.unlink(path)
    except: pass

def _enviar_whatsapp_desktop(grupo):
    import subprocess as _sp, time as _t
    import pyautogui as _ag, pygetwindow as _gw
    _ag.FAILSAFE = False
    _sp.run(["cmd", "/c", "start", "whatsapp://"], shell=True)
    for _ in range(16):
        _t.sleep(0.5)
        wins = _gw.getWindowsWithTitle("WhatsApp")
        if wins:
            wins[0].activate()
            break
    _t.sleep(1.2)
    _ag.press('escape');     _t.sleep(0.3)
    _ag.press('escape');     _t.sleep(0.3)
    _ag.hotkey('ctrl','f');  _t.sleep(0.5)
    _ag.hotkey('ctrl','a');  _ag.write(grupo, interval=0.05)
    _t.sleep(1.8)
    _ag.press('down');       _t.sleep(0.4)
    _ag.press('enter');      _t.sleep(0.8)
    _ag.hotkey('ctrl','v');  _t.sleep(2.0)
    _ag.press('enter')

# =====================================================================
# SPLASH SCREEN — aparece antes dos imports pesados
# =====================================================================
_BG       = "#1C2833"   # fundo escuro
_GOLD     = "#F1C40F"   # dourado
_TRACK    = "#2C3E50"   # trilho da barra
_WHITE    = "#FFFFFF"
_GRAY     = "#7F8C8D"
_LGRAY    = "#BDC3C7"

splash = tk.Tk()
splash.overrideredirect(True)
splash.attributes("-topmost", True)
_SW, _SH = 540, 300
_SX = (splash.winfo_screenwidth()  // 2) - (_SW // 2)
_SY = (splash.winfo_screenheight() // 2) - (_SH // 2)
splash.geometry(f"{_SW}x{_SH}+{_SX}+{_SY}")
splash.configure(bg=_BG)

# Faixa dourada no topo
tk.Frame(splash, bg=_GOLD, height=5).pack(fill="x", side="top")

# Área central
_fm = tk.Frame(splash, bg=_BG)
_fm.pack(fill="both", expand=True, padx=35, pady=(18, 0))

# Nome da empresa
tk.Label(_fm, text="Bruno Eletromóveis",
         font=("Segoe UI", 24, "bold"), bg=_BG, fg=_WHITE, anchor="w").pack(fill="x")
tk.Label(_fm, text="Engenharia de Custos  ·  V4",
         font=("Segoe UI", 10), bg=_BG, fg=_GRAY, anchor="w").pack(fill="x", pady=(2, 0))

# Logo voga no canto inferior direito do splash
try:
    from PIL import Image as _PilImg, ImageTk as _PilTk
    _voga_splash_path = (os.path.join(sys._MEIPASS, "voga.png")
                         if getattr(sys, 'frozen', False)
                         else os.path.join(diretorio_atual, "voga.png"))
    _voga_img = _PilImg.open(_voga_splash_path).convert("RGBA")
    _target_w = 160
    _voga_img = _voga_img.resize(
        (_target_w, int(_voga_img.height * _target_w / _voga_img.width)),
        _PilImg.LANCZOS)
    _bg_s = _PilImg.new("RGBA", _voga_img.size, (28, 40, 51, 255))  # #1C2833
    _bg_s.paste(_voga_img, mask=_voga_img.split()[3])
    _logo_splash_photo = _PilTk.PhotoImage(_bg_s.convert("RGB"))
    _lbl_voga_s = tk.Label(splash, image=_logo_splash_photo, bg=_BG, bd=0)
    _lbl_voga_s.image = _logo_splash_photo
    _lbl_voga_s.place(relx=1.0, rely=1.0, anchor="se", x=-14, y=-34)
except Exception:
    pass

# Linha separadora dourada
tk.Frame(_fm, bg=_GOLD, height=2).pack(fill="x", pady=(14, 18))

# --- Barra de progresso em Canvas ---
_BAR_H   = 22
_RADIUS  = 11   # metade da altura → cápsulas arredondadas
_cv = tk.Canvas(_fm, height=_BAR_H, bg=_BG, highlightthickness=0)
_cv.pack(fill="x")

def _draw_pill(canvas, x0, y0, x1, y1, color):
    """Desenha um retângulo com pontas arredondadas (cápsula)."""
    r = (y1 - y0) // 2
    canvas.create_oval(x0, y0, x0 + 2*r, y1, fill=color, outline="")
    canvas.create_oval(x1 - 2*r, y0, x1, y1, fill=color, outline="")
    canvas.create_rectangle(x0 + r, y0, x1 - r, y1, fill=color, outline="")

# Trilho (fundo da barra)
_draw_pill(_cv, 0, 0, _SW - 70, _BAR_H, _TRACK)

# Barra de preenchimento (começa zerada — tags permitem redesenho)
_bar_tag  = "bar_fill"
_shine_tag = "bar_shine"

# Porcentagem à direita da barra
_lbl_pct = tk.Label(_fm, text="0%", font=("Segoe UI", 10, "bold"),
                    bg=_BG, fg=_GOLD, width=5, anchor="e")
_lbl_pct.place(relx=1.0, y=-_BAR_H - 2, anchor="ne")   # posicionado à direita

# Label de status
_lbl_status = tk.Label(_fm, text="Iniciando...",
                        font=("Segoe UI", 9), bg=_BG, fg=_LGRAY, anchor="w")
_lbl_status.pack(fill="x", pady=(10, 0))

# Rodapé
tk.Frame(splash, bg=_GOLD, height=2).pack(fill="x", side="bottom")
tk.Label(splash, text="© Bruno Eletromóveis  —  Sistema de Precificação",
         font=("Segoe UI", 7), bg=_BG, fg=_GRAY).pack(side="bottom", pady=(4, 4))

splash.update()

def _splash_set(pct, msg):
    """Atualiza barra de progresso e texto de status."""
    _cv.delete("all")
    w_total = _cv.winfo_width() or (_SW - 70)
    w_fill  = max(int(w_total * pct / 100), 0)

    _draw_pill(_cv, 0, 0, w_total, _BAR_H, _TRACK)          # trilho
    if w_fill > _RADIUS * 2:
        _draw_pill(_cv, 0, 0, w_fill, _BAR_H, _GOLD)         # preenchimento
        # Brilho sutil (linha clara no topo da barra)
        _cv.create_line(
            _RADIUS, 3, w_fill - _RADIUS, 3,
            fill="#FDE880", width=2
        )
    _lbl_pct.config(text=f"{pct}%")
    _lbl_status.config(text=f"  ▶  {msg}")
    splash.update()

_splash_set(3, "Iniciando...")

# --- IMPORTS PESADOS — progresso real a cada etapa ---
_splash_set(8,  "Carregando pandas e módulos base...")
import re
import difflib
import pandas as pd

_splash_set(30, "Inicializando interface gráfica...")
from tkinter import ttk, messagebox, filedialog
import glob

_splash_set(42, "Carregando temas visuais (ttkbootstrap)...")
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

_splash_set(55, "Carregando componentes de tooltip...")
try:
    from ttkbootstrap.widgets import ToolTip
except ImportError:
    from ttkbootstrap.tooltip import ToolTip

_splash_set(62, "Carregando utilitários do sistema...")
from datetime import datetime
import time
import logging
import shutil
from PIL import Image, ImageTk

_splash_set(68, "Carregando módulo de fretes...")
from edicao_de_fretes import abrir_modulo_fretes

_splash_set(75, "Carregando módulo de exportação...")
from exportacao import processar_exportacao_carga, salvar_edicao_precos

_splash_set(82, "Carregando banco de fornecedores...")
from db_fornecedores import inicializar_banco_fornecedores, carregar_fornecedores_db, get_lista_nomes_fornecedores, abrir_gerenciador_fornecedores, abrir_gerenciador_de_para
from importador_xml import ler_xml_nfe, cruzar_produtos, salvar_de_para

_splash_set(88, "Carregando utilitários de cálculo...")
from utils import converter_moeda, formatar_moeda, formatar_percentual, auto_selecionar, arredondar_preco, check_nota_duplicada

_splash_set(93, "Carregando motor FDC...")
from motor_fdc import cache_fdc, carregar_dados_memoria, tem_brutos_novos

_splash_set(96, "Configurando logs do sistema...")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('precificacao.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)

_splash_set(97, "Validando acesso ao banco de dados...")
_banco_acessivel = True
if _CONFIG_INI_NOVO or not DB_PATH:
    # Primeiro acesso nesta máquina — vai pedir pasta ao usuário, sem erro
    _banco_acessivel = False
else:
    try:
        inicializar_banco_fornecedores(DB_PATH, diretorio_atual)
    except Exception as _e_banco:
        _banco_acessivel = False
        from tkinter import messagebox as _mb
        _mb.showerror(
            "Banco de Dados Inacessível",
            f"Não foi possível acessar o banco de dados em:\n{DB_PATH}\n\nErro: {_e_banco}\n\n"
            "Verifique o caminho em Configurações → Banco de Dados após o sistema abrir.",
            parent=splash
        )

_splash_set(100, "Concluído! Abrindo o sistema...")
cache_fornecedores = carregar_fornecedores_db(DB_PATH) if _banco_acessivel else []

splash.after(450, splash.destroy)
splash.mainloop()

# =====================================================================
# --- TELA PRINCIPAL ---
# =====================================================================

def _get_recurso(nome):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, nome)
    return os.path.join(diretorio_atual, nome)

def _criar_logo_img(pil_rgba, hex_bg):
    r, g, b = int(hex_bg[1:3], 16), int(hex_bg[3:5], 16), int(hex_bg[5:7], 16)
    bg = Image.new("RGBA", pil_rgba.size, (r, g, b, 255))
    bg.paste(pil_rgba, mask=pil_rgba.split()[3])
    return ImageTk.PhotoImage(bg.convert("RGB"))

def criar_tela():
    global cache_fornecedores
    root = ttkb.Window(themename="litera")
    root.title("Bruno Eletromóveis - Engenharia de Custos V4")
    root.geometry("1400x850")
    root.state('zoomed')

    try:
        root.iconbitmap(_get_recurso("icone.ico"))
    except Exception:
        pass
    try:
        _logo_rgba = Image.open(_get_recurso("voga.png")).convert("RGBA")
        _logo_rgba.thumbnail((9999, 40), Image.LANCZOS)
    except Exception:
        _logo_rgba = None
    lbl_logo = None

    root.tema_atual = "claro"

    linhas_nota = []
    indice_linha_atual = 2 
    lista_fornecedores = get_lista_nomes_fornecedores(DB_PATH)
    var_regime = tk.StringVar(value="MISTA (NF + Romaneio)") 
    var_pedido = tk.StringVar()
    root.arquivo_aberto_atual = None 

    root.ignorando_validacao = False

    var_num_nota = tk.StringVar()
    var_dt_emissao = tk.StringVar()
    var_dt_chegada = tk.StringVar()
    var_tipo_frete = tk.StringVar()
    var_val_terceirizado = tk.StringVar(value="R$ 0,00")
    var_markup_geral = tk.StringVar(value="0,00%")

    def atualizar_cache_fornecedores():
        global cache_fornecedores
        cache_fornecedores = carregar_fornecedores_db(DB_PATH)
    root.atualizar_cache_fornecedores = atualizar_cache_fornecedores
    
    def pular_foco(proximo_widget):
        root.after(10, proximo_widget.focus_force)
        return "break"

    def safe_is_focused(widget):
        try:
            focus = root.focus_get()
            if focus is None: return True
            return focus == widget
        except KeyError: return True

    def mostrar_balao_aviso(widget, mensagem):
        if getattr(widget, 'balao_ativo', False): return
        widget.balao_ativo = True
        try:
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() - 28 
            balao = tk.Toplevel(widget)
            balao.wm_overrideredirect(True)
            balao.wm_geometry(f"+{x}+{y}")
            balao.attributes("-topmost", True)
            lbl = tk.Label(balao, text=f"⚠️ {mensagem}", bg="#2C3E50", fg="#F1C40F", font=("Segoe UI", 9, "bold"), padx=10, pady=4, borderwidth=1, relief="solid")
            lbl.pack()
            def fechar():
                widget.balao_ativo = False
                try: balao.destroy()
                except: pass
            widget.after(2000, fechar)
        except: widget.balao_ativo = False

    def check_and_trap(condicao, widget, mensagem):
        if getattr(root, 'ignorando_validacao', False): return False
        focus = root.focus_get()
        if focus is None: return False
        try:
            if str(focus.winfo_toplevel()) != str(root): return False
        except Exception: return False
        if condicao:
            mostrar_balao_aviso(widget, mensagem)
            root.after(10, widget.focus_force)
            return True
        return False

    style = ttkb.Style()

    for _nome, _bg, _hover in [
        ("Lilas",          "#9B59B6", "#8E44AD"),
        ("Vermelho",       "#E74C3C", "#C0392B"),
        ("Azul",           "#2980B9", "#1F618D"),
        ("VerdeClaro",     "#2ECC71", "#27AE60"),
        ("VerdeSalvar",    "#1A7A4A", "#145E38"),
        ("VermelhoClaro",  "#FF6B6B", "#E74C3C"),
        ("Marrom",         "#5D4037", "#4E342E"),
        ("VermelhoEscuro", "#8B0000", "#6B0000"),
        ("Ciano",          "#17A589", "#148F77"),
        ("Laranja",        "#E67E22", "#CA6F1E"),
    ]:
        style.configure(f"{_nome}.TButton", background=_bg, foreground="white",
                        font=("Segoe UI", 9, "bold"), borderwidth=0, padding=4)
        style.map(f"{_nome}.TButton",
                  background=[("pressed", _hover), ("active", _hover)],
                  foreground=[("pressed", "white"), ("active", "white")])


    def obter_cores_tabela():
        if getattr(root, 'tema_atual', 'claro') == 'claro':
            return "#FFFFFF", "#F8F9F9", "#E3F2FD", "#E8F5E9", "#FFF8E1", "#F3E5F5", "#E8F8F5", "#0E6655", "black", "#d35400"
        else:
            return "#3b4252", "#2e3440", "#1a2c42", "#193623", "#3b2612", "#301a3b", "#123026", "#4ade80", "#eceff4", "#f97316"

    def atualizar_estilos():
        if root.tema_atual == 'claro':
            style.configure("SuperId.TLabel", background="#2C3E50", foreground="white", font=("Segoe UI", 11, "bold"), anchor="center", justify="center")
            style.configure("SubId.TLabel", background="#34495E", foreground="white", font=("Segoe UI", 9, "bold"), anchor="center", justify="center")
            style.configure("SuperNF.TLabel", background="#2980B9", foreground="white", font=("Segoe UI", 11, "bold"), anchor="center", justify="center")
            style.configure("SubNF.TLabel", background="#3498DB", foreground="white", font=("Segoe UI", 9, "bold"), anchor="center", justify="center")
            style.configure("SuperRom.TLabel", background="#27AE60", foreground="white", font=("Segoe UI", 11, "bold"), anchor="center", justify="center")
            style.configure("SubRom.TLabel", background="#2ECC71", foreground="white", font=("Segoe UI", 9, "bold"), anchor="center", justify="center")
            style.configure("SuperFrete.TLabel", background="#D35400", foreground="white", font=("Segoe UI", 11, "bold"), anchor="center", justify="center")
            style.configure("SubFrete.TLabel", background="#E67E22", foreground="white", font=("Segoe UI", 9, "bold"), anchor="center", justify="center")
            style.configure("SuperRes.TLabel", background="#8E44AD", foreground="white", font=("Segoe UI", 11, "bold"), anchor="center", justify="center")
            style.configure("SubRes.TLabel", background="#9B59B6", foreground="white", font=("Segoe UI", 9, "bold"), anchor="center", justify="center")
            style.configure("SuperVenda.TLabel", background="#0E6655", foreground="#F1C40F", font=("Segoe UI", 11, "bold"), anchor="center", justify="center")
            style.configure("SubVenda.TLabel", background="#117A65", foreground="white", font=("Segoe UI", 9, "bold"), anchor="center", justify="center")
        else:
            style.configure("SuperId.TLabel", background="#1e222a", foreground="white", font=("Segoe UI", 11, "bold"), anchor="center", justify="center")
            style.configure("SubId.TLabel", background="#282c34", foreground="white", font=("Segoe UI", 9, "bold"), anchor="center", justify="center")
            style.configure("SuperNF.TLabel", background="#0f2038", foreground="white", font=("Segoe UI", 11, "bold"), anchor="center", justify="center")
            style.configure("SubNF.TLabel", background="#173152", foreground="white", font=("Segoe UI", 9, "bold"), anchor="center", justify="center")
            style.configure("SuperRom.TLabel", background="#0b2416", foreground="white", font=("Segoe UI", 11, "bold"), anchor="center", justify="center")
            style.configure("SubRom.TLabel", background="#103621", foreground="white", font=("Segoe UI", 9, "bold"), anchor="center", justify="center")
            style.configure("SuperFrete.TLabel", background="#331906", foreground="white", font=("Segoe UI", 11, "bold"), anchor="center", justify="center")
            style.configure("SubFrete.TLabel", background="#4a260b", foreground="white", font=("Segoe UI", 9, "bold"), anchor="center", justify="center")
            style.configure("SuperRes.TLabel", background="#24112e", foreground="white", font=("Segoe UI", 11, "bold"), anchor="center", justify="center")
            style.configure("SubRes.TLabel", background="#381b47", foreground="white", font=("Segoe UI", 9, "bold"), anchor="center", justify="center")
            style.configure("SuperVenda.TLabel", background="#091c14", foreground="#4ade80", font=("Segoe UI", 11, "bold"), anchor="center", justify="center")
            style.configure("SubVenda.TLabel", background="#0d2b1f", foreground="white", font=("Segoe UI", 9, "bold"), anchor="center", justify="center")

    atualizar_estilos()

    def abrir_config_banco(primeiro_acesso=False):
        janela_cfg = tk.Toplevel(root)
        janela_cfg.title("Configurações — Pasta de Trabalho em Rede")
        janela_cfg.resizable(False, False)
        janela_cfg.transient(root)
        janela_cfg.grab_set()
        janela_cfg.update_idletasks()
        larg, alt = 660, 280
        x = root.winfo_x() + (root.winfo_width()  // 2) - larg // 2
        y = root.winfo_y() + (root.winfo_height() // 2) - alt  // 2
        janela_cfg.geometry(f"{larg}x{alt}+{x}+{y}")

        if primeiro_acesso:
            ttkb.Label(janela_cfg,
                text="  Informe a pasta de rede onde estão os dados da empresa.\n"
                     "  O programa irá ler e salvar tudo nessa pasta (banco, planilhas, fretes).",
                font=("Segoe UI", 9), bootstyle="warning", padding=6).pack(fill="x", padx=10, pady=(8, 0))

        f_cfg = ttkb.Labelframe(janela_cfg, text=" Pasta de trabalho (banco + planilhas + fretes) ", padding=12)
        f_cfg.pack(fill="both", expand=True, padx=10, pady=8)

        # pasta atual = diretório do DB_PATH
        _pasta_atual = os.path.dirname(DB_PATH) if DB_PATH else diretorio_atual
        var_pasta = tk.StringVar(value=_pasta_atual)

        ttkb.Entry(f_cfg, textvariable=var_pasta, font=("Segoe UI", 10), width=62).grid(
            row=0, column=0, padx=(0, 5), pady=6, sticky="ew")

        def _browse():
            import tkinter.filedialog as _fd
            p = _fd.askdirectory(title="Selecionar pasta de trabalho", parent=janela_cfg)
            if p:
                var_pasta.set(os.path.normpath(p))

        ttkb.Button(f_cfg, text="📂", command=_browse, bootstyle="secondary", width=3).grid(row=0, column=1)

        lbl_info = ttkb.Label(f_cfg,
            text=f"  Banco:    {os.path.join(_pasta_atual, 'fornecedores.db')}\n"
                 f"  Arquivos: {os.path.join(_pasta_atual, 'ARQUIVO')}\n"
                 f"  Fretes:   {os.path.join(_pasta_atual, 'FRETES')}",
            font=("Segoe UI", 8), foreground="#555")
        lbl_info.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 2))

        lbl_status = ttkb.Label(f_cfg, text="", font=("Segoe UI", 9, "bold"))
        lbl_status.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))

        def _atualizar_info(*_):
            p = var_pasta.get().strip()
            lbl_info.config(
                text=f"  Banco:    {os.path.join(p, 'fornecedores.db')}\n"
                     f"  Arquivos: {os.path.join(p, 'ARQUIVO')}\n"
                     f"  Fretes:   {os.path.join(p, 'FRETES')}")
        var_pasta.trace_add("write", _atualizar_info)

        def _testar():
            pasta = var_pasta.get().strip()
            if not os.path.isdir(pasta):
                lbl_status.config(text="❌ Pasta não encontrada ou inacessível.", foreground="#e74c3c")
                return
            try:
                _db = os.path.join(pasta, "fornecedores.db")
                c = _sqlite3_cfg.connect(_db, timeout=10)
                c.close()
                lbl_status.config(text="✅ Pasta acessível e banco OK!", foreground="#27ae60")
            except Exception as e:
                lbl_status.config(text=f"❌ Falha no banco: {e}", foreground="#e74c3c")

        def _salvar():
            pasta = var_pasta.get().strip()
            if not pasta:
                messagebox.showerror("Erro", "Informe uma pasta válida.", parent=janela_cfg)
                return
            if not os.path.isdir(pasta):
                if not messagebox.askyesno(
                    "Pasta não encontrada",
                    f"A pasta não está acessível no momento:\n{pasta}\n\nSalvar mesmo assim?",
                    parent=janela_cfg
                ):
                    return
            _cfg_w = configparser.ConfigParser()
            _cfg_w["banco"] = {"pasta": pasta}
            os.makedirs(_CONFIG_LOCAL_DIR, exist_ok=True)
            with open(_CONFIG_LOCAL_INI, "w", encoding="utf-8") as _fini:
                _cfg_w.write(_fini)
            _aplicar_pasta_base(pasta)
            try:
                inicializar_banco_fornecedores(DB_PATH, diretorio_atual)
                root.atualizar_cache_fornecedores()
                nova_lista = get_lista_nomes_fornecedores(DB_PATH)
                combo_forn['values'] = nova_lista
                combo_forn.master_list = nova_lista
            except Exception:
                pass
            messagebox.showinfo(
                "Configuração Salva",
                f"Pasta de trabalho:\n  {pasta}\n\n"
                f"Banco:    fornecedores.db\n"
                f"Arquivos: ARQUIVO\\\n"
                f"Fretes:   FRETES\\",
                parent=janela_cfg)
            janela_cfg.destroy()

        f_btns = ttkb.Frame(f_cfg)
        f_btns.grid(row=3, column=0, columnspan=2, pady=6)
        ttkb.Button(f_btns, text="🔌 Testar Acesso", command=_testar, bootstyle="info").pack(side="left", padx=5)
        ttkb.Button(f_btns, text="💾 Salvar",         command=_salvar, bootstyle="success").pack(side="left", padx=5)
        ttkb.Button(f_btns, text="Cancelar", command=janela_cfg.destroy, bootstyle="secondary").pack(side="left", padx=5)

        f_cfg.grid_columnconfigure(0, weight=1)

    def sair_seguro():
        root.ignorando_validacao = True
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", sair_seguro)

    f_header = ttkb.Frame(root, bootstyle="primary", padding=15); f_header.pack(fill="x", side="top")
    ttkb.Label(f_header, text="📑 ENGENHARIA DE CUSTOS", font=("Segoe UI", 18, "bold"), bootstyle="inverse-primary").pack(side="left")

    f_forn = ttkb.Frame(f_header, bootstyle="primary"); f_forn.pack(side="left", padx=15)
    ttkb.Label(f_forn, text="FORNECEDOR:", font=("Segoe UI", 10, "bold"), bootstyle="inverse-primary").pack(side="left", padx=5)
    
    combo_forn = ttk.Combobox(f_forn, values=lista_fornecedores, width=25, font=("Segoe UI", 10))
    combo_forn.master_list = lista_fornecedores
    combo_forn.pack(side="left")
    
    listbox_forn_window = None
    listbox_forn = None

    def close_listbox_forn(e=None):
        nonlocal listbox_forn_window
        if listbox_forn_window:
            listbox_forn_window.destroy()
            listbox_forn_window = None

    def check_global_click_forn(e):
        if listbox_forn_window and listbox_forn_window.winfo_exists():
            w = e.widget
            if w != combo_forn and str(w.winfo_toplevel()) != str(listbox_forn_window):
                close_listbox_forn()
    root.bind("<Button-1>", check_global_click_forn, add="+")

    def ao_trocar_fornecedor(event=None):
        forn_sel = combo_forn.get()
        dados = next((f for f in cache_fornecedores if str(f.get('fabricante', '')).strip() == forn_sel), None)
        if dados:
            novo_ipi = formatar_percentual(float(dados.get('ipi_calculo', 0)) * 100)
            novo_frete = formatar_percentual(float(dados.get('frete', 0)) * 100)
            novo_markup = formatar_percentual(float(dados.get('markup', 0)) * 100)
            
            var_markup_geral.set(f"{novo_markup}%")
            
            for r in linhas_nota: 
                r['var_ipi'].set(novo_ipi)
                r['var_frete'].set(novo_frete)
        atualizar_tudo_real_time()

    combo_forn.bind("<<ComboboxSelected>>", ao_trocar_fornecedor)

    def on_forn_keyrelease(event):
        nonlocal listbox_forn_window, listbox_forn
        if event.keysym in ['Up', 'Down', 'Return', 'Tab', 'Escape', 'Right', 'Left']: return
        
        termo = combo_forn.get().strip().upper()
        combo_forn['values'] = combo_forn.master_list 
        
        close_listbox_forn()
        if not termo: return
        
        filtrados = [f for f in combo_forn.master_list if termo in f.upper()]
        if not filtrados: return
        
        x = combo_forn.winfo_rootx()
        y = combo_forn.winfo_rooty() + combo_forn.winfo_height()

        listbox_forn_window = tk.Toplevel(combo_forn)
        listbox_forn_window.wm_overrideredirect(True)
        listbox_forn_window.geometry(f"350x150+{x}+{y}")
        listbox_forn_window.attributes('-topmost', True)

        frame = tk.Frame(listbox_forn_window, borderwidth=1, relief="solid")
        frame.pack(fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame, orient=VERTICAL)
        bg_list = "white" if getattr(root, 'tema_atual', 'claro') == 'claro' else "#2e3440"
        fg_list = "black" if getattr(root, 'tema_atual', 'claro') == 'claro' else "#eceff4"
        
        listbox_forn = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Segoe UI", 10), bg=bg_list, fg=fg_list, selectbackground="#3498DB", selectforeground="white")
        scrollbar.config(command=listbox_forn.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        listbox_forn.pack(side=LEFT, fill=BOTH, expand=True)

        for f in filtrados:
            listbox_forn.insert(END, f)

        def select_item_forn(ev=None):
            if not listbox_forn.curselection(): return "break"
            selecionado = listbox_forn.get(listbox_forn.curselection())
            combo_forn.set(selecionado)
            close_listbox_forn()
            ao_trocar_fornecedor(None) 
            pular_foco(ent_pedido)
            return "break"
            
        listbox_forn.bind("<Double-Button-1>", select_item_forn)
        listbox_forn.bind("<Return>", select_item_forn)
        listbox_forn.bind("<Escape>", close_listbox_forn)
        
        def check_scroll_click_forn(e):
            if e.widget == scrollbar: return
            root.after(100, lambda: close_listbox_forn() if listbox_forn_window and root.focus_get() != listbox_forn and root.focus_get() != scrollbar else None)
        listbox_forn.bind("<FocusOut>", check_scroll_click_forn)

    def handle_keys_forn(e):
        nonlocal listbox_forn_window, listbox_forn
        if listbox_forn_window and listbox_forn:
            if e.keysym == 'Down':
                listbox_forn.focus_set()
                listbox_forn.selection_set(0)
                return "break"
            elif e.keysym == 'Escape':
                close_listbox_forn()
                return "break"
        if e.keysym in ['Return', 'Tab']:
            close_listbox_forn()

    combo_forn.bind('<KeyRelease>', on_forn_keyrelease)
    combo_forn.bind('<Down>', handle_keys_forn)
    combo_forn.bind('<Escape>', handle_keys_forn)
    combo_forn.bind('<Return>', lambda e: [close_listbox_forn(), pular_foco(ent_pedido)])

    tk.Button(f_forn, text="⚙️ Gerenciar", bg="#f39c12", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, cursor="hand2", command=lambda: abrir_gerenciador_fornecedores(root, combo_forn, DB_PATH)).pack(side="left", padx=10)
    tk.Button(f_forn, text="🔗 De-Para", bg="#17A589", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, cursor="hand2", command=lambda: abrir_gerenciador_de_para(root, DB_PATH)).pack(side="left", padx=2)

    f_pedido = ttkb.Frame(f_header, bootstyle="primary"); f_pedido.pack(side="left", padx=15)
    ttkb.Label(f_pedido, text="PEDIDO FDC:", font=("Segoe UI", 10, "bold"), bootstyle="inverse-primary").pack(side="left", padx=5)
    ent_pedido = ttkb.Entry(f_pedido, textvariable=var_pedido, width=12, font=("Segoe UI", 10, "bold"), justify="center")
    ent_pedido.pack(side="left")

    f_regime = ttkb.Frame(f_header, bootstyle="primary"); f_regime.pack(side="left", padx=15)
    ttkb.Label(f_regime, text="REGIME:", font=("Segoe UI", 10, "bold"), bootstyle="inverse-primary").pack(side="left", padx=5)
    combo_regime = ttk.Combobox(f_regime, textvariable=var_regime, values=["MISTA (NF + Romaneio)", "100% NOTA FISCAL", "NOTA + BONIFICAÇÃO"], width=22, font=("Segoe UI", 10, "bold"), state="readonly")
    combo_regime.pack(side="left")
    
    def alternar_tema():
        if root.tema_atual == "claro":
            root.tema_atual = "escuro"
            root.style.theme_use('darkly')
            btn_tema.config(text="☀️", bg="#f39c12", fg="black")
        else:
            root.tema_atual = "claro"
            root.style.theme_use('litera')
            btn_tema.config(text="🌙", bg="#2c3e50", fg="white")
        atualizar_estilos()
        
        bg_canvas = "#21252e" if root.tema_atual == 'escuro' else "white"
        bg_grid = "#1a1c23" if root.tema_atual == 'escuro' else "#7F8C8D"
        c_head = "#2e3440" if root.tema_atual == 'escuro' else "white"
        fg_dados = "#eceff4" if root.tema_atual == 'escuro' else "black"
        
        c_id, c_id_ro, c_nf, c_rom, c_frete, c_fdc, c_venda, f_venda, f_e, f_nc = obter_cores_tabela()

        f_tabela_container.config(bg=bg_canvas); canvas.config(bg=bg_canvas); f_grid.config(bg=bg_grid)
        lbl_foot_txt.config(bg=c_head, fg=fg_dados); foot_vazio1.config(bg=c_head); foot_vazio2.config(bg=c_head)
        
        for cell, bg_c in [(foot_qtd_nf, c_nf), (foot_val_nf, c_nf), (foot_qtd_rom, c_rom), (foot_val_rom, c_rom), (foot_estoque, c_fdc)]:
            cell.config(bg=bg_c, readonlybackground=bg_c, fg=f_e); cell.bg_padrao = bg_c

        for rd in linhas_nota:
            rd['e_cod'].config(bg=c_id, fg=f_e, insertbackground=f_e); rd['e_cod'].bg_padrao = c_id
            rd['e_nome'].config(bg=c_id_ro, readonlybackground=c_id_ro, fg=f_e); rd['e_nome'].bg_padrao = c_id_ro
            rd['e_qtd_nf'].config(bg=c_nf, fg=f_e, insertbackground=f_e); rd['e_qtd_nf'].bg_padrao = c_nf
            rd['e_unit_nf'].config(bg=c_nf, fg=f_e, insertbackground=f_e); rd['e_unit_nf'].bg_padrao = c_nf
            rd['e_ipi'].config(bg=c_nf, fg=f_e, insertbackground=f_e); rd['e_ipi'].bg_padrao = c_nf
            if 'e_qtd_rom' in rd and rd['e_qtd_rom'].winfo_exists(): 
                rd['e_qtd_rom'].config(bg=c_rom, fg=f_e, insertbackground=f_e); rd['e_qtd_rom'].bg_padrao = c_rom
                rd['e_unit_rom'].config(bg=c_rom, fg=f_e, insertbackground=f_e); rd['e_unit_rom'].bg_padrao = c_rom
            rd['e_frete'].config(bg=c_frete, fg=f_e, insertbackground=f_e); rd['e_frete'].bg_padrao = c_frete
            rd['e_estoque'].config(bg=c_fdc, readonlybackground=c_fdc, fg=f_e); rd['e_estoque'].bg_padrao = c_fdc
            rd['e_custo_atual'].config(bg=c_fdc, readonlybackground=c_fdc, fg=f_e); rd['e_custo_atual'].bg_padrao = c_fdc
            rd['e_novo_custo'].config(bg=c_fdc, fg=f_nc, insertbackground=f_nc); rd['e_novo_custo'].bg_padrao = c_fdc
            rd['e_venda_antiga'].config(bg=c_venda, readonlybackground=c_venda, fg=f_venda); rd['e_venda_antiga'].bg_padrao = c_venda
            rd['e_venda'].config(bg=c_venda, fg=f_venda, insertbackground=f_e); rd['e_venda'].bg_padrao = c_venda
            rd['e_prazo'].config(bg=c_venda, fg=f_venda, insertbackground=f_e); rd['e_prazo'].bg_padrao = c_venda
            rd['e_mkp'].config(bg=c_venda, readonlybackground=c_venda, fg=f_venda); rd['e_mkp'].bg_padrao = c_venda

        if _logo_rgba and lbl_logo:
            try:
                hex_bg = style.colors.bg
                if not hex_bg.startswith("#"):
                    hex_bg = "#" + hex_bg
                _img = _criar_logo_img(_logo_rgba, hex_bg)
                lbl_logo.config(image=_img, bg=hex_bg)
                lbl_logo.image = _img
            except Exception:
                pass

        _inicializar_marca_dagua()

    tk.Button(f_header, text="✖ Sair", bg="#FF0000", activebackground="#CC0000", activeforeground="white", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2", padx=15, pady=5, command=sair_seguro).pack(side="right")
    btn_tema = tk.Button(f_header, text="🌙", bg="#2c3e50", fg="white", font=("Segoe UI", 12), relief=tk.FLAT, cursor="hand2", padx=8, command=alternar_tema)
    btn_tema.pack(side="right", padx=10)
    tk.Button(f_header, text="⚙️ Banco", bg="#2980b9", activebackground="#1a6090", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, cursor="hand2", padx=10, command=abrir_config_banco).pack(side="right", padx=5)

    # ÁREA DE NOTA — layout adaptativo à resolução
    f_dados_nota = ttkb.Frame(root, padding=(8, 4))
    f_dados_nota.pack(fill="x", side="top", padx=20)

    _tela_larga = root.winfo_screenwidth() >= 1500

    if _tela_larga:
        # Linha única para telas largas (≥1500px)
        col = 0
        lbl_nota = ttkb.Label(f_dados_nota, text="Nº DA NOTA:", font=("Segoe UI", 9, "bold"))
        lbl_nota.grid(row=0, column=col, sticky="w", padx=(0, 2)); col += 1
        ToolTip(lbl_nota, text="Atalho: Ctrl + N")
        ent_nota = ttkb.Entry(f_dados_nota, textvariable=var_num_nota, width=15, font=("Segoe UI", 10))
        ent_nota.grid(row=0, column=col, sticky="w", padx=(0, 16)); col += 1
        ToolTip(ent_nota, text="Atalho: Ctrl + N")
        ttkb.Label(f_dados_nota, text="DT. EMISSÃO:", font=("Segoe UI", 9, "bold")).grid(row=0, column=col, sticky="w", padx=(0, 2)); col += 1
        ent_emissao = ttkb.Entry(f_dados_nota, textvariable=var_dt_emissao, width=12, font=("Segoe UI", 10), justify="center")
        ent_emissao.grid(row=0, column=col, sticky="w", padx=(0, 16)); col += 1
        ttkb.Label(f_dados_nota, text="DT. CHEGADA:", font=("Segoe UI", 9, "bold")).grid(row=0, column=col, sticky="w", padx=(0, 2)); col += 1
        ent_chegada = ttkb.Entry(f_dados_nota, textvariable=var_dt_chegada, width=12, font=("Segoe UI", 10), justify="center")
        ent_chegada.grid(row=0, column=col, sticky="w", padx=(0, 16)); col += 1
        ttkb.Label(f_dados_nota, text="TIPO DE FRETE:", font=("Segoe UI", 9, "bold")).grid(row=0, column=col, sticky="w", padx=(0, 2)); col += 1
        combo_frete = ttk.Combobox(f_dados_nota, textvariable=var_tipo_frete, values=["FOB", "CIF", "TERCEIRIZADO"], width=14, state="readonly", font=("Segoe UI", 10))
        combo_frete.grid(row=0, column=col, sticky="w", padx=(0, 16)); col += 1
        ttkb.Label(f_dados_nota, text="VLR TERCEIRO:", font=("Segoe UI", 9, "bold")).grid(row=0, column=col, sticky="w", padx=(0, 2)); col += 1
        ent_val_terceiro = ttkb.Entry(f_dados_nota, textvariable=var_val_terceirizado, width=12, font=("Segoe UI", 10, "bold"), justify="right", state="disabled")
        ent_val_terceiro.grid(row=0, column=col, sticky="w", padx=(0, 16)); col += 1
        ttkb.Label(f_dados_nota, text="MARKUP (%):", font=("Segoe UI", 9, "bold")).grid(row=0, column=col, sticky="w", padx=(0, 2)); col += 1
        ent_mkp_geral = ttkb.Entry(f_dados_nota, textvariable=var_markup_geral, width=8, font=("Segoe UI", 10, "bold"), justify="center")
        ent_mkp_geral.grid(row=0, column=col, sticky="w")
    else:
        # Duas linhas para telas menores (<1500px)
        # Linha 0: Nota | Emissão | Chegada
        lbl_nota = ttkb.Label(f_dados_nota, text="Nº DA NOTA:", font=("Segoe UI", 9, "bold"))
        lbl_nota.grid(row=0, column=0, sticky="w", padx=(0, 2), pady=(0, 4))
        ToolTip(lbl_nota, text="Atalho: Ctrl + N")
        ent_nota = ttkb.Entry(f_dados_nota, textvariable=var_num_nota, width=15, font=("Segoe UI", 10))
        ent_nota.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=(0, 4))
        ToolTip(ent_nota, text="Atalho: Ctrl + N")
        ttkb.Label(f_dados_nota, text="DT. EMISSÃO:", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", padx=(0, 2), pady=(0, 4))
        ent_emissao = ttkb.Entry(f_dados_nota, textvariable=var_dt_emissao, width=12, font=("Segoe UI", 10), justify="center")
        ent_emissao.grid(row=0, column=3, sticky="w", padx=(0, 20), pady=(0, 4))
        ttkb.Label(f_dados_nota, text="DT. CHEGADA:", font=("Segoe UI", 9, "bold")).grid(row=0, column=4, sticky="w", padx=(0, 2), pady=(0, 4))
        ent_chegada = ttkb.Entry(f_dados_nota, textvariable=var_dt_chegada, width=12, font=("Segoe UI", 10), justify="center")
        ent_chegada.grid(row=0, column=5, sticky="w", pady=(0, 4))
        # Linha 1: Frete | Vlr Terceiro | Markup
        ttkb.Label(f_dados_nota, text="TIPO DE FRETE:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", padx=(0, 2))
        combo_frete = ttk.Combobox(f_dados_nota, textvariable=var_tipo_frete, values=["FOB", "CIF", "TERCEIRIZADO"], width=14, state="readonly", font=("Segoe UI", 10))
        combo_frete.grid(row=1, column=1, sticky="w", padx=(0, 20))
        ttkb.Label(f_dados_nota, text="VLR TERCEIRO:", font=("Segoe UI", 9, "bold")).grid(row=1, column=2, sticky="w", padx=(0, 2))
        ent_val_terceiro = ttkb.Entry(f_dados_nota, textvariable=var_val_terceirizado, width=12, font=("Segoe UI", 10, "bold"), justify="right", state="disabled")
        ent_val_terceiro.grid(row=1, column=3, sticky="w", padx=(0, 20))
        ttkb.Label(f_dados_nota, text="MARKUP (%):", font=("Segoe UI", 9, "bold")).grid(row=1, column=4, sticky="w", padx=(0, 2))
        ent_mkp_geral = ttkb.Entry(f_dados_nota, textvariable=var_markup_geral, width=8, font=("Segoe UI", 10, "bold"), justify="center")
        ent_mkp_geral.grid(row=1, column=5, sticky="w")

    def validar_fornecedor(event=None):
        if check_and_trap(not combo_forn.get().strip(), combo_forn, "Preencha o Fornecedor"): return "break"
    combo_forn.bind("<FocusOut>", lambda e: validar_fornecedor() if not safe_is_focused(combo_forn) else None)

    def validar_pedido(event=None):
        if check_and_trap(not var_pedido.get().strip(), ent_pedido, "Preencha o Pedido"): return "break"
        if event and getattr(event, 'keysym', '') in ['Return', 'Tab']: return pular_foco(combo_regime)
        
    ent_pedido.bind("<Return>", validar_pedido)
    ent_pedido.bind("<Tab>", validar_pedido)
    ent_pedido.bind("<FocusOut>", lambda e: validar_pedido() if not safe_is_focused(ent_pedido) else None)

    def nav_regime(event=None):
        if event and getattr(event, 'keysym', '') in ['Return', 'Tab']: return pular_foco(ent_nota)

    combo_regime.bind("<Return>", nav_regime)
    combo_regime.bind("<Tab>", nav_regime)

    def validar_saida_nota(event=None):
        if check_and_trap(not var_num_nota.get().strip(), ent_nota, "Preencha a Nota"): return "break"
        nota = var_num_nota.get().strip()
        is_carga_existente = root.arquivo_aberto_atual is not None
        if not is_carga_existente and check_nota_duplicada(nota, pasta_fretes):
            mostrar_balao_aviso(ent_nota, f"Nota {nota} duplicada na B-LOG!")
            var_num_nota.set("")
            root.after(10, ent_nota.focus_force)
            return "break"
        if event and getattr(event, 'keysym', '') in ['Return', 'Tab']: return pular_foco(ent_emissao)

    ent_nota.bind("<Return>", validar_saida_nota)
    ent_nota.bind("<Tab>", validar_saida_nota)
    ent_nota.bind("<FocusOut>", lambda e: validar_saida_nota() if not safe_is_focused(ent_nota) else None)

    def validar_data_real(var, widget, event=None):
        t = var.get().strip()
        if check_and_trap(not t, widget, "Campo obrigatório"): return "break"
        if check_and_trap(len(t) < 10, widget, "Use DD/MM/AAAA"): return "break"
        try:
            dt = datetime.strptime(t, "%d/%m/%Y")
            if var == var_dt_chegada:
                hoje = datetime.now()
                if check_and_trap(dt.month != hoje.month or dt.year != hoje.year, widget, f"Mês deve ser {hoje.month:02d}/{hoje.year}"):
                    var.set("")
                    return "break"
        except ValueError:
            mostrar_balao_aviso(widget, "Data inválida no calendário")
            var.set("")
            root.after(10, widget.focus_force)
            return "break"
        if event and getattr(event, 'keysym', '') in ['Return', 'Tab']:
            if var == var_dt_emissao: return pular_foco(ent_chegada)
            else: return pular_foco(combo_frete)

    ent_emissao.bind("<Return>", lambda e: validar_data_real(var_dt_emissao, ent_emissao, e))
    ent_emissao.bind("<Tab>", lambda e: validar_data_real(var_dt_emissao, ent_emissao, e))
    ent_emissao.bind("<FocusOut>", lambda e: validar_data_real(var_dt_emissao, ent_emissao) if not safe_is_focused(ent_emissao) else None)

    ent_chegada.bind("<Return>", lambda e: validar_data_real(var_dt_chegada, ent_chegada, e))
    ent_chegada.bind("<Tab>", lambda e: validar_data_real(var_dt_chegada, ent_chegada, e))
    ent_chegada.bind("<FocusOut>", lambda e: validar_data_real(var_dt_chegada, ent_chegada) if not safe_is_focused(ent_chegada) else None)

    def validar_frete_saida(event=None):
        if check_and_trap(not var_tipo_frete.get().strip(), combo_frete, "Escolha o frete"): return "break"
        if event and getattr(event, 'keysym', '') in ['Return', 'Tab']:
            tipo = var_tipo_frete.get().strip()
            if tipo == "TERCEIRIZADO": return pular_foco(ent_val_terceiro)
            elif tipo in ["CIF", "FOB"]: return pular_foco(ent_mkp_geral)

    combo_frete.bind("<Return>", validar_frete_saida)
    combo_frete.bind("<Tab>", validar_frete_saida)
    combo_frete.bind("<FocusOut>", lambda e: validar_frete_saida() if not safe_is_focused(combo_frete) else None)

    def ao_selecionar_frete(event=None, force=False):
        tipo = var_tipo_frete.get().strip()
        if tipo == "TERCEIRIZADO":
            ent_val_terceiro.config(state="normal")
            if not force:
                var_val_terceirizado.set("") 
                pular_foco(ent_val_terceiro)
        elif tipo in ["CIF", "FOB"]:
            if not force:
                var_val_terceirizado.set("R$ 0,00")
            ent_val_terceiro.config(state="disabled")
            if not force: pular_foco(ent_mkp_geral)
            
    combo_frete.bind("<<ComboboxSelected>>", ao_selecionar_frete)

    def nav_terceiro(event=None):
        var_val_terceirizado.set(formatar_moeda(converter_moeda(var_val_terceirizado.get())) if var_val_terceirizado.get() else "R$ 0,00")
        if event and getattr(event, 'keysym', '') in ['Return', 'Tab']:
            return pular_foco(ent_mkp_geral)
        
    ent_val_terceiro.bind("<Return>", nav_terceiro)
    ent_val_terceiro.bind("<Tab>", nav_terceiro)
    ent_val_terceiro.bind("<FocusOut>", lambda e: nav_terceiro())

    def ao_editar_markup_geral(event=None):
        v_limpo = var_markup_geral.get().replace('%', '').strip()
        val = converter_moeda(v_limpo)
        var_markup_geral.set(f"{formatar_percentual(val)}%")
        atualizar_tudo_real_time()
        if event and getattr(event, 'keysym', '') in ['Return', 'Tab']:
            if linhas_nota: return pular_foco(linhas_nota[0]['e_cod'])
            return "break"
        
    ent_mkp_geral.bind("<FocusOut>", ao_editar_markup_geral)
    ent_mkp_geral.bind("<Return>", ao_editar_markup_geral)
    ent_mkp_geral.bind("<Tab>", ao_editar_markup_geral)

    def aplicar_mascara_data(event, var, entry):
        if event.keysym in ['BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Tab', 'Return']: return
        texto = var.get()
        num = re.sub(r'\D', '', texto)[:8]
        formatado = ""
        if len(num) > 0: formatado += num[:2]
        if len(num) > 2: formatado += "/" + num[2:4]
        if len(num) > 4: formatado += "/" + num[4:]
        if texto != formatado:
            var.set(formatado)
            entry.icursor(tk.END)

    ent_emissao.bind("<KeyRelease>", lambda e: aplicar_mascara_data(e, var_dt_emissao, ent_emissao))
    ent_chegada.bind("<KeyRelease>", lambda e: aplicar_mascara_data(e, var_dt_chegada, ent_chegada))

    # =====================================================================
    # --- CONTAINER DA TABELA ---
    # =====================================================================
    f_tabela_container = tk.Frame(root, bg="white"); f_tabela_container.pack(fill="both", expand=True, side="top", padx=10, pady=5)
    canvas = tk.Canvas(f_tabela_container, bg="white", highlightthickness=0); scrollbar_y = ttkb.Scrollbar(f_tabela_container, orient="vertical", command=canvas.yview); scrollbar_x = ttkb.Scrollbar(f_tabela_container, orient="horizontal", command=canvas.xview)
    f_grid = tk.Frame(canvas, bg="#7F8C8D"); f_grid.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas.create_window((0, 0), window=f_grid, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set); scrollbar_y.pack(side="right", fill="y"); scrollbar_x.pack(side="bottom", fill="x"); canvas.pack(side="left", fill="both", expand=True)

    _marca_dagua_img = None
    _marca_dagua_id  = None

    def _inicializar_marca_dagua():
        nonlocal _marca_dagua_img, _marca_dagua_id
        try:
            img = Image.open(_get_recurso("Bruno.png")).convert("RGBA")
            max_w = 420
            if img.width > max_w:
                img = img.resize((max_w, int(img.height * max_w / img.width)), Image.LANCZOS)
            bg_cor = "#21252e" if root.tema_atual == 'escuro' else "#ffffff"
            rr, gg, bb = int(bg_cor[1:3], 16), int(bg_cor[3:5], 16), int(bg_cor[5:7], 16)
            bg = Image.new("RGBA", img.size, (rr, gg, bb, 255))
            r_ch, g_ch, b_ch, a_ch = img.split()
            a_faded = a_ch.point(lambda x: int(x * 0.12))
            faded = Image.merge("RGBA", (r_ch, g_ch, b_ch, a_faded))
            bg.paste(faded, mask=faded.split()[3])
            _marca_dagua_img = ImageTk.PhotoImage(bg.convert("RGB"))
            cw = max(canvas.winfo_width(), 800)
            if _marca_dagua_id is None:
                _marca_dagua_id = canvas.create_image(cw // 2, 360, image=_marca_dagua_img, anchor="center", tags="watermark")
                canvas.tag_lower("watermark")
            else:
                canvas.itemconfig(_marca_dagua_id, image=_marca_dagua_img)
                canvas.coords(_marca_dagua_id, cw // 2, 360)
        except Exception:
            pass

    def _reposicionar_marca_dagua(event=None):
        if _marca_dagua_id:
            try:
                cw = canvas.winfo_width()
                coords = canvas.coords(_marca_dagua_id)
                canvas.coords(_marca_dagua_id, cw // 2, coords[1])
            except Exception:
                pass

    canvas.bind("<Configure>", _reposicionar_marca_dagua, add="+")

    labels_cabecalho_romaneio = []
    lbl_grupo_rom = None
    lbl_sub_qtd_rom = None
    lbl_sub_val_rom = None

    def criar_cabecalhos():
        nonlocal lbl_grupo_rom, lbl_sub_qtd_rom, lbl_sub_val_rom
        grupos = [("📦 PRODUTO", 0, 3, "SuperId.TLabel"), ("🧾 NF", 3, 3, "SuperNF.TLabel"), ("📋 ROMANEIO", 6, 2, "SuperRom.TLabel"), ("🚚 FRETE", 8, 1, "SuperFrete.TLabel"), ("🎯 CUSTO", 9, 3, "SuperRes.TLabel"), ("💰 PRECIFICAÇÃO SUGERIDA", 12, 4, "SuperVenda.TLabel")]
        for texto, col_inicio, span, estilo in grupos:
            lbl = ttk.Label(f_grid, text=texto, style=estilo, anchor="center", justify="center"); lbl.grid(row=0, column=col_inicio, columnspan=span, sticky="nsew", padx=1, pady=1, ipadx=5, ipady=8)
            if "ROMANEIO" in texto:
                labels_cabecalho_romaneio.append(lbl)
                lbl_grupo_rom = lbl

        colunas = [("Ação", 4, "SubId.TLabel"), ("Código", 8, "SubId.TLabel"), ("Nome do Produto", 50, "SubId.TLabel"), ("Qtd NF", 7, "SubNF.TLabel"), ("R$ Unit", 10, "SubNF.TLabel"), ("% IPI", 7, "SubNF.TLabel"), ("Qtd Rom", 7, "SubRom.TLabel"), ("R$ Rom", 10, "SubRom.TLabel"), ("% Frete", 7, "SubFrete.TLabel"), ("Estq", 6, "SubRes.TLabel"), ("Custo Ant", 10, "SubRes.TLabel"), ("NOVO CUSTO", 12, "SubRes.TLabel"), ("Venda Ant", 10, "SubVenda.TLabel"), ("VENDA (R$)", 12, "SubVenda.TLabel"), ("PRAZO (R$)", 12, "SubVenda.TLabel"), ("MKP REAL", 10, "SubVenda.TLabel")]
        for col, (texto, largura, estilo) in enumerate(colunas):
            lbl = ttk.Label(f_grid, text=texto, style=estilo, width=largura, anchor="center", justify="center"); lbl.grid(row=1, column=col, sticky="nsew", padx=1, pady=1, ipady=6)
            if "Rom" in texto:
                labels_cabecalho_romaneio.append(lbl)
                if "Qtd" in texto: lbl_sub_qtd_rom = lbl
                if "R$"  in texto: lbl_sub_val_rom = lbl

    criar_cabecalhos()
    root.after(300, _inicializar_marca_dagua)

    def criar_celula_digitavel(parent, row, col, var, width, justify, font, bg_color, fg_color="black"):
        campo = tk.Entry(parent, textvariable=var, width=width, justify=justify, font=font, bg=bg_color, fg=fg_color, relief="flat", insertbackground=fg_color)
        campo.grid(row=row, column=col, sticky="nsew", padx=1, pady=1, ipadx=4, ipady=4)
        campo.bg_padrao = bg_color
        def forcar_cor(e=None):
            try: campo.config(bg=campo.bg_padrao)
            except: pass
        campo.bind("<Configure>", forcar_cor, add="+")
        campo.bind("<FocusIn>", lambda e: [auto_selecionar(e), campo.config(bg="#f4f6ff" if root.tema_atual=='claro' else "#434c5e")], add="+")
        campo.bind("<FocusOut>", forcar_cor, add="+")
        campo.after(50, forcar_cor)
        return campo

    def criar_celula_blindada(parent, row, col, var, width, justify, font, bg_color, fg_color="black"):
        campo = tk.Entry(parent, textvariable=var, width=width, justify=justify, font=font, bg=bg_color, fg=fg_color, readonlybackground=bg_color, relief="flat", state="readonly", takefocus=0, cursor="arrow")
        campo.grid(row=row, column=col, sticky="nsew", padx=1, pady=1, ipadx=4, ipady=4)
        campo.bg_padrao = bg_color
        campo.bind("<Button-1>", lambda e: "break")
        def forcar_cor(e=None):
            try: campo.config(readonlybackground=campo.bg_padrao)
            except: pass
        campo.bind("<Configure>", forcar_cor, add="+")
        campo.after(50, forcar_cor)
        return campo

    var_tot_qtd_nf, var_tot_val_nf, var_tot_qtd_rom, var_tot_val_rom, var_tot_estoque = tk.StringVar(value="0"), tk.StringVar(value="R$ 0,00"), tk.StringVar(value="0"), tk.StringVar(value="R$ 0,00"), tk.StringVar(value="0")

    lbl_foot_txt = tk.Label(f_grid, text="TOTAIS PARCIAIS ➡", font=("Segoe UI", 10, "bold"), bg="white", fg="#2C3E50", anchor="e")
    foot_vazio1, foot_vazio2 = tk.Label(f_grid, text="", bg="white"), tk.Label(f_grid, text="", bg="white")
    
    foot_qtd_nf = criar_celula_blindada(f_grid, 1000, 3, var_tot_qtd_nf, 8, "center", ("Segoe UI", 11, "bold"), "#E3F2FD", "#2980b9")
    foot_val_nf = criar_celula_blindada(f_grid, 1000, 4, var_tot_val_nf, 12, "center", ("Segoe UI", 11, "bold"), "#E3F2FD", "#2980b9")
    foot_qtd_rom = criar_celula_blindada(f_grid, 1000, 6, var_tot_qtd_rom, 8, "center", ("Segoe UI", 11, "bold"), "#E8F5E9", "#27ae60")
    foot_val_rom = criar_celula_blindada(f_grid, 1000, 7, var_tot_val_rom, 12, "center", ("Segoe UI", 11, "bold"), "#E8F5E9", "#27ae60")
    foot_estoque = criar_celula_blindada(f_grid, 1000, 9, var_tot_estoque, 8, "center", ("Segoe UI", 11, "bold"), "#F3E5F5", "#8e44ad")

    def posicionar_rodape_tabela():
        r = indice_linha_atual
        lbl_foot_txt.grid(row=r, column=2, sticky="nsew", padx=1, pady=10); foot_qtd_nf.grid(row=r, column=3, sticky="nsew", padx=1, pady=10); foot_val_nf.grid(row=r, column=4, sticky="nsew", padx=1, pady=10); foot_vazio1.grid(row=r, column=5, sticky="nsew", padx=1, pady=10); foot_vazio2.grid(row=r, column=8, sticky="nsew", padx=1, pady=10); foot_estoque.grid(row=r, column=9, sticky="nsew", padx=1, pady=10)
        regime = var_regime.get()
        if regime == "MISTA (NF + Romaneio)":
            foot_qtd_rom.grid(row=r, column=6, sticky="nsew", padx=1, pady=10)
            foot_val_rom.grid(row=r, column=7, sticky="nsew", padx=1, pady=10)
        elif regime == "NOTA + BONIFICAÇÃO":
            foot_qtd_rom.grid(row=r, column=6, sticky="nsew", padx=1, pady=10)
            foot_val_rom.grid(row=r, column=7, sticky="nsew", padx=1, pady=10)
        else:
            foot_qtd_rom.grid_remove()
            foot_val_rom.grid_remove()

    def atualizar_tudo_real_time(*args):
        t_qtd_nf = t_val_nf_total = t_ipi_total = t_qtd_rom = t_val_rom_total = t_frete_total = t_estoque = t_custo_carga = 0.0; sucessos = 0
        regime = var_regime.get()
        
        v_limpo = var_markup_geral.get().replace('%', '').strip()
        markup_fator = converter_moeda(v_limpo) / 100.0

        for r in linhas_nota:
            try:
                if not r['var_cod'].get().strip() or r['var_nome'].get() in ["---", "❌ PRODUTO NÃO ENCONTRADO"]:
                    r['var_novo_custo'].set("R$ 0,00"); r['var_venda'].set("R$ 0,00"); r['var_prazo'].set("R$ 0,00"); r['var_mkp_real'].set("0,00%"); continue
                q_nf, u_nf, ipi_perc, frete_perc = converter_moeda(r['var_qtd_nf'].get()), converter_moeda(r['var_unit_nf'].get()), converter_moeda(r['var_ipi'].get()), converter_moeda(r['var_frete'].get())
                est_ant, custo_ant = r['val_estoque'], r['val_custo_atual']
                novo_c = 0.0

                if regime == "100% NOTA FISCAL":
                    q_fisica = q_nf
                    val_mercadoria_bruto = q_nf * u_nf
                elif regime == "NOTA + BONIFICAÇÃO":
                    q_bon = converter_moeda(r['var_qtd_rom'].get())
                    q_fisica = q_nf + q_bon
                    val_mercadoria_bruto = q_nf * u_nf
                else:  # MISTA
                    q_fisica = converter_moeda(r['var_qtd_rom'].get())
                    val_mercadoria_bruto = q_fisica * converter_moeda(r['var_unit_rom'].get())

                if q_nf > 0 and q_fisica > 0:
                    val_nf_base = u_nf * q_nf
                    v_ipi      = val_nf_base * (ipi_perc / 100)

                    if regime == "NOTA + BONIFICAÇÃO":
                        q_bon          = converter_moeda(r['var_qtd_rom'].get())
                        u_bon          = converter_moeda(r['var_unit_rom'].get()) or u_nf  # usa R$ Bon ou cai no unit NF
                        base_nf_c_ipi  = val_nf_base + v_ipi
                        frete_nf       = base_nf_c_ipi * (frete_perc / 100)
                        base_bon       = q_bon * u_bon          # sem IPI, usa preço do campo R$ Bon
                        frete_bon      = base_bon * (frete_perc / 100)
                        custo_linha    = val_nf_base + v_ipi + frete_nf + frete_bon
                        v_frete        = frete_nf + frete_bon
                    else:
                        base_mais_ipi  = val_mercadoria_bruto + v_ipi
                        v_frete        = base_mais_ipi * (frete_perc / 100)
                        custo_linha    = base_mais_ipi + v_frete

                    custo_calculado = ((est_ant * custo_ant) + custo_linha) / (est_ant + q_fisica)
                    
                    if r.get('custo_editado', False):
                        novo_c = converter_moeda(r['var_novo_custo'].get())
                    else:
                        novo_c = custo_calculado
                        r['var_novo_custo'].set(formatar_moeda(novo_c))
                        
                    custo_arredondado = round(novo_c, 4)
                    if 'last_novo_c' not in r: r['last_novo_c'] = 0.0
                    if 'last_markup' not in r: r['last_markup'] = -1.0
                    
                    if abs(custo_arredondado - r['last_novo_c']) > 0.001 or abs(markup_fator - r['last_markup']) > 0.001:
                        r['last_novo_c'] = custo_arredondado; r['last_markup'] = markup_fator; r['venda_editada'] = False; r['prazo_editado'] = False
                    
                    if not r['venda_editada']:
                        preco_sugerido = novo_c * (1 + markup_fator); venda_arredondada = arredondar_preco(preco_sugerido, novo_c, markup_fator); r['var_venda'].set(formatar_moeda(venda_arredondada))
                        if not r['prazo_editado']:
                            real_mkp_auto = (venda_arredondada / novo_c) - 1 if novo_c > 0 else 0
                            p_calc = venda_arredondada if round(real_mkp_auto, 4) >= 1.30 else (venda_arredondada + 100 if novo_c > 1000 else venda_arredondada + 50)
                            r['var_prazo'].set(formatar_moeda(p_calc))
                    venda_atual = converter_moeda(r['var_venda'].get()); mkp_real = ((venda_atual / novo_c) - 1) * 100 if novo_c > 0 else 0
                    r['var_mkp_real'].set(formatar_percentual(mkp_real) + "%")
                    sucessos += 1; t_qtd_nf += q_nf; t_val_nf_total += val_nf_base; t_ipi_total += v_ipi; t_qtd_rom += q_fisica; t_val_rom_total += val_mercadoria_bruto; t_frete_total += v_frete; t_estoque += est_ant; t_custo_carga += custo_linha
                else: 
                    if not r.get('custo_editado', False): r['var_novo_custo'].set("R$ 0,00")
                    r['var_mkp_real'].set("0,00%")
                    if not r['venda_editada']: r['var_venda'].set("R$ 0,00")
                    if not r['prazo_editado']: r['var_prazo'].set("R$ 0,00")
            except Exception as ex: r['var_novo_custo'].set("ERRO")

        var_tot_qtd_nf.set(f"{t_qtd_nf:g}"); var_tot_val_nf.set(formatar_moeda(t_val_nf_total)); var_tot_qtd_rom.set(f"{t_qtd_rom:g}"); var_tot_val_rom.set(formatar_moeda(t_val_rom_total)); var_tot_estoque.set(f"{t_estoque:g}")
        t_base = t_val_rom_total if regime == "MISTA (NF + Romaneio)" else t_val_nf_total
        lbl_res_formula.config(text=f"Itens: {sucessos}  | Prod: {formatar_moeda(t_base)}  +  IPI: {formatar_moeda(t_ipi_total)}  =  {formatar_moeda(t_base+t_ipi_total)}  +  Frete: {formatar_moeda(t_frete_total)}  =  CUSTO TOTAL CARGA: {formatar_moeda(t_custo_carga)}")
        root.total_mercadoria_compra, root.total_frete_compra, root.total_ipi_compra = t_base, t_frete_total, t_ipi_total

    def alternar_regime(*args):
        regime = var_regime.get()
        if regime == "100% NOTA FISCAL":
            for lbl in labels_cabecalho_romaneio: lbl.grid_remove()
            for r in linhas_nota: r['e_qtd_rom'].grid_remove(); r['e_unit_rom'].grid_remove()
        elif regime == "MISTA (NF + Romaneio)":
            if lbl_grupo_rom:    lbl_grupo_rom.config(text="📋 ROMANEIO")
            if lbl_sub_qtd_rom:  lbl_sub_qtd_rom.config(text="Qtd Rom")
            if lbl_sub_val_rom:  lbl_sub_val_rom.config(text="R$ Rom"); lbl_sub_val_rom.grid()
            for lbl in labels_cabecalho_romaneio: lbl.grid()
            for r in linhas_nota: r['e_qtd_rom'].grid(); r['e_unit_rom'].grid()
        elif regime == "NOTA + BONIFICAÇÃO":
            if lbl_grupo_rom:    lbl_grupo_rom.config(text="🎁 BONIFICAÇÃO")
            if lbl_sub_qtd_rom:  lbl_sub_qtd_rom.config(text="Qtd Bon")
            if lbl_sub_val_rom:  lbl_sub_val_rom.config(text="R$ Bon"); lbl_sub_val_rom.grid()
            for lbl in labels_cabecalho_romaneio: lbl.grid()
            for r in linhas_nota: r['e_qtd_rom'].grid(); r['e_unit_rom'].grid()
        posicionar_rodape_tabela(); atualizar_tudo_real_time()

    combo_regime.bind("<<ComboboxSelected>>", alternar_regime)

    # --- FUNÇÃO SEGURA PARA FOCAR A QTD APÓS O ENTER ---
    def focus_qtd(w):
        try:
            if w.winfo_exists():
                w.focus_set()
                w.focus_force()
                w.select_range(0, tk.END)
                w.icursor(tk.END)
        except:
            pass

    # === AUTOCOMPLETE BLINDADO PARA PRODUTOS ===
    def criar_autocomplete_codigo(entry_widget, var_cod, row_data):
        listbox_window = None
        listbox = None
        entry_widget.lista_aberta = False

        def close_listbox(e=None):
            nonlocal listbox_window
            entry_widget.lista_aberta = False
            if listbox_window:
                listbox_window.destroy()
                listbox_window = None

        def check_global_click(e):
            if listbox_window and listbox_window.winfo_exists():
                w = e.widget
                if w != entry_widget and str(w.winfo_toplevel()) != str(listbox_window):
                    close_listbox()
        root.bind("<Button-1>", check_global_click, add="+")

        def update_listbox(e):
            nonlocal listbox_window, listbox
            if e.keysym in ['Up', 'Down', 'Return', 'Escape', 'Tab']: return
            termo = var_cod.get().strip().upper()
            close_listbox()
            if len(termo) < 2 or not cache_fdc['carregado']: return
            df = cache_fdc['basico']
            if df.empty or '_cod_str' not in df.columns or '_nome_str' not in df.columns: return

            mask = df['_cod_str'].str.contains(termo, case=False, na=False) | df['_nome_str'].str.contains(termo, case=False, na=False)
            resultados = df[mask].head(15)

            if resultados.empty: return

            entry_widget.lista_aberta = True
            x = entry_widget.winfo_rootx()
            y = entry_widget.winfo_rooty() + entry_widget.winfo_height()

            listbox_window = tk.Toplevel(entry_widget)
            listbox_window.wm_overrideredirect(True)
            listbox_window.geometry(f"500x150+{x}+{y}")
            listbox_window.attributes('-topmost', True)

            frame = tk.Frame(listbox_window, borderwidth=1, relief="solid")
            frame.pack(fill=BOTH, expand=True)

            scrollbar = ttk.Scrollbar(frame, orient=VERTICAL)
            bg_list = "white" if getattr(root, 'tema_atual', 'claro') == 'claro' else "#2e3440"
            fg_list = "black" if getattr(root, 'tema_atual', 'claro') == 'claro' else "#eceff4"

            listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Segoe UI", 10), bg=bg_list, fg=fg_list, selectbackground="#3498DB", selectforeground="white")
            scrollbar.config(command=listbox.yview)
            scrollbar.pack(side=RIGHT, fill=Y)
            listbox.pack(side=LEFT, fill=BOTH, expand=True)

            for _, r in resultados.iterrows(): listbox.insert(END, f"{r['_cod_str']} - {r['_nome_str']}")

            def select_item(event=None):
                if not listbox or not listbox.winfo_exists() or not listbox.curselection():
                    return "break"
                selecionado = listbox.get(listbox.curselection())
                cod_selecionado = selecionado.split(' - ')[0].strip()
                var_cod.set(cod_selecionado)
                # BLINDAGEM CONTRA O CRASH DO TKINTER (SEGFAULT)
                root.after(10, close_listbox)
                if buscar_produto(row_data):
                    root.after(50, lambda: focus_qtd(row_data['e_qtd_nf']))
                return "break"

            listbox.bind("<Double-Button-1>", select_item)
            listbox.bind("<Return>", select_item)
            listbox.bind("<Escape>", close_listbox)

            def check_scroll_click(e):
                if e.widget == scrollbar: return
                root.after(100, lambda: close_listbox() if listbox_window and root.focus_get() != listbox and root.focus_get() != scrollbar else None)
            listbox.bind("<FocusOut>", check_scroll_click)

            def handle_keys(e):
                if listbox_window and listbox:
                    if e.keysym == 'Down':
                        listbox.focus_set()
                        listbox.selection_set(0)
                        return "break"
                    elif e.keysym == 'Return':
                        if listbox.size() > 0:
                            listbox.selection_set(0)
                            select_item()
                        return "break"
                    elif e.keysym == 'Escape':
                        close_listbox()
                        return "break"

            def on_entry_return(e):
                if listbox_window and listbox and listbox.winfo_exists() and listbox.size() > 0:
                    listbox.selection_set(0)
                    select_item()
                    return "break"

            entry_widget.force_select_first = on_entry_return
            entry_widget.bind('<Down>', handle_keys)
            entry_widget.bind('<Escape>', handle_keys)

        entry_widget.bind('<KeyRelease>', update_listbox)

    def buscar_produto(row_data):
        codigo = row_data['var_cod'].get().strip()
        if not codigo or not cache_fdc['carregado']: return False
        df_bas, df_pos, achou = cache_fdc['basico'], cache_fdc['posicao'], False
        if not df_bas.empty and '_cod_str' in df_bas.columns:
            filtro = df_bas[df_bas['_cod_str'] == codigo]
            if not filtro.empty:
                achou = True; col_n = next((c for c in ['DESCRICAOPRODUTO', 'NOME', 'PRODUTO'] if c in df_bas.columns), None); col_c = next((c for c in ['CUSTOMEDIO', 'CUSTO'] if c in df_bas.columns), None)
                row_data['var_nome'].set(str(filtro[col_n].iloc[0]) if col_n else ""); v_c = str(filtro[col_c].iloc[0]).replace('R$','').strip() if col_c else "0"
                if ',' in v_c and '.' in v_c: v_c = v_c.replace('.', '').replace(',', '.')
                else: v_c = v_c.replace(',', '.')
                try: row_data['val_custo_atual'] = float(v_c)
                except: row_data['val_custo_atual'] = 0.0
                
                try:
                    if len(df_bas.columns) > 5:
                        v_va = str(filtro.iloc[0, 5]).replace('R$','').strip()
                        if ',' in v_va and '.' in v_va: v_va = v_va.replace('.', '').replace(',', '.')
                        else: v_va = v_va.replace(',', '.')
                        row_data['var_venda_antiga'].set(formatar_moeda(float(v_va)))
                except: pass
                    
        if achou and not df_pos.empty and '_cod_str' in df_pos.columns:
            f_p = df_pos[df_pos['_cod_str'] == codigo]; col_q = next((c for c in ['QGERENCIAL', 'QGEREN', 'ESTOQUE', 'QUANTIDADE'] if c in df_pos.columns), None)
            row_data['val_estoque'] = pd.to_numeric(f_p[col_q].astype(str).str.replace(',', '.'), errors='coerce').sum() if not f_p.empty and col_q else 0.0
        if achou:
            row_data['var_estoque'].set(f"{row_data['val_estoque']:g}"); row_data['var_custo_atual'].set(formatar_moeda(row_data['val_custo_atual'])); atualizar_tudo_real_time(); return True
        row_data['var_nome'].set("❌ Produto não encontrado"); return False

    def adicionar_linha(evento=None):
        nonlocal indice_linha_atual
        r = indice_linha_atual; ipi_p, frete_p = "0,00", "0,00"; forn_sel = combo_forn.get()
        if forn_sel:
            dados = next((f for f in cache_fornecedores if str(f.get('fabricante', '')).strip() == forn_sel), None)
            if dados: ipi_p, frete_p = formatar_percentual(float(dados.get('ipi_calculo', 0)) * 100), formatar_percentual(float(dados.get('frete', 0)) * 100)
        rd = {'linha_idx': r, 'var_cod': tk.StringVar(), 'var_nome': tk.StringVar(value="---"), 'var_qtd_nf': tk.StringVar(), 'var_unit_nf': tk.StringVar(), 'var_ipi': tk.StringVar(value=ipi_p), 'var_qtd_rom': tk.StringVar(), 'var_unit_rom': tk.StringVar(), 'var_frete': tk.StringVar(value=frete_p), 'var_estoque': tk.StringVar(value="0"), 'var_custo_atual': tk.StringVar(value="R$ 0,00"), 'var_novo_custo': tk.StringVar(value="R$ 0,00"), 'var_venda_antiga': tk.StringVar(value="R$ 0,00"), 'val_estoque': 0.0, 'val_custo_atual': 0.0, 'var_venda': tk.StringVar(value="R$ 0,00"), 'var_prazo': tk.StringVar(value="R$ 0,00"), 'var_mkp_real': tk.StringVar(value="0,00%"), 'venda_editada': False, 'prazo_editado': False, 'custo_editado': False, 'last_novo_c': 0.0, 'last_markup': -1.0}
        for v in ['var_qtd_nf', 'var_unit_nf', 'var_ipi', 'var_qtd_rom', 'var_unit_rom', 'var_frete']: rd[v].trace_add("write", atualizar_tudo_real_time)
        btn_del = tk.Button(f_grid, text="X", fg="white", bg="#e74c3c", font=("Segoe UI", 8, "bold"), relief="flat", command=lambda: remover_linha(rd))
        btn_del.grid(row=r, column=0, sticky="nsew", padx=1, pady=1); rd['btn_del'] = btn_del
        
        c_id, c_id_ro, c_nf, c_rom, c_frete, c_fdc, c_venda, f_venda, f_ent, f_nc = obter_cores_tabela()

        rd['e_cod'] = criar_celula_digitavel(f_grid, r, 1, rd['var_cod'], 8, "center", ("Segoe UI", 10), c_id, f_ent)
        criar_autocomplete_codigo(rd['e_cod'], rd['var_cod'], rd)

        rd['e_nome'] = criar_celula_blindada(f_grid, r, 2, rd['var_nome'], 50, "left", ("Segoe UI", 8), c_id_ro, f_ent) 
        rd['e_qtd_nf'] = criar_celula_digitavel(f_grid, r, 3, rd['var_qtd_nf'], 7, "center", ("Segoe UI", 10), c_nf, f_ent)
        rd['e_unit_nf'] = criar_celula_digitavel(f_grid, r, 4, rd['var_unit_nf'], 10, "center", ("Segoe UI", 10), c_nf, f_ent)
        rd['e_ipi'] = criar_celula_digitavel(f_grid, r, 5, rd['var_ipi'], 7, "center", ("Segoe UI", 10), c_nf, f_ent) 
        rd['e_qtd_rom'] = criar_celula_digitavel(f_grid, r, 6, rd['var_qtd_rom'], 7, "center", ("Segoe UI", 10), c_rom, f_ent)
        rd['e_unit_rom'] = criar_celula_digitavel(f_grid, r, 7, rd['var_unit_rom'], 10, "center", ("Segoe UI", 10), c_rom, f_ent)
        rd['e_frete'] = criar_celula_digitavel(f_grid, r, 8, rd['var_frete'], 7, "center", ("Segoe UI", 10), c_frete, f_ent) 
        rd['e_estoque'] = criar_celula_blindada(f_grid, r, 9, rd['var_estoque'], 6, "center", ("Segoe UI", 10), c_fdc, f_ent)
        rd['e_custo_atual'] = criar_celula_blindada(f_grid, r, 10, rd['var_custo_atual'], 10, "center", ("Segoe UI", 10), c_fdc, f_ent)
        
        rd['e_novo_custo'] = criar_celula_digitavel(f_grid, r, 11, rd['var_novo_custo'], 12, "center", ("Segoe UI", 11, "bold"), c_fdc, f_nc)
        rd['e_novo_custo'].config(takefocus=0) 
        
        rd['e_venda_antiga'] = criar_celula_blindada(f_grid, r, 12, rd['var_venda_antiga'], 10, "center", ("Segoe UI", 10), c_venda, f_venda)
        rd['e_venda'] = criar_celula_digitavel(f_grid, r, 13, rd['var_venda'], 12, "center", ("Segoe UI", 11, "bold"), c_venda, f_venda)
        rd['e_prazo'] = criar_celula_digitavel(f_grid, r, 14, rd['var_prazo'], 12, "center", ("Segoe UI", 11, "bold"), c_venda, f_venda)
        rd['e_mkp'] = criar_celula_blindada(f_grid, r, 15, rd['var_mkp_real'], 10, "center", ("Segoe UI", 10, "bold"), c_venda, f_venda)

        rd['e_unit_nf'].bind("<FocusOut>", lambda e, v=rd['var_unit_nf']: v.set(formatar_moeda(converter_moeda(v.get())) if v.get().strip() else ""))
        rd['e_unit_rom'].bind("<FocusOut>", lambda e, v=rd['var_unit_rom']: v.set(formatar_moeda(converter_moeda(v.get())) if v.get().strip() else ""))
        rd['e_ipi'].bind("<FocusOut>", lambda e, v=rd['var_ipi']: v.set(formatar_percentual(converter_moeda(v.get()))))
        rd['e_frete'].bind("<FocusOut>", lambda e, v=rd['var_frete']: v.set(formatar_percentual(converter_moeda(v.get()))))

        def ao_digitar_custo(e, d): 
            if e.keysym not in ('Tab', 'Return', 'Left', 'Right', 'Up', 'Down', 'Shift_L', 'Shift_R'):
                d['custo_editado'] = True
                d['venda_editada'] = False 
                d['prazo_editado'] = False 
        rd['e_novo_custo'].bind("<Key>", lambda e, d=rd: ao_digitar_custo(e, d))
        
        def validar_custo_manual(e, d):
            v_custo = converter_moeda(d['var_novo_custo'].get()) 
            if v_custo > 0: d['var_novo_custo'].set(formatar_moeda(v_custo))
            else: d['custo_editado'] = False 
            atualizar_tudo_real_time()

        rd['e_novo_custo'].bind("<FocusOut>", lambda e, d=rd: validar_custo_manual(e, d))
        rd['e_novo_custo'].bind("<Return>", lambda e, d=rd: pular_foco(d['e_venda']))

        def ao_digitar_venda(e, d): 
            if e.keysym not in ('Tab', 'Return', 'Left', 'Right', 'Up', 'Down', 'Shift_L', 'Shift_R'):
                d['venda_editada'] = True; d['prazo_editado'] = False 
        rd['e_venda'].bind("<Key>", lambda e, d=rd: ao_digitar_venda(e, d))
        
        def validar_venda_manual(e, d):
            v_venda = converter_moeda(d['var_venda'].get()); novo_c = converter_moeda(d['var_novo_custo'].get()) 
            if v_venda > 0:
                d['var_venda'].set(formatar_moeda(v_venda))
                if not d['prazo_editado']:
                    real_mkp = (v_venda / novo_c) - 1 if novo_c > 0 else 0
                    p_calc = v_venda if round(real_mkp, 4) >= 1.30 else (v_venda + 100 if novo_c > 1000 else v_venda + 50)
                    d['var_prazo'].set(formatar_moeda(p_calc))
            else: d['venda_editada'] = False 
            atualizar_tudo_real_time()

        rd['e_venda'].bind("<FocusOut>", lambda e, d=rd: validar_venda_manual(e, d))

        def ao_digitar_prazo(e, d): 
            if e.keysym not in ('Tab', 'Return', 'Left', 'Right', 'Up', 'Down', 'Shift_L', 'Shift_R'): d['prazo_editado'] = True
        rd['e_prazo'].bind("<Key>", lambda e, d=rd: ao_digitar_prazo(e, d))

        def validar_prazo_manual(e, d):
            v_prazo = converter_moeda(d['var_prazo'].get())
            if v_prazo > 0: d['var_prazo'].set(formatar_moeda(v_prazo))
            else: d['prazo_editado'] = False
        
        rd['e_prazo'].bind("<FocusOut>", lambda e, d=rd: validar_prazo_manual(e, d))

        def tentar_avancar(e, d):
            if getattr(d['e_cod'], 'lista_aberta', False):
                if hasattr(d['e_cod'], 'force_select_first'):
                    d['e_cod'].force_select_first(e)
                return "break"
                
            if buscar_produto(d): 
                root.after(50, lambda: focus_qtd(d['e_qtd_nf']))
            else: 
                root.after(50, lambda: focus_qtd(d['e_cod']))
                mostrar_balao_aviso(d['e_cod'], "Produto não encontrado")
            return "break"
                
        rd['e_cod'].bind("<Return>", lambda e, d=rd: tentar_avancar(e, d))
        rd['e_cod'].bind("<Tab>", lambda e, d=rd: tentar_avancar(e, d))
        rd['e_cod'].bind("<FocusOut>", lambda e, d=rd: buscar_produto(d), add="+")
        
        rd['e_qtd_nf'].bind("<Return>", lambda e, d=rd: pular_foco(d['e_unit_nf']))
        rd['e_qtd_nf'].bind("<Tab>", lambda e, d=rd: pular_foco(d['e_unit_nf']))
        
        rd['e_unit_nf'].bind("<Return>", lambda e, d=rd: pular_foco(d['e_ipi']))
        rd['e_unit_nf'].bind("<Tab>", lambda e, d=rd: pular_foco(d['e_ipi']))
        
        def nav_ipi(e, d):
            proximo = d['e_frete'] if var_regime.get() == "100% NOTA FISCAL" else d['e_qtd_rom']
            return pular_foco(proximo)
            
        rd['e_ipi'].bind("<Return>", lambda e, d=rd: nav_ipi(e, d))
        rd['e_ipi'].bind("<Tab>", lambda e, d=rd: nav_ipi(e, d))
        
        rd['e_qtd_rom'].bind("<Return>", lambda e, d=rd: pular_foco(d['e_unit_rom']))
        rd['e_qtd_rom'].bind("<Tab>", lambda e, d=rd: pular_foco(d['e_unit_rom']))
        
        rd['e_unit_rom'].bind("<Return>", lambda e, d=rd: pular_foco(d['e_frete']))
        rd['e_unit_rom'].bind("<Tab>", lambda e, d=rd: pular_foco(d['e_frete']))
        
        rd['e_frete'].bind("<Return>", lambda e, d=rd: pular_foco(d['e_venda']))
        rd['e_frete'].bind("<Tab>", lambda e, d=rd: pular_foco(d['e_venda']))

        rd['e_venda'].bind("<Return>", lambda e, d=rd: pular_foco(d['e_prazo']))
        rd['e_venda'].bind("<Tab>", lambda e, d=rd: pular_foco(d['e_prazo']))

        def finalizar_linha(e):
            adicionar_linha()
            return "break"
            
        rd['e_prazo'].bind("<Return>", finalizar_linha)
        rd['e_prazo'].bind("<Tab>", finalizar_linha)

        if var_regime.get() == "100% NOTA FISCAL": rd['e_qtd_rom'].grid_remove(); rd['e_unit_rom'].grid_remove()
        elif var_regime.get() == "NOTA + BONIFICAÇÃO": rd['e_qtd_rom'].grid(); rd['e_unit_rom'].grid()
            
        linhas_nota.append(rd); indice_linha_atual += 1; posicionar_rodape_tabela()
        if len(linhas_nota) > 1: pular_foco(rd['e_cod'])

    def remover_linha(rd):
        for k in rd:
            if hasattr(rd[k], 'destroy'): rd[k].destroy()
        if rd in linhas_nota: linhas_nota.remove(rd)
        atualizar_tudo_real_time(); posicionar_rodape_tabela()

    def limpar_nota(pergunta=True, add_linha=True):
        nonlocal indice_linha_atual
        if linhas_nota and pergunta:
            if not messagebox.askyesno("Limpar Nota", "Deseja apagar todos os produtos?"): return
        root.ignorando_validacao = True
        for rd in list(linhas_nota): remover_linha(rd)
        combo_forn.set("")
        var_pedido.set("")
        var_regime.set("MISTA (NF + Romaneio)")
        alternar_regime()
        var_num_nota.set(""); var_dt_emissao.set(""); var_dt_chegada.set(""); var_tipo_frete.set(""); var_val_terceirizado.set("R$ 0,00"); var_markup_geral.set("0,00%")
        ent_val_terceiro.config(state="disabled")
        lbl_res_formula.config(text="Aguardando inserção de produtos...")
        root.arquivo_aberto_atual = None 
        indice_linha_atual = 2 
        if add_linha: adicionar_linha()
        root.ignorando_validacao = False
        root.after(50, combo_forn.focus_force)

    def carregar_arquivo_precificacao(caminho_arquivo):
        root.ignorando_validacao = True
        try:
            df = pd.read_excel(caminho_arquivo, engine='openpyxl')
            limpar_nota(pergunta=False, add_linha=False)
            nome_arq = os.path.basename(caminho_arquivo)
            root.arquivo_aberto_atual = caminho_arquivo

            def clean_str(val):
                s = str(val).strip()
                return "" if s.lower() == 'nan' else s

            if "NOTA" in df.columns: var_num_nota.set(clean_str(df["NOTA"].iloc[0]))
            if "EMISSAO" in df.columns: var_dt_emissao.set(clean_str(df["EMISSAO"].iloc[0]))
            if "CHEGADA" in df.columns: var_dt_chegada.set(clean_str(df["CHEGADA"].iloc[0]))
            if "VLR TERCEIRO" in df.columns: 
                val_terc = clean_str(df["VLR TERCEIRO"].iloc[0])
                if val_terc: var_val_terceirizado.set(val_terc)
            if "TIPO FRETE" in df.columns: 
                tipo_f = clean_str(df["TIPO FRETE"].iloc[0])
                if tipo_f:
                    var_tipo_frete.set(tipo_f)
                    ao_selecionar_frete(force=True)

            if "Qtd Bon" in df.columns: var_regime.set("NOTA + BONIFICAÇÃO")
            elif "Qtd Rom" in df.columns: var_regime.set("MISTA (NF + Romaneio)")
            else: var_regime.set("100% NOTA FISCAL")
            alternar_regime()

            for f in combo_forn.master_list:
                if f.replace(' ', '_').replace('/', '-') in nome_arq:
                    combo_forn.set(f)
                    ao_trocar_fornecedor(None) 
                    break
            
            match_ped = re.search(r'_PED_([\w\-]+)', nome_arq)
            if match_ped: var_pedido.set(match_ped.group(1).replace('_PENDENTE', ''))
            else: var_pedido.set("")

            for index, row in df.iterrows():
                adicionar_linha(); linha_atual = linhas_nota[-1] 
                linha_atual['var_cod'].set(str(row.get("Código", ""))); buscar_produto(linha_atual) 
                linha_atual['var_qtd_nf'].set(str(row.get("Qtd NF", ""))); linha_atual['var_unit_nf'].set(str(row.get("Unit. NF", "")))
                linha_atual['var_ipi'].set(str(row.get("% IPI", ""))); linha_atual['var_frete'].set(str(row.get("% Frete", "")))
                if var_regime.get() == "MISTA (NF + Romaneio)":
                    linha_atual['var_qtd_rom'].set(str(row.get("Qtd Rom", ""))); linha_atual['var_unit_rom'].set(str(row.get("Unit. Rom", "")))
                elif var_regime.get() == "NOTA + BONIFICAÇÃO":
                    linha_atual['var_qtd_rom'].set(str(row.get("Qtd Bon", "")))
                    linha_atual['var_unit_rom'].set(str(row.get("R$ Bon", "")))
                linha_atual['venda_editada'], linha_atual['prazo_editado'] = True, True
                linha_atual['var_venda_antiga'].set(str(row.get("Venda Ant", "R$ 0,00")))
                linha_atual['var_venda'].set(str(row.get("VENDA (R$)", "")))
                linha_atual['var_prazo'].set(str(row.get("PRAZO (R$)", "")))
            atualizar_tudo_real_time()
            messagebox.showinfo("Sucesso", "Precificação carregada com sucesso!")
        except Exception as e: messagebox.showerror("Erro", f"Não foi possível abrir o arquivo.\n\nDetalhes do erro: {e}")
        finally: root.ignorando_validacao = False

    def abrir_precificacao_salva():
        caminho_arquivo = filedialog.askopenfilename(initialdir=pasta_arquivo, title="Selecione a Precificação", filetypes=[("Arquivos Excel", "*.xlsx")])
        if not caminho_arquivo: return
        carregar_arquivo_precificacao(caminho_arquivo)

    def pesquisar_carga_salva():
        modal = tk.Toplevel(root)
        modal.title("Localizar Processo Salvo (Busca Rápida)")
        modal.geometry("850x550")
        modal.transient(root)
        modal.grab_set()
        
        bg_mod = "#ecf0f1" if root.tema_atual == 'claro' else "#2e3440"
        fg_mod = "black" if root.tema_atual == 'claro' else "white"
        modal.config(bg=bg_mod)

        f_busca = tk.Frame(modal, bg=bg_mod, pady=15, padx=15)
        f_busca.pack(fill="x", side="top")
        
        tk.Label(f_busca, text="🔍 Digite Nº da Nota, Pedido ou Fornecedor:", font=("Segoe UI", 11, "bold"), bg=bg_mod, fg=fg_mod).pack(side="left")
        ent_busca = ttkb.Entry(f_busca, font=("Segoe UI", 12), width=35)
        ent_busca.pack(side="left", padx=10)
        ent_busca.focus_set()

        f_lista = tk.Frame(modal, bg=bg_mod, padx=15, pady=5)
        f_lista.pack(fill="both", expand=True)

        colunas = ("Arquivo / Fornecedor", "Nota Fiscal", "Pedido", "Status")
        tree_busca = ttk.Treeview(f_lista, columns=colunas, show="headings")
        tree_busca.heading("Arquivo / Fornecedor", text="Fornecedor / Arquivo")
        tree_busca.heading("Nota Fiscal", text="Nota Fiscal")
        tree_busca.heading("Pedido", text="Pedido FDC")
        tree_busca.heading("Status", text="Status")
        
        tree_busca.column("Arquivo / Fornecedor", width=350, anchor="w")
        tree_busca.column("Nota Fiscal", width=120, anchor="center")
        tree_busca.column("Pedido", width=120, anchor="center")
        tree_busca.column("Status", width=150, anchor="center")

        scroll = ttk.Scrollbar(f_lista, orient="vertical", command=tree_busca.yview)
        tree_busca.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        tree_busca.pack(side="left", fill="both", expand=True)
        
        arquivos_na_pasta = glob.glob(os.path.join(pasta_arquivo, "*.xlsx"))
        arquivos_na_pasta.sort(key=os.path.getmtime, reverse=True)

        mapa_busca = {}

        def atualizar_lista(*args):
            termo = ent_busca.get().strip().upper()
            tree_busca.delete(*tree_busca.get_children())
            
            for arq in arquivos_na_pasta:
                nome_base = os.path.basename(arq).upper()
                if termo in nome_base or not termo:
                    is_pendente = "PENDENTE" in nome_base
                    status = "⚠️ PENDENTE" if is_pendente else "✅ AUDITADO"
                    
                    nf = ""
                    if "_NF_" in nome_base:
                        nf_part = nome_base.split("_NF_")[1]
                        nf = nf_part.split("_")[0].replace(".XLSX", "")
                    
                    ped = ""
                    if "_PED_" in nome_base:
                        ped_part = nome_base.split("_PED_")[1]
                        ped = ped_part.split("_")[0].replace(".XLSX", "")
                        
                    forn_nome = nome_base.split("_202")[0] if "_202" in nome_base else nome_base.split("_NF_")[0]
                    forn_nome = forn_nome.replace("_", " ")

                    if nome_base.startswith("~$"): continue

                    iid = tree_busca.insert("", "end", values=(forn_nome, nf, ped, status))
                    mapa_busca[iid] = arq
                    
        atualizar_lista()
        ent_busca.bind("<KeyRelease>", atualizar_lista)
        
        def carregar_selecionado(e=None):
            selecao = tree_busca.selection()
            if not selecao: return
            arq_selecionado = mapa_busca[selecao[0]]
            modal.destroy()
            carregar_arquivo_precificacao(arq_selecionado)
            
        tree_busca.bind("<Double-Button-1>", carregar_selecionado)
        tree_busca.bind("<Return>", carregar_selecionado)
        
        tk.Label(modal, text="💡 Dica: Dê um duplo clique no arquivo da lista para carregá-lo na tela.", font=("Segoe UI", 9, "italic"), bg=bg_mod, fg="#7f8c8d").pack(pady=10)

    def mostrar_pendencias():
        pendentes = glob.glob(os.path.join(pasta_arquivo, "*_PENDENTE.xlsx"))
        if not pendentes:
            messagebox.showinfo("Aviso", "Não há pedidos pendentes!")
            return
        modal = tk.Toplevel(root)
        modal.title("Auditoria Pendente")
        modal.geometry("600x400")
        modal.transient(root)
        modal.grab_set()
        lbl = tk.Label(modal, text="Selecione o pedido pendente para carregar e finalizar:", font=("Segoe UI", 11, "bold"))
        lbl.pack(pady=10)
        frame_list = tk.Frame(modal)
        frame_list.pack(fill="both", expand=True, padx=20, pady=5)
        style_pend = ttk.Style(modal)
        style_pend.configure("Pendencias.Treeview", rowheight=35, font=("Segoe UI", 11))
        style_pend.configure("Pendencias.Treeview.Heading", font=("Segoe UI", 11, "bold"))
        scrollbar = ttk.Scrollbar(frame_list, orient="vertical")
        tree_pend = ttk.Treeview(frame_list, columns=("Pedido",), show="headings", style="Pendencias.Treeview", yscrollcommand=scrollbar.set)
        tree_pend.heading("Pedido", text="Pedidos Aguardando Auditoria")
        tree_pend.column("Pedido", anchor="w", width=500)
        scrollbar.config(command=tree_pend.yview)
        scrollbar.pack(side="right", fill="y")
        tree_pend.pack(side="left", fill="both", expand=True)

        mapa_arquivos = {}
        for arq in pendentes:
            nome = os.path.basename(arq)
            display_name = nome.replace("_PENDENTE", "").replace(".xlsx", "").replace("_", " ")
            mapa_arquivos[display_name] = arq
            tree_pend.insert("", "end", values=(display_name,))

        def carregar_selecionado(e=None):
            selecao = tree_pend.selection()
            if not selecao:
                messagebox.showwarning("Aviso", "Selecione um pedido na lista.")
                return
            display_name = tree_pend.item(selecao[0], "values")[0]
            caminho_arquivo = mapa_arquivos[display_name]
            modal.destroy()
            carregar_arquivo_precificacao(caminho_arquivo)

        tree_pend.bind("<Double-Button-1>", carregar_selecionado)
        btn_carregar = tk.Button(modal, text="📥 CARREGAR PEDIDO SELECIONADO", bg="#f39c12", fg="white", font=("Segoe UI", 10, "bold"), command=carregar_selecionado)
        btn_carregar.pack(pady=15, fill="x", padx=20)

    # =====================================================================
    # --- AUDITORIA FINANCEIRA E EXPORTAÇÃO ---
    # =====================================================================
    def abrir_cofre_auditoria():
        def alerta_topo(msg, tipo="warning", titulo="Aviso"):
            top = tk.Toplevel() 
            top.geometry("0x0+0+0")
            top.attributes('-topmost', True)
            top.withdraw()
            
            if tipo == "warning": messagebox.showwarning(titulo, msg, parent=top)
            elif tipo == "error": messagebox.showerror(titulo, msg, parent=top)
            elif tipo == "info": messagebox.showinfo(titulo, msg, parent=top)
            
            try:
                top.destroy()
            except:
                pass

        try:
            if not combo_forn.get().strip(): 
                alerta_topo("Selecione o FORNECEDOR antes de auditar.")
                return 
            
            nota_atual = var_num_nota.get().strip()
            if not nota_atual:
                ent_nota.focus_force()
                alerta_topo("Preencha o NÚMERO DA NOTA!")
                return 
            
            is_carga_existente = root.arquivo_aberto_atual is not None
            if not is_carga_existente and check_nota_duplicada(nota_atual, pasta_fretes):
                alerta_topo(f"A Nota Fiscal nº {nota_atual} já está registrada na B-LOG!\n\nAuditoria bloqueada para evitar duplicidade.", "error", "Bloqueio de Segurança")
                return
                
            dt_emissao_str = var_dt_emissao.get().strip()
            dt_chegada_str = var_dt_chegada.get().strip()
            
            if not dt_emissao_str or not dt_chegada_str:
                ent_emissao.focus_force()
                alerta_topo("Preencha as DATAS DE EMISSÃO e CHEGADA!")
                return 
                
            try:
                dt_c = datetime.strptime(dt_chegada_str, "%d/%m/%Y")
                hoje = datetime.now()
                if dt_c.month != hoje.month or dt_c.year != hoje.year:
                    alerta_topo(f"A Data de Chegada ({dt_chegada_str}) deve ser do mês atual ({hoje.month:02d}/{hoje.year}).")
                    ent_chegada.focus_force()
                    return
            except ValueError:
                alerta_topo("A Data de Chegada é inválida!")
                ent_chegada.focus_force()
                return
                
            if not var_tipo_frete.get().strip():
                combo_frete.focus_force()
                alerta_topo("Selecione o TIPO DE FRETE!")
                return 
                
            if not linhas_nota or not linhas_nota[0]['var_cod'].get().strip(): 
                alerta_topo("Insira pelo menos um produto na nota!")
                return 
            
            tot_nf = getattr(root, 'total_mercadoria_compra', 0.0) + getattr(root, 'total_ipi_compra', 0.0)
            if tot_nf <= 0.01:
                alerta_topo("BLOQUEADO: Não é possível auditar uma nota com valor zerado!\n\nPreencha quantidades e valores na tabela.")
                return 
            
            modal = tk.Toplevel(root)
            modal.title("Auditoria Financeira")
            modal.geometry("1200x830")
            modal.transient(root)
            modal.grab_set()

            bg_mod    = "#0D2B45"
            bg_header = "#071F33"
            bg_secao  = "#0A3A6B"
            fg_gold   = "#F1C40F"
            fg_text   = "#FFFFFF"
            fg_muted  = "#AED6F1"
            modal.configure(bg=bg_mod)
            # força bg escuro em todos os widgets tk que não tenham cor explícita
            modal.option_add("*Background",       bg_mod,   70)
            modal.option_add("*Foreground",       fg_text,  70)
            modal.option_add("*selectColor",      bg_secao, 70)
            modal.option_add("*activeBackground", bg_secao, 70)
            modal.option_add("*activeForeground", fg_gold,  70)

            # estilos ttk para botões com texto branco bold
            _ms = ttkb.Style()
            _ms.configure("AuditW.warning.TButton", foreground="white", font=("Segoe UI", 10, "bold"))
            _ms.configure("AuditS.success.TButton", foreground="white", font=("Segoe UI", 10, "bold"))
            _ms.configure("AuditP.primary.TButton", foreground="white", font=("Segoe UI", 10, "bold"))
            _ms.configure("AuditD.dark.TButton",    foreground="white", font=("Segoe UI", 12, "bold"))
            _ms.configure("AuditB.info.TButton",    foreground="white", font=("Segoe UI", 10, "bold"))
            _ms.map("AuditW.warning.TButton", foreground=[("disabled", "#AAAAAA"), ("active", "white")])
            _ms.map("AuditS.success.TButton", foreground=[("disabled", "#AAAAAA"), ("active", "white")])
            _ms.map("AuditP.primary.TButton", foreground=[("disabled", "#AAAAAA"), ("active", "white")])
            _ms.map("AuditD.dark.TButton",    foreground=[("disabled", "#888888"), ("active", "white")])
            _ms.map("AuditB.info.TButton",    foreground=[("disabled", "#AAAAAA"), ("active", "white")])

            # --- Total (calculado antes do header) ---
            tipo_f = var_tipo_frete.get().strip()
            val_blog = 0.0
            if tipo_f == "CIF":
                txt_aviso = "FRETE CIF: ISENTA  (R$ 0,00)"
                fg_aviso = "#85929E"
            elif tipo_f == "FOB":
                frete_perc = converter_moeda(linhas_nota[0]['var_frete'].get()) / 100 if linhas_nota else 0
                val_blog = tot_nf * frete_perc
                txt_aviso = f"FRETE FOB: B-LOG  {formatar_moeda(val_blog)}"
                fg_aviso = "#2ECC71"
            else:
                txt_aviso = "FRETE TERCEIRIZADO"
                fg_aviso = "#E67E22"

            # --- Header compacto (2 linhas) ---
            f_header = tk.Frame(modal, bg=bg_header)
            f_header.pack(fill="x")
            f_row1 = tk.Frame(f_header, bg=bg_header)
            f_row1.pack(fill="x", padx=15, pady=(5, 1))
            tk.Label(f_row1, text="AUDITORIA FINANCEIRA", fg=fg_gold, bg=bg_header,
                     font=("Segoe UI", 10, "bold")).pack(side="left")
            tk.Label(f_row1, text="  —  " + combo_forn.get().upper(), fg="#AED6F1", bg=bg_header,
                     font=("Segoe UI", 9)).pack(side="left")
            f_row2 = tk.Frame(f_header, bg=bg_header)
            f_row2.pack(fill="x", padx=15, pady=(0, 5))
            tk.Label(f_row2, text="TOTAL:  ", fg=fg_muted, bg=bg_header,
                     font=("Segoe UI", 8, "bold")).pack(side="left")
            tk.Label(f_row2, text=formatar_moeda(tot_nf), fg=fg_gold, bg=bg_header,
                     font=("Segoe UI", 14, "bold")).pack(side="left")
            tk.Label(f_row2, text=f"     {txt_aviso}", fg=fg_aviso, bg=bg_header,
                     font=("Segoe UI", 9, "bold")).pack(side="left")
            tk.Frame(modal, bg=fg_gold, height=2).pack(fill="x")
            tk.Frame(modal, bg=bg_secao, height=1).pack(fill="x", padx=20, pady=(4, 0))
            
            tk.Label(modal, text="  FORMA DE PAGAMENTO", fg="white", bg=bg_secao,
                     font=("Segoe UI", 9, "bold"), anchor="w", pady=4
                     ).pack(fill="x", padx=20, pady=(8, 0))
            f_p = tk.Frame(modal, pady=4, bg=bg_mod)
            f_p.pack(fill="x", padx=20)
            var_pag = tk.StringVar(value="BOLETOS")
            f_b = tk.Frame(modal, pady=4, bg=bg_mod)
            f_status_bar = tk.Frame(modal, bg="white", pady=5,
                                    highlightthickness=1, highlightbackground=fg_gold)
            lbl_d = tk.Label(f_status_bar, text="DIFERENÇA: " + formatar_moeda(tot_nf),
                             font=("Segoe UI", 13, "bold"), fg="#E74C3C", bg="white")

            var_dinheiro = tk.StringVar(value="R$ 0,00")
            f_dinheiro = tk.Frame(f_b, bg=bg_mod)
            tk.Label(f_dinheiro, text="Entrada em Dinheiro:", width=18, anchor="e",
                     font=("Segoe UI", 10, "bold"), fg="#2ECC71", bg=bg_mod).pack(side="left")
            ent_dinheiro = tk.Entry(f_dinheiro, textvariable=var_dinheiro, width=16, justify="right",
                                    font=("Segoe UI", 10, "bold"), bg=bg_secao, fg=fg_gold,
                                    insertbackground="white", relief="flat", bd=5)
            ent_dinheiro.pack(side="left", padx=10, ipady=3)

            def format_dinheiro_entrada(e=None):
                val = var_dinheiro.get()
                if val: var_dinheiro.set(formatar_moeda(converter_moeda(val)))
            ent_dinheiro.bind("<FocusOut>", format_dinheiro_entrada)
            ent_dinheiro.bind("<Return>", format_dinheiro_entrada)

            def check():
                if var_pag.get() == "BLU / À VISTA":
                    f_b.pack_forget()
                    f_dinheiro.pack_forget()
                    lbl_d.config(text="✅ LIBERADO (BLU / À VISTA)", fg="#1A7A3E", bg="white")
                    btn_e.config(state="normal", bg="#C0392B", fg="white")
                elif var_pag.get() == "PENDENTES":
                    f_b.pack_forget()
                    f_dinheiro.pack_forget()
                    lbl_d.config(text="⚠️ LIBERADO COM PENDÊNCIA", fg="#B8600A", bg="white")
                    btn_e.config(state="normal", bg="#C0392B", fg="white")
                elif var_pag.get() == "DINHEIRO + BOLETO":
                    f_b.pack(fill="x", padx=20, before=f_status_bar)
                    f_dinheiro.pack(fill="x", pady=(0, 6), before=f_boletos)
                    recalcular()
                else:
                    f_b.pack(fill="x", padx=20, before=f_status_bar)
                    f_dinheiro.pack_forget()
                    var_dinheiro.set("R$ 0,00")
                    recalcular()
                    
            _rb = dict(bg=bg_mod, fg=fg_text, font=("Segoe UI", 10),
                       selectcolor=bg_secao, activebackground=bg_mod, activeforeground=fg_gold)
            tk.Radiobutton(f_p, text="BLU / Transferencia a Vista", variable=var_pag, value="BLU / À VISTA", command=check, **_rb).pack(anchor="w")
            tk.Radiobutton(f_p, text="Pagamento em Boletos",        variable=var_pag, value="BOLETOS",          command=check, **_rb).pack(anchor="w")
            tk.Radiobutton(f_p, text="Dinheiro + Boleto (Misto)",   variable=var_pag, value="DINHEIRO + BOLETO", command=check, **_rb).pack(anchor="w")
            tk.Radiobutton(f_p, text="Boletos Pendentes (Aguardando Retorno)", variable=var_pag, value="PENDENTES", command=check, **_rb).pack(anchor="w")
            
            f_boletos = tk.Frame(f_b, bg=bg_mod)
            f_boletos.pack(fill="x", pady=(4, 0))
            f_boletos_col1 = tk.Frame(f_boletos, bg=bg_mod)
            f_boletos_col1.pack(side="left", fill="both", expand=True, padx=(0, 6))
            tk.Frame(f_boletos, bg=bg_secao, width=2).pack(side="left", fill="y")
            f_boletos_col2 = tk.Frame(f_boletos, bg=bg_mod)
            f_boletos_col2.pack(side="left", fill="both", expand=True, padx=(6, 6))
            tk.Frame(f_boletos, bg=bg_secao, width=2).pack(side="left", fill="y")
            f_boletos_col3 = tk.Frame(f_boletos, bg=bg_mod)
            f_boletos_col3.pack(side="left", fill="both", expand=True, padx=(6, 0))

            vars_b = []
            entradas_b = []
            prazos = [30, 60, 90, 120, 150, 180, 210, 240, 270]

            def recalcular(*args):
                s_boletos = sum(converter_moeda(v.get()) for v in vars_b)
                v_dinheiro = converter_moeda(var_dinheiro.get()) if var_pag.get() == "DINHEIRO + BOLETO" else 0.0
                diff = tot_nf - v_dinheiro - s_boletos
                if abs(diff) < 0.05:
                    lbl_d.config(text="✅  BATEU!  R$ 0,00", fg="#1A7A3E", bg="white")
                    btn_e.config(state="normal",   bg="#C0392B", fg="white")
                else:
                    lbl_d.config(text="🔴  DIFERENÇA:  " + formatar_moeda(diff), fg="#c0392b", bg="white")
                    btn_e.config(state="disabled", bg="#7B241C")

            var_dinheiro.trace_add("write", recalcular)

            for _i in range(9):
                _var = tk.StringVar()
                vars_b.append(_var)
                _parent = f_boletos_col1 if _i < 3 else (f_boletos_col2 if _i < 6 else f_boletos_col3)
                _row = tk.Frame(_parent, bg=bg_mod)
                _row.pack(fill="x", pady=2)
                tk.Label(_row, text=f"Boleto {_i+1}  ({prazos[_i]} d):", width=17, anchor="e",
                         bg=bg_mod, fg=fg_muted, font=("Segoe UI", 9)).pack(side="left")
                _e = tk.Entry(_row, textvariable=_var, width=14, justify="right",
                              font=("Segoe UI", 10, "bold"), bg=bg_secao, fg=fg_gold,
                              insertbackground="white", relief="flat", bd=4)
                _e.pack(side="left", padx=6, ipady=3)
                _e.bind("<FocusOut>", lambda ev, v=_var: v.set(formatar_moeda(converter_moeda(v.get())) if v.get() else ""))
                _e.bind("<Return>", lambda ev, i=_i: entradas_b[i+1].focus_set() if i < 8 else btn_e.focus_set())
                _var.trace_add("write", recalcular)
                entradas_b.append(_e)
            entradas_b[0].focus_set()

            lbl_d.pack(pady=4)
            f_status_bar.pack(fill="x", padx=20, pady=(4, 2))
            
            # === GERAÇÃO DE IMAGENS PARA CLIPBOARD ===
            def _get_font_pil(size, bold=False):
                from PIL import ImageFont as _IF
                candidatos = [
                    (r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"),
                    r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
                ]
                for p in candidatos:
                    try: return _IF.truetype(p, size)
                    except: pass
                return _IF.load_default()

            def _gerar_imagem_chefe():
                from PIL import Image as _Im, ImageDraw as _ID
                C_BG     = (23,  32,  42)
                C_BG2    = (28,  40,  51)
                C_ROW    = (33,  47,  61)
                C_GOLD   = (241,196,  15)
                C_WHITE  = (236,240, 241)
                C_MUTED  = (189,195, 199)
                C_BLUE   = (174,214, 241)
                C_SEP    = (241,196,  15)
                W = 960; PAD = 22
                # Posições X dos centros das 5 colunas da direita
                X_CANT = W - 490   # CUSTO ANT
                X_CNOV = W - 375   # CUSTO NOVO
                X_VEND = W - 255   # VENDA
                X_PRZO = W - 135   # PRAZO
                X_MKP  = W - 32    # MARKUP (âncora direita)
                forn   = combo_forn.get()
                nf     = var_num_nota.get()
                pedido = var_pedido.get()
                data   = datetime.now().strftime("%d/%m/%Y")
                prods  = [
                    {"cod":       r["var_cod"].get().strip(),
                     "nome":      r["var_nome"].get(),
                     "preco_ant": r["var_venda_antiga"].get(),
                     "custo_ant": r["var_custo_atual"].get(),
                     "custo":     r["var_novo_custo"].get(),
                     "venda":     r["var_venda"].get(),
                     "prazo":     r["var_prazo"].get(),
                     "markup":    r["var_mkp_real"].get()}
                    for r in linhas_nota
                    if r["var_cod"].get().strip()
                    and r["var_nome"].get() not in ["---", "❌ PRODUTO NÃO ENCONTRADO"]
                ]
                fT = _get_font_pil(16, bold=True)
                fS = _get_font_pil(12)
                fP = _get_font_pil(13, bold=True)
                fV = _get_font_pil(12)
                fF = _get_font_pil(12, bold=True)
                HEADER_H = 100; SUB_H = 40; ROW_H = 78; FOOT_H = 56; SEP = 2
                H = HEADER_H + SUB_H + SEP + len(prods)*ROW_H + (max(0,len(prods)-1)*SEP) + FOOT_H
                img = _Im.new("RGB", (W, H), C_BG)
                d   = _ID.Draw(img)
                # Header
                d.rectangle([0,0,W,HEADER_H], fill=C_BG)
                d.text((PAD, 18), "RESUMO DE PRECIFICACAO", fill=C_GOLD, font=fT)
                d.text((PAD, 44), f"Fornecedor: {forn}", fill=C_BLUE, font=fS)
                d.text((PAD, 64), f"NF: {nf}   |   Pedido: {pedido}   |   {data}", fill=C_MUTED, font=fV)
                d.rectangle([0, HEADER_H, W, HEADER_H+SEP], fill=C_SEP)
                # Sub-header
                y = HEADER_H + SEP
                d.rectangle([0, y, W, y+SUB_H], fill=(19,27,36))
                d.text((PAD,    y+20), "PRODUTO",     fill=C_MUTED, font=fF, anchor="lm")
                d.text((X_CANT, y+20), "CUSTO ANT",   fill=C_MUTED, font=fF, anchor="mm")
                d.text((X_CNOV, y+20), "CUSTO NOVO",  fill=C_MUTED, font=fF, anchor="mm")
                d.text((X_VEND, y+20), "VENDA",       fill=C_MUTED, font=fF, anchor="mm")
                d.text((X_PRZO, y+20), "PRAZO",       fill=C_MUTED, font=fF, anchor="mm")
                d.text((X_MKP,  y+20), "MARKUP",      fill=C_MUTED, font=fF, anchor="rm")
                y += SUB_H
                # Produtos
                for i, p in enumerate(prods):
                    bg = C_BG2 if i%2==0 else C_ROW
                    d.rectangle([0, y, W, y+ROW_H], fill=bg)
                    texto = f"[{p['cod']}]  " + p["nome"]
                    max_w = X_CANT - PAD - 30
                    orig  = texto
                    while d.textlength(texto, font=fP) > max_w:
                        texto = texto[:-1]
                    if len(texto) < len(orig):
                        texto = texto[:-1] + "…"
                    mid = y + ROW_H // 2
                    d.text((PAD,    y+16), texto,              fill=C_WHITE, font=fP, anchor="lm")
                    d.text((PAD,    y+50), f"Preço ant: {p['preco_ant']}", fill=C_MUTED, font=fS, anchor="lm")
                    d.text((X_CANT, mid),  p["custo_ant"],     fill=C_MUTED, font=fP, anchor="mm")
                    d.text((X_CNOV, mid),  p["custo"],         fill=C_WHITE, font=fP, anchor="mm")
                    d.text((X_VEND, mid),  p["venda"],         fill=C_WHITE, font=fP, anchor="mm")
                    d.text((X_PRZO, mid),  p["prazo"],         fill=C_WHITE, font=fP, anchor="mm")
                    d.text((X_MKP,  mid),  p["markup"],        fill=C_GOLD,  font=fP, anchor="rm")
                    y += ROW_H
                    if i < len(prods)-1:
                        d.rectangle([0,y,W,y+SEP], fill=(40,55,71))
                        y += SEP
                # Footer
                d.rectangle([0, y, W, H], fill=C_BG)
                resumo = re.sub(r'Itens:\s*\d+\s*\|\s*','', lbl_res_formula.cget("text"))
                d.text((PAD, y+18), resumo, fill=C_MUTED, font=fF)
                return img

            def _gerar_imagem_lojas():
                from PIL import Image as _Im, ImageDraw as _ID
                C_BG   = (11, 61, 37)
                C_BG2  = (8,  46, 28)
                C_ROW  = (15, 77, 46)
                C_GOLD = (241,196, 15)
                C_WHITE= (236,240,241)
                C_MUTED= (161,221,192)
                C_SEP  = (39,174, 96)
                W = 760; PAD = 28
                forn   = combo_forn.get()
                data   = datetime.now().strftime("%d/%m/%Y")
                regime_av = var_regime.get()
                prods = []
                for r in linhas_nota:
                    if r["var_cod"].get().strip() and r["var_nome"].get() not in ["---", "❌ PRODUTO NÃO ENCONTRADO"]:
                        q_nf  = r["var_qtd_nf"].get()
                        q_bon = r["var_qtd_rom"].get()
                        if regime_av == "MISTA (NF + Romaneio)":
                            qtd = q_bon
                        elif regime_av == "NOTA + BONIFICAÇÃO":
                            try: tot = int(float(q_nf or 0)+float(q_bon or 0))
                            except: tot = "?"
                            qtd = str(tot)
                        else:
                            qtd = q_nf
                        prods.append({"cod": r["var_cod"].get().strip(),
                                      "nome": r["var_nome"].get(),
                                      "qtd": qtd,
                                      "venda": r["var_venda"].get(),
                                      "prazo": r["var_prazo"].get()})
                fT = _get_font_pil(16, bold=True)
                fS = _get_font_pil(13)
                fP = _get_font_pil(14, bold=True)
                fV = _get_font_pil(13)
                fF = _get_font_pil(13, bold=True)
                HEADER_H = 90; SUB_H = 40; ROW_H = 62; FOOT_H = 46; SEP = 2
                H = HEADER_H + SUB_H + SEP + len(prods)*ROW_H + (max(0,len(prods)-1)*SEP) + FOOT_H
                img = _Im.new("RGB", (W, H), C_BG)
                d   = _ID.Draw(img)
                # Header
                d.rectangle([0,0,W,HEADER_H], fill=C_BG2)
                d.text((PAD, 16), "AVISO DE NOVOS PRECOS", fill=C_GOLD, font=fT)
                d.text((PAD, 46), f"Fornecedor: {forn}   |   {data}", fill=C_MUTED, font=fS)
                d.rectangle([0, HEADER_H, W, HEADER_H+SEP], fill=C_SEP)
                # Sub-header
                y = HEADER_H + SEP
                d.rectangle([0,y,W,y+SUB_H], fill=(6,36,22))
                d.text((PAD,   y+20), "PRODUTO", fill=C_MUTED, font=fF, anchor="lm")
                d.text((W-260, y+20), "QTD",     fill=C_MUTED, font=fF, anchor="mm")
                d.text((W-155, y+20), "VENDA",   fill=C_MUTED, font=fF, anchor="mm")
                d.text((W-50,  y+20), "PRAZO",   fill=C_MUTED, font=fF, anchor="mm")
                y += SUB_H
                # Produtos
                for i, p in enumerate(prods):
                    bg = C_BG if i%2==0 else C_ROW
                    d.rectangle([0,y,W,y+ROW_H], fill=bg)
                    texto = f"[{p['cod']}]  " + p["nome"]
                    max_w = W - 310 - PAD - 10
                    orig  = texto
                    while d.textlength(texto, font=fP) > max_w:
                        texto = texto[:-1]
                    if len(texto) < len(orig):
                        texto = texto[:-1] + "…"
                    d.text((PAD,   y+31), texto,    fill=C_WHITE, font=fP, anchor="lm")
                    d.text((W-260, y+31), p["qtd"],   fill=C_WHITE, font=fP, anchor="mm")
                    d.text((W-155, y+31), p["venda"], fill=C_WHITE, font=fP, anchor="mm")
                    d.text((W-50,  y+31), p["prazo"], fill=C_WHITE, font=fP, anchor="mm")
                    y += ROW_H
                    if i < len(prods)-1:
                        d.rectangle([0,y,W,y+SEP], fill=(20,90,50))
                        y += SEP
                # Footer
                d.rectangle([0,y,W,H], fill=C_BG2)
                d.text((PAD, y+14), "Boas vendas!", fill=C_MUTED, font=fF)
                return img

            def copiar_resumo_area_transferencia():
                try:
                    img = _gerar_imagem_chefe()
                    _copiar_imagem_clipboard(img)
                    if not _dialogo_whatsapp_confirmar(modal, para_chefe=True):
                        return
                    _enviar_whatsapp_desktop(_ler_contato_chefe())
                    messagebox.showinfo("Enviado!", f"Resumo enviado para '{_ler_contato_chefe()}'.", parent=modal)
                except Exception as _ex:
                    messagebox.showerror("Erro", f"Nao foi possivel enviar o resumo:\n{_ex}")

            def copiar_aviso_lojas():
                try:
                    img = _gerar_imagem_lojas()
                    _copiar_imagem_clipboard(img)
                    if not _dialogo_whatsapp_confirmar(modal, para_lojas=True):
                        return
                    _enviar_whatsapp_desktop(_ler_grupo_whatsapp())
                    messagebox.showinfo("Enviado!", f"Aviso enviado para '{_ler_grupo_whatsapp()}'.", parent=modal)
                except Exception as _ex:
                    messagebox.showerror("Erro", f"Nao foi possivel enviar o aviso:\n{_ex}")

            def enviar_lojas_e_chefe():
                if not _dialogo_whatsapp_confirmar(modal, para_chefe=True, para_lojas=True):
                    return
                try:
                    import time as _t2
                    img_lojas = _gerar_imagem_lojas()
                    _copiar_imagem_clipboard(img_lojas)
                    _enviar_whatsapp_desktop(_ler_grupo_whatsapp())
                    _t2.sleep(3.0)
                    img_chefe = _gerar_imagem_chefe()
                    _copiar_imagem_clipboard(img_chefe)
                    _enviar_whatsapp_desktop(_ler_contato_chefe())
                    messagebox.showinfo("Enviado!", "Imagens enviadas para as lojas e para o chefe.", parent=modal)
                except Exception as _ex:
                    messagebox.showerror("Erro", f"Erro ao enviar:\n{_ex}")

            def executar_exportacao():
                root.status_pagamento = var_pag.get()
                root.val_dinheiro_entrada_salvo = var_dinheiro.get().strip() if var_pag.get() == "DINHEIRO + BOLETO" else "R$ 0,00"
                modal.destroy()
                
                itens_export = []
                for r in linhas_nota:
                    if r['var_cod'].get().strip() and r['var_nome'].get() not in ["---", "❌ PRODUTO NÃO ENCONTRADO"]:
                        linha_dict = {
                            "NOTA": var_num_nota.get().strip(),
                            "EMISSAO": var_dt_emissao.get().strip(),
                            "CHEGADA": var_dt_chegada.get().strip(),
                            "TIPO FRETE": var_tipo_frete.get().strip(),
                            "VLR TERCEIRO": var_val_terceirizado.get().strip(),
                            "Código": r['var_cod'].get(), 
                            "Produto": r['var_nome'].get(), 
                            "Qtd NF": r['var_qtd_nf'].get(), 
                            "Unit. NF": r['var_unit_nf'].get(), 
                            "% IPI": r['var_ipi'].get()
                        }
                        if var_regime.get() == "MISTA (NF + Romaneio)":
                            linha_dict.update({"Qtd Rom": r['var_qtd_rom'].get(), "Unit. Rom": r['var_unit_rom'].get()})
                        elif var_regime.get() == "NOTA + BONIFICAÇÃO":
                            linha_dict.update({"Qtd Bon": r['var_qtd_rom'].get(), "R$ Bon": r['var_unit_rom'].get()})

                        linha_dict.update({
                            "% Frete": r['var_frete'].get(),
                            "Estq Ant": r['var_estoque'].get(),
                            "Custo Ant": r['var_custo_atual'].get(),
                            "NOVO CUSTO": r['var_novo_custo'].get(),
                            "Venda Ant": r['var_venda_antiga'].get(),
                            "VENDA (R$)": r['var_venda'].get(),
                            "PRAZO (R$)": r['var_prazo'].get(),
                            "MKP REAL": r['var_mkp_real'].get()
                        })
                        itens_export.append(linha_dict)

                dados_exportacao = {
                    'forn': combo_forn.get().strip(),
                    'num_nota': var_num_nota.get().strip(),
                    'num_pedido': var_pedido.get().strip(),
                    'dt_emissao': var_dt_emissao.get().strip(),
                    'dt_chegada': var_dt_chegada.get().strip(),
                    'tipo_frete': var_tipo_frete.get().strip(),
                    'val_terceiro_str': var_val_terceirizado.get().strip(),
                    'regime': var_regime.get(),
                    'status_pagamento': root.status_pagamento,
                    'val_dinheiro_entrada': root.val_dinheiro_entrada_salvo,
                    'arquivo_aberto_atual': root.arquivo_aberto_atual,
                    'pasta_arquivo': pasta_arquivo,
                    'pasta_fretes': pasta_fretes,
                    'db_path': DB_PATH,
                    'resumo_texto': lbl_res_formula.cget("text"),
                    'total_mercadoria_compra': getattr(root, 'total_mercadoria_compra', 0.0),
                    'total_ipi_compra': getattr(root, 'total_ipi_compra', 0.0),
                    'total_frete_compra': getattr(root, 'total_frete_compra', 0.0),
                    'itens': itens_export
                }
                
                root.arquivo_aberto_atual = processar_exportacao_carga(dados_exportacao)
                atualizar_alerta_pendencias()
                alerta_topo("Planilha de Precificação gerada na pasta ARQUIVO!\nEspelho aberto no navegador.", "info", "Sucesso")
                
            tk.Frame(modal, bg=bg_secao, height=1).pack(fill="x", padx=20, pady=(4,0))
            f_botoes_modal = tk.Frame(modal, bg=bg_mod)
            f_botoes_modal.pack(fill="x", padx=20, pady=10)

            # Linha 1 — botões de imagem lado a lado
            f_linha1 = tk.Frame(f_botoes_modal, bg=bg_mod)
            f_linha1.pack(fill="x", pady=(0, 6))

            btn_copiar = ttkb.Button(f_linha1, text="IMAGEM RESUMO P/ CHEFE",
                                     style="AuditW.warning.TButton", cursor="hand2", padding=(0, 9),
                                     command=copiar_resumo_area_transferencia)
            btn_copiar.pack(side="left", fill="x", expand=True, padx=(0, 4))

            btn_aviso_lojas = ttkb.Button(f_linha1, text="IMAGEM AVISO PARA AS LOJAS",
                                          style="AuditS.success.TButton", cursor="hand2", padding=(0, 9),
                                          command=copiar_aviso_lojas)
            btn_aviso_lojas.pack(side="left", fill="x", expand=True, padx=(4, 0))

            # Linha 1b — enviar os dois de uma vez
            f_linha1b = tk.Frame(f_botoes_modal, bg=bg_mod)
            f_linha1b.pack(fill="x", pady=(0, 6))

            btn_enviar_ambos = ttkb.Button(f_linha1b, text="ENVIAR PARA LOJAS E PARA O CHEFE",
                                           style="AuditB.info.TButton", cursor="hand2", padding=(0, 9),
                                           command=enviar_lojas_e_chefe)
            btn_enviar_ambos.pack(fill="x")

            # Linha 2 — confirmar e gerar (largura total)
            f_linha2 = tk.Frame(f_botoes_modal, bg=bg_mod)
            f_linha2.pack(fill="x")

            btn_e = tk.Button(f_linha2, text="CONFIRMAR E GERAR PLANILHA",
                              bg="#C0392B", fg="white",
                              font=("Segoe UI", 12, "bold"),
                              activebackground="#E74C3C", activeforeground="white",
                              disabledforeground="#CCCCCC",
                              cursor="hand2", relief="flat", bd=0)
            btn_e.config(command=executar_exportacao)
            btn_e.pack(fill="x", ipady=10)
            check()
            
        except Exception as e:
            alerta_topo(f"Ocorreu um erro interno ao auditar a carga:\n\n{str(e)}", "error", "Erro Crítico")


    # =====================================================================
    # --- SALVAR EDIÇÃO DE PREÇOS (sem criar arquivo novo, sem tocar no BLOG) ---
    # =====================================================================
    def reimprimir_processo():
        """Salva preços editados NO MESMO arquivo e reabre o espelho HTML."""
        if not linhas_nota or not linhas_nota[0]['var_cod'].get().strip():
            messagebox.showwarning("Aviso", "Não há produtos na tela para salvar!")
            return

        if root.arquivo_aberto_atual is None:
            messagebox.showwarning("Aviso", "Nenhuma precificação salva está aberta.\nAbra um arquivo antes de usar esta função.")
            return

        itens_export = []
        for r in linhas_nota:
            if r['var_cod'].get().strip() and r['var_nome'].get() not in ["---", "❌ PRODUTO NÃO ENCONTRADO"]:
                linha_dict = {
                    "NOTA": var_num_nota.get().strip(),
                    "EMISSAO": var_dt_emissao.get().strip(),
                    "CHEGADA": var_dt_chegada.get().strip(),
                    "TIPO FRETE": var_tipo_frete.get().strip(),
                    "VLR TERCEIRO": var_val_terceirizado.get().strip(),
                    "Código": r['var_cod'].get(),
                    "Produto": r['var_nome'].get(),
                    "Qtd NF": r['var_qtd_nf'].get(),
                    "Unit. NF": r['var_unit_nf'].get(),
                    "% IPI": r['var_ipi'].get()
                }
                if var_regime.get() == "MISTA (NF + Romaneio)":
                    linha_dict.update({"Qtd Rom": r['var_qtd_rom'].get(), "Unit. Rom": r['var_unit_rom'].get()})
                elif var_regime.get() == "NOTA + BONIFICAÇÃO":
                    linha_dict.update({"Qtd Bon": r['var_qtd_rom'].get(), "R$ Bon": r['var_unit_rom'].get()})

                linha_dict.update({
                    "% Frete": r['var_frete'].get(),
                    "Estq Ant": r['var_estoque'].get(),
                    "Custo Ant": r['var_custo_atual'].get(),
                    "NOVO CUSTO": r['var_novo_custo'].get(),
                    "Venda Ant": r['var_venda_antiga'].get(),
                    "VENDA (R$)": r['var_venda'].get(),
                    "PRAZO (R$)": r['var_prazo'].get(),
                    "MKP REAL": r['var_mkp_real'].get()
                })
                itens_export.append(linha_dict)

        dados_edicao = {
            'arquivo_aberto_atual': root.arquivo_aberto_atual,
            'forn': combo_forn.get().strip(),
            'num_nota': var_num_nota.get().strip(),
            'num_pedido': var_pedido.get().strip(),
            'dt_emissao': var_dt_emissao.get().strip(),
            'dt_chegada': var_dt_chegada.get().strip(),
            'tipo_frete': var_tipo_frete.get().strip(),
            'val_terceiro_str': var_val_terceirizado.get().strip(),
            'regime': var_regime.get(),
            'status_pagamento': getattr(root, 'status_pagamento', 'N/A'),
            'resumo_texto': lbl_res_formula.cget("text"),
            'itens': itens_export
        }

        sucesso, mensagem = salvar_edicao_precos(dados_edicao)
        if sucesso:
            messagebox.showinfo("Salvo!", "Preços atualizados no arquivo original.\nEspelho HTML reaberto no navegador.")
        else:
            messagebox.showerror("Erro ao Salvar", mensagem)

    # ------------------------------------------------------------------
    # Helper reutilizável de confirmação de envio WhatsApp
    # ------------------------------------------------------------------
    def _dialogo_whatsapp_confirmar(parent, para_chefe=False, para_lojas=False):
        """Abre diálogo de confirmação de envio. Retorna True se ENVIAR clicado."""
        BG="#1A2535"; BG2="#223048"; BG3="#1B3A5C"
        GOLD="#F1C40F"; BLUE="#2471A3"; WHITE="#EAECEE"; MUTED="#AEB6BF"

        # Garante destinatários configurados antes de abrir o diálogo
        if para_lojas and not _ler_grupo_whatsapp():
            from tkinter import simpledialog as _sd
            g = _sd.askstring("WhatsApp", "Nome exato do grupo das lojas (ex: Ajuste de Preços):", parent=parent)
            if not g: return False
            _salvar_grupo_whatsapp(g.strip())
        if para_chefe and not _ler_contato_chefe():
            from tkinter import simpledialog as _sd
            c = _sd.askstring("WhatsApp", "Nome do contato do chefe no WhatsApp\n(ex: Edson Cordeiro):", parent=parent)
            if not c: return False
            _salvar_contato_chefe(c.strip())

        result = [False]
        n_linhas = (1 if para_chefe else 0) + (1 if para_lojas else 0)
        H_w = 270 + n_linhas * 30
        win = tk.Toplevel(parent)
        win.title("Confirmar Envio")
        win.resizable(False, False)
        win.grab_set()
        win.configure(bg=BG)
        win.option_add("*Background", BG)
        win.option_add("*Foreground", WHITE)
        try: win.iconbitmap(_get_recurso("icone.ico"))
        except: pass
        W_w = 460
        win.geometry(f"{W_w}x{H_w}+{parent.winfo_rootx()+(parent.winfo_width()-W_w)//2}+{parent.winfo_rooty()+(parent.winfo_height()-H_w)//2}")

        tk.Frame(win, bg=GOLD, height=5).pack(fill="x")

        # Título dentro de Frame para evitar fundo branco no Windows
        f_t = tk.Frame(win, bg=BG)
        f_t.pack(fill="x")
        tk.Label(f_t, text="CONFIRMAR ENVIO VIA WHATSAPP", bg=BG, fg=GOLD,
                 font=("Segoe UI", 13, "bold")).pack(pady=(16, 6))

        # Info dos destinatários
        refs = {}
        f_info = tk.Frame(win, bg=BG2)
        f_info.pack(fill="x", padx=28, pady=(4, 4))
        if para_lojas:
            refs['grupo'] = [_ler_grupo_whatsapp()]
            refs['lbl_lo'] = tk.StringVar(value=f"   Lojas  →  {refs['grupo'][0]}")
            tk.Label(f_info, textvariable=refs['lbl_lo'], bg=BG2, fg=WHITE,
                     font=("Segoe UI", 11), anchor="w", bd=0, highlightthickness=0
                     ).pack(fill="x", padx=14, pady=(10, 4))
        if para_chefe:
            refs['chefe'] = [_ler_contato_chefe()]
            refs['lbl_ch'] = tk.StringVar(value=f"   Chefe  →  {refs['chefe'][0]}")
            tk.Label(f_info, textvariable=refs['lbl_ch'], bg=BG2, fg=WHITE,
                     font=("Segoe UI", 11), anchor="w", bd=0, highlightthickness=0
                     ).pack(fill="x", padx=14, pady=(4, 10))

        def _editar():
            sub = tk.Toplevel(win)
            sub.title("Editar Destinatários")
            sub.resizable(False, False)
            sub.grab_set()
            sub.configure(bg=BG)
            sub.option_add("*Background", BG)
            sub.option_add("*Foreground", WHITE)
            try: sub.iconbitmap(_get_recurso("icone.ico"))
            except: pass
            Hs = 240 + n_linhas * 65
            Ws = 430
            sub.geometry(f"{Ws}x{Hs}+{win.winfo_rootx()+(win.winfo_width()-Ws)//2}+{win.winfo_rooty()+(win.winfo_height()-Hs)//2}")
            tk.Frame(sub, bg=GOLD, height=4).pack(fill="x")
            f_st = tk.Frame(sub, bg=BG)
            f_st.pack(fill="x")
            tk.Label(f_st, text="EDITAR DESTINATÁRIOS", bg=BG, fg=GOLD,
                     font=("Segoe UI", 12, "bold"), bd=0).pack(pady=(14, 10))
            f_form = tk.Frame(sub, bg=BG)
            f_form.pack(padx=28, fill="x")
            entries = {}
            row = 0
            if para_chefe:
                tk.Label(f_form, text="Contato do chefe:", bg=BG, fg=MUTED,
                         font=("Segoe UI", 10), bd=0).grid(row=row, column=0, sticky="w", pady=(0,2))
                row += 1
                ent = tk.Entry(f_form, font=("Segoe UI", 11), bg=BG3, fg=WHITE,
                               insertbackground=WHITE, relief="flat", bd=4)
                ent.grid(row=row, column=0, sticky="ew", ipady=7, pady=(0, 8))
                ent.insert(0, _ler_contato_chefe() or "")
                entries['chefe'] = ent; row += 1
            if para_lojas:
                tk.Label(f_form, text="Grupo das lojas:", bg=BG, fg=MUTED,
                         font=("Segoe UI", 10), bd=0).grid(row=row, column=0, sticky="w", pady=(0,2))
                row += 1
                ent = tk.Entry(f_form, font=("Segoe UI", 11), bg=BG3, fg=WHITE,
                               insertbackground=WHITE, relief="flat", bd=4)
                ent.grid(row=row, column=0, sticky="ew", ipady=7)
                ent.insert(0, _ler_grupo_whatsapp() or "")
                entries['lojas'] = ent; row += 1
            f_form.columnconfigure(0, weight=1)
            def _salvar_edit():
                if 'chefe' in entries:
                    c = entries['chefe'].get().strip()
                    if c: _salvar_contato_chefe(c); refs['chefe'][0]=c; refs['lbl_ch'].set(f"   Chefe  →  {c}")
                if 'lojas' in entries:
                    l = entries['lojas'].get().strip()
                    if l: _salvar_grupo_whatsapp(l); refs['grupo'][0]=l; refs['lbl_lo'].set(f"   Lojas  →  {l}")
                sub.destroy()
            _b_ok = tk.Button(sub, text="  OK  ", bg=BLUE, fg="white", font=("Segoe UI", 11, "bold"),
                              relief="flat", bd=0, highlightthickness=0, cursor="hand2",
                              activebackground="#1A6FA8", activeforeground="white",
                              command=_salvar_edit)
            _b_ca = tk.Button(sub, text="Cancelar", bg="#424242", fg=WHITE, font=("Segoe UI", 11),
                              relief="flat", bd=0, highlightthickness=0, cursor="hand2",
                              activebackground="#555555", activeforeground="white",
                              command=sub.destroy)
            _b_ok.place(x=24, y=Hs - 52, width=130, height=38)
            _b_ca.place(x=Ws - 24 - 110, y=Hs - 52, width=110, height=38)

        f_eb2 = tk.Frame(win, bg=BG)
        f_eb2.pack(fill="x", padx=28, pady=(6, 2))
        tk.Button(f_eb2, text="✏  EDITAR DESTINATÁRIOS", bg=BG3, fg=WHITE,
                  font=("Segoe UI", 10), relief="flat", bd=0,
                  padx=12, pady=7, cursor="hand2",
                  activebackground="#1A4A72", activeforeground=WHITE,
                  command=_editar).pack(fill="x")

        # Botões colocados diretamente no Toplevel com place() — sem container intermediário
        # O fundo do Toplevel (BG) aparece entre eles sem branco
        _b_env = tk.Button(win, text="  ENVIAR  ", bg=BLUE, fg="white",
                           font=("Segoe UI", 12, "bold"), relief="flat", bd=0, highlightthickness=0,
                           cursor="hand2", activebackground="#1A6FA8", activeforeground="white",
                           command=lambda: (result.__setitem__(0, True), win.destroy()))
        _b_can = tk.Button(win, text="Cancelar", bg="#424242", fg=WHITE,
                           font=("Segoe UI", 12), relief="flat", bd=0, highlightthickness=0,
                           cursor="hand2", activebackground="#555555", activeforeground="white",
                           command=win.destroy)
        _b_env.place(x=28, y=H_w - 58, width=160, height=42)
        _b_can.place(x=W_w - 28 - 130, y=H_w - 58, width=130, height=42)

        parent.wait_window(win)
        return result[0]

    def abrir_dialogo_enviar_avisos():
        if not linhas_nota or not any(r["var_cod"].get().strip() for r in linhas_nota):
            messagebox.showwarning("Aviso", "Não há produtos na tela para gerar as imagens.")
            return

        BG    = "#1A2535"
        BG2   = "#223048"
        GOLD  = "#F1C40F"
        BLUE  = "#2471A3"
        WHITE = "#EAECEE"
        MUTED = "#AEB6BF"

        dial = tk.Toplevel(root)
        dial.title("Enviar Avisos")
        dial.resizable(False, False)
        dial.grab_set()
        dial.configure(bg=BG)
        # option_add: define fundo padrão para TODOS os widgets filhos (evita branco no Windows)
        dial.option_add("*Background", BG)
        dial.option_add("*Foreground", WHITE)
        W_d, H_d = 560, 400
        dial.geometry(f"{W_d}x{H_d}+{root.winfo_rootx()+(root.winfo_width()-W_d)//2}+{root.winfo_rooty()+(root.winfo_height()-H_d)//2}")
        try:
            dial.iconbitmap(_get_recurso("icone.ico"))
        except Exception:
            pass

        # Faixa dourada
        tk.Frame(dial, bg=GOLD, height=5).pack(fill="x")

        # Título e subtítulo dentro de Frame intermediário (evita fundo branco direto no Toplevel)
        f_hdr = tk.Frame(dial, bg=BG)
        f_hdr.pack(fill="x")
        tk.Label(f_hdr, text="ENVIAR AVISOS VIA WHATSAPP", bg=BG,
                 fg=GOLD, font=("Segoe UI", 15, "bold"), bd=0).pack(pady=(20, 4))
        tk.Label(f_hdr, text="Selecione os destinatários:", bg=BG,
                 fg=MUTED, font=("Segoe UI", 11), bd=0).pack(pady=(0, 12))

        var_ch = tk.BooleanVar(value=True)
        var_lo = tk.BooleanVar(value=True)

        nome_chefe = _ler_contato_chefe() or "não configurado"
        nome_lojas = _ler_grupo_whatsapp() or "não configurado"

        f_opts = tk.Frame(dial, bg=BG2)
        f_opts.pack(padx=36, fill="x")

        def _make_toggle(parent, var, rotulo, nome_dest):
            frm = tk.Frame(parent, bg=BG2, cursor="hand2")
            frm.pack(fill="x")
            cv = tk.Canvas(frm, width=26, height=26, bg=BG2, highlightthickness=0)
            cv.pack(side="left", padx=(16, 10), pady=14)
            tk.Label(frm, text=rotulo, bg=BG2, fg=WHITE,
                     font=("Segoe UI", 12, "bold"), anchor="w", bd=0).pack(side="left")
            lbl_var = tk.StringVar(value=f"→  {nome_dest}")
            lbl_dest = tk.Label(frm, textvariable=lbl_var, bg=BG2, fg=MUTED,
                                font=("Segoe UI", 10), anchor="w", bd=0)
            lbl_dest.pack(side="left", padx=(6, 0))

            def _desenhar():
                cv.delete("all")
                if var.get():
                    cv.create_rectangle(3, 3, 23, 23, fill=BLUE, outline="#5DADE2", width=2)
                    cv.create_line(7, 13, 11, 18, fill="white", width=2)
                    cv.create_line(11, 18, 20, 8, fill="white", width=2)
                else:
                    cv.create_rectangle(3, 3, 23, 23, fill=BG2, outline=MUTED, width=2)

            def _toggle(e=None):
                var.set(not var.get())
                _desenhar()

            for w in (cv, frm, lbl_dest):
                w.bind("<Button-1>", _toggle)
            # lbl rotulo está num Frame fill, precisa do bind no frm
            _desenhar()
            return lbl_var

        lbl_ch_var = _make_toggle(f_opts, var_ch, "CHEFE", nome_chefe)
        tk.Frame(f_opts, bg="#2C3E50", height=1).pack(fill="x", padx=16)
        lbl_lo_var = _make_toggle(f_opts, var_lo, "LOJAS", nome_lojas)

        def _get_font_pil_local(size, bold=False):
            from PIL import ImageFont as _IF
            candidatos = [
                "C:/Windows/Fonts/segoeui.ttf" if not bold else "C:/Windows/Fonts/segoeuib.ttf",
                "C:/Windows/Fonts/arial.ttf"   if not bold else "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/verdana.ttf"
            ]
            for c in candidatos:
                if os.path.exists(c):
                    try: return _IF.truetype(c, size)
                    except: pass
            return _IF.load_default()

        def _gerar_img_chefe_local():
            from PIL import Image as _Im, ImageDraw as _ID
            C_BG=(23,32,42); C_BG2=(28,40,51); C_ROW=(33,47,61)
            C_GOLD=(241,196,15); C_WHITE=(236,240,241); C_MUTED=(189,195,199)
            C_BLUE=(174,214,241); C_SEP=(241,196,15)
            W=960; PAD=22
            X_CANT=W-490; X_CNOV=W-375; X_VEND=W-255; X_PRZO=W-135; X_MKP=W-32
            forn=combo_forn.get(); nf=var_num_nota.get(); pedido=var_pedido.get()
            data=datetime.now().strftime("%d/%m/%Y")
            prods=[{"cod":r["var_cod"].get().strip(),"nome":r["var_nome"].get(),
                    "preco_ant":r["var_venda_antiga"].get(),"custo_ant":r["var_custo_atual"].get(),
                    "custo":r["var_novo_custo"].get(),"venda":r["var_venda"].get(),
                    "prazo":r["var_prazo"].get(),"markup":r["var_mkp_real"].get()}
                   for r in linhas_nota if r["var_cod"].get().strip()
                   and r["var_nome"].get() not in ["---","❌ PRODUTO NÃO ENCONTRADO"]]
            fT=_get_font_pil_local(16,True); fS=_get_font_pil_local(12)
            fP=_get_font_pil_local(13,True); fV=_get_font_pil_local(12); fF=_get_font_pil_local(12,True)
            HEADER_H=100; SUB_H=40; ROW_H=78; FOOT_H=56; SEP=2
            H=HEADER_H+SUB_H+SEP+len(prods)*ROW_H+(max(0,len(prods)-1)*SEP)+FOOT_H
            img=_Im.new("RGB",(W,H),C_BG); d=_ID.Draw(img)
            d.rectangle([0,0,W,HEADER_H],fill=C_BG)
            d.text((PAD,18),"RESUMO DE PRECIFICACAO",fill=C_GOLD,font=fT)
            d.text((PAD,44),f"Fornecedor: {forn}",fill=C_BLUE,font=fS)
            d.text((PAD,64),f"NF: {nf}   |   Pedido: {pedido}   |   {data}",fill=C_MUTED,font=fV)
            d.rectangle([0,HEADER_H,W,HEADER_H+SEP],fill=C_SEP)
            y=HEADER_H+SEP
            d.rectangle([0,y,W,y+SUB_H],fill=(19,27,36))
            d.text((PAD,y+20),"PRODUTO",fill=C_MUTED,font=fF,anchor="lm")
            d.text((X_CANT,y+20),"CUSTO ANT",fill=C_MUTED,font=fF,anchor="mm")
            d.text((X_CNOV,y+20),"CUSTO NOVO",fill=C_MUTED,font=fF,anchor="mm")
            d.text((X_VEND,y+20),"VENDA",fill=C_MUTED,font=fF,anchor="mm")
            d.text((X_PRZO,y+20),"PRAZO",fill=C_MUTED,font=fF,anchor="mm")
            d.text((X_MKP,y+20),"MARKUP",fill=C_MUTED,font=fF,anchor="rm")
            y+=SUB_H
            for i,p in enumerate(prods):
                bg=C_BG2 if i%2==0 else C_ROW
                d.rectangle([0,y,W,y+ROW_H],fill=bg)
                texto=f"[{p['cod']}]  "+p["nome"]; orig=texto; max_w=X_CANT-PAD-30
                while d.textlength(texto,font=fP)>max_w: texto=texto[:-1]
                if len(texto)<len(orig): texto=texto[:-1]+"…"
                mid=y+ROW_H//2
                d.text((PAD,y+16),texto,fill=C_WHITE,font=fP,anchor="lm")
                d.text((PAD,y+50),f"Preço ant: {p['preco_ant']}",fill=C_MUTED,font=fS,anchor="lm")
                d.text((X_CANT,mid),p["custo_ant"],fill=C_MUTED,font=fP,anchor="mm")
                d.text((X_CNOV,mid),p["custo"],fill=C_WHITE,font=fP,anchor="mm")
                d.text((X_VEND,mid),p["venda"],fill=C_WHITE,font=fP,anchor="mm")
                d.text((X_PRZO,mid),p["prazo"],fill=C_WHITE,font=fP,anchor="mm")
                d.text((X_MKP,mid),p["markup"],fill=C_GOLD,font=fP,anchor="rm")
                y+=ROW_H
                if i<len(prods)-1: d.rectangle([0,y,W,y+SEP],fill=(40,55,71)); y+=SEP
            d.rectangle([0,y,W,H],fill=C_BG)
            resumo=re.sub(r'Itens:\s*\d+\s*\|\s*','',lbl_res_formula.cget("text"))
            d.text((PAD,y+18),resumo,fill=C_MUTED,font=fF)
            return img

        def _gerar_img_lojas_local():
            from PIL import Image as _Im, ImageDraw as _ID
            C_BG=(11,61,37); C_BG2=(8,46,28); C_ROW=(15,77,46)
            C_GOLD=(241,196,15); C_WHITE=(236,240,241); C_MUTED=(161,221,192); C_SEP=(39,174,96)
            W=760; PAD=28
            forn=combo_forn.get(); data=datetime.now().strftime("%d/%m/%Y")
            regime_av=var_regime.get(); prods=[]
            for r in linhas_nota:
                if r["var_cod"].get().strip() and r["var_nome"].get() not in ["---","❌ PRODUTO NÃO ENCONTRADO"]:
                    q_nf=r["var_qtd_nf"].get(); q_bon=r["var_qtd_rom"].get()
                    if regime_av=="MISTA (NF + Romaneio)": qtd=q_bon
                    elif regime_av=="NOTA + BONIFICAÇÃO":
                        try: tot=int(float(q_nf or 0)+float(q_bon or 0))
                        except: tot="?"
                        qtd=str(tot)
                    else: qtd=q_nf
                    prods.append({"cod":r["var_cod"].get().strip(),"nome":r["var_nome"].get(),
                                  "qtd":qtd,"venda":r["var_venda"].get(),"prazo":r["var_prazo"].get()})
            fT=_get_font_pil_local(16,True); fS=_get_font_pil_local(13)
            fP=_get_font_pil_local(14,True); fV=_get_font_pil_local(13); fF=_get_font_pil_local(13,True)
            HEADER_H=90; SUB_H=40; ROW_H=62; FOOT_H=46; SEP=2
            H=HEADER_H+SUB_H+SEP+len(prods)*ROW_H+(max(0,len(prods)-1)*SEP)+FOOT_H
            img=_Im.new("RGB",(W,H),C_BG); d=_ID.Draw(img)
            d.rectangle([0,0,W,HEADER_H],fill=C_BG2)
            d.text((PAD,16),"AVISO DE NOVOS PRECOS",fill=C_GOLD,font=fT)
            d.text((PAD,46),f"Fornecedor: {forn}   |   {data}",fill=C_MUTED,font=fS)
            d.rectangle([0,HEADER_H,W,HEADER_H+SEP],fill=C_SEP)
            y=HEADER_H+SEP
            d.rectangle([0,y,W,y+SUB_H],fill=(6,36,22))
            d.text((PAD,y+20),"PRODUTO",fill=C_MUTED,font=fF,anchor="lm")
            d.text((W-260,y+20),"QTD",fill=C_MUTED,font=fF,anchor="mm")
            d.text((W-155,y+20),"VENDA",fill=C_MUTED,font=fF,anchor="mm")
            d.text((W-50,y+20),"PRAZO",fill=C_MUTED,font=fF,anchor="mm")
            y+=SUB_H
            for i,p in enumerate(prods):
                bg=C_BG if i%2==0 else C_ROW
                d.rectangle([0,y,W,y+ROW_H],fill=bg)
                texto=f"[{p['cod']}]  "+p["nome"]; orig=texto; max_w=W-310-PAD-10
                while d.textlength(texto,font=fP)>max_w: texto=texto[:-1]
                if len(texto)<len(orig): texto=texto[:-1]+"…"
                d.text((PAD,y+31),texto,fill=C_WHITE,font=fP,anchor="lm")
                d.text((W-260,y+31),p["qtd"],fill=C_WHITE,font=fP,anchor="mm")
                d.text((W-155,y+31),p["venda"],fill=C_WHITE,font=fP,anchor="mm")
                d.text((W-50,y+31),p["prazo"],fill=C_WHITE,font=fP,anchor="mm")
                y+=ROW_H
                if i<len(prods)-1: d.rectangle([0,y,W,y+SEP],fill=(20,90,50)); y+=SEP
            d.rectangle([0,y,W,H],fill=C_BG2)
            d.text((PAD,y+14),"Boas vendas!",fill=C_MUTED,font=fF)
            return img

        def _confirmar():
            envia_chefe = var_ch.get()
            envia_lojas = var_lo.get()
            if not envia_chefe and not envia_lojas:
                messagebox.showwarning("Aviso", "Selecione ao menos um destinatário.", parent=dial)
                return
            if not _dialogo_whatsapp_confirmar(dial, para_chefe=envia_chefe, para_lojas=envia_lojas):
                return
            dial.destroy()
            try:
                import time as _t2
                if envia_lojas:
                    img_lo = _gerar_img_lojas_local()
                    _copiar_imagem_clipboard(img_lo)
                    _enviar_whatsapp_desktop(_ler_grupo_whatsapp())
                    if envia_chefe: _t2.sleep(3.0)
                if envia_chefe:
                    img_ch = _gerar_img_chefe_local()
                    _copiar_imagem_clipboard(img_ch)
                    _enviar_whatsapp_desktop(_ler_contato_chefe())
                messagebox.showinfo("Enviado!", "Aviso(s) enviado(s) com sucesso!")
            except Exception as _ex:
                messagebox.showerror("Erro", f"Erro ao enviar:\n{_ex}")

        def _editar_dest_local():
            BG3 = "#1B3A5C"
            sub = tk.Toplevel(dial)
            sub.title("Editar Destinatários")
            sub.resizable(False, False)
            sub.grab_set()
            sub.configure(bg=BG)
            sub.option_add("*Background", BG)
            sub.option_add("*Foreground", WHITE)
            try: sub.iconbitmap(_get_recurso("icone.ico"))
            except: pass
            sub.geometry(f"430x310+{dial.winfo_rootx()+(dial.winfo_width()-430)//2}+{dial.winfo_rooty()+(dial.winfo_height()-310)//2}")
            tk.Frame(sub, bg=GOLD, height=4).pack(fill="x")
            f_st = tk.Frame(sub, bg=BG); f_st.pack(fill="x")
            tk.Label(f_st, text="EDITAR DESTINATÁRIOS", bg=BG, fg=GOLD,
                     font=("Segoe UI", 12, "bold"), bd=0).pack(pady=(14, 10))
            f_form = tk.Frame(sub, bg=BG); f_form.pack(padx=28, fill="x")
            tk.Label(f_form, text="Contato do chefe:", bg=BG, fg=MUTED,
                     font=("Segoe UI", 10), bd=0).grid(row=0, column=0, sticky="w", pady=(0,2))
            ent_ch = tk.Entry(f_form, font=("Segoe UI", 11), bg=BG3, fg=WHITE,
                              insertbackground=WHITE, relief="flat", bd=4)
            ent_ch.grid(row=1, column=0, sticky="ew", ipady=7, pady=(0, 8))
            ent_ch.insert(0, _ler_contato_chefe() or "")
            tk.Label(f_form, text="Grupo das lojas:", bg=BG, fg=MUTED,
                     font=("Segoe UI", 10), bd=0).grid(row=2, column=0, sticky="w", pady=(0,2))
            ent_lo = tk.Entry(f_form, font=("Segoe UI", 11), bg=BG3, fg=WHITE,
                              insertbackground=WHITE, relief="flat", bd=4)
            ent_lo.grid(row=3, column=0, sticky="ew", ipady=7)
            ent_lo.insert(0, _ler_grupo_whatsapp() or "")
            f_form.columnconfigure(0, weight=1)
            def _ok_edit():
                c = ent_ch.get().strip(); l = ent_lo.get().strip()
                if c: _salvar_contato_chefe(c); lbl_ch_var.set(f"→  {c}")
                if l: _salvar_grupo_whatsapp(l); lbl_lo_var.set(f"→  {l}")
                sub.destroy()
            _b_ok2 = tk.Button(sub, text="  OK  ", bg=BLUE, fg="white", font=("Segoe UI", 11, "bold"),
                               relief="flat", bd=0, highlightthickness=0, cursor="hand2",
                               activebackground="#1A6FA8", activeforeground="white",
                               command=_ok_edit)
            _b_ca2 = tk.Button(sub, text="Cancelar", bg="#424242", fg=WHITE, font=("Segoe UI", 11),
                               relief="flat", bd=0, highlightthickness=0, cursor="hand2",
                               activebackground="#555555", activeforeground="white",
                               command=sub.destroy)
            _b_ok2.place(x=24, y=295, width=130, height=38)
            _b_ca2.place(x=430 - 24 - 110, y=295, width=110, height=38)

        f_alt = tk.Frame(dial, bg=BG)
        f_alt.pack(fill="x", padx=36, pady=(10, 2))
        tk.Button(f_alt, text="✏  ALTERAR DESTINATÁRIOS", bg="#1B3A5C", fg=WHITE,
                  font=("Segoe UI", 10), relief="flat", bd=0,
                  padx=12, pady=8, cursor="hand2",
                  activebackground="#1A4A72", activeforeground=WHITE,
                  command=_editar_dest_local).pack(fill="x")

        _b_env2 = tk.Button(dial, text="   ENVIAR   ", bg=BLUE, fg="white",
                            font=("Segoe UI", 12, "bold"), relief="flat", bd=0, highlightthickness=0,
                            cursor="hand2", activebackground="#1A6FA8", activeforeground="white",
                            command=_confirmar)
        _b_can2 = tk.Button(dial, text="Cancelar", bg="#424242", fg=WHITE,
                            font=("Segoe UI", 12), relief="flat", bd=0, highlightthickness=0,
                            cursor="hand2", activebackground="#555555", activeforeground="white",
                            command=dial.destroy)
        _b_env2.place(x=28, y=H_d - 58, width=160, height=42)
        _b_can2.place(x=W_d - 28 - 130, y=H_d - 58, width=130, height=42)

    f_resumo_container = ttkb.Labelframe(root, text=" 📊 DEMONSTRATIVO FINANCEIRO DA CARGA ", bootstyle="primary", padding=5)
    f_resumo_container.pack(fill="x", side="bottom", padx=10, pady=5)

    if _logo_rgba:
        try:
            hex_bg = style.colors.bg
            if not hex_bg.startswith("#"):
                hex_bg = "#" + hex_bg
            _img_logo_footer = _criar_logo_img(_logo_rgba, hex_bg)
            lbl_logo = tk.Label(f_resumo_container, image=_img_logo_footer, bg=hex_bg,
                                bd=0, cursor="hand2")
            lbl_logo.image = _img_logo_footer
            lbl_logo.pack(side="right", padx=(0, 18), pady=2)

            _cartao_ref = [None]
            def mostrar_cartao_visitas(event=None):
                if _cartao_ref[0] and _cartao_ref[0].winfo_exists():
                    _cartao_ref[0].destroy()
                    _cartao_ref[0] = None
                    return
                card = tk.Toplevel(root)
                card.overrideredirect(True)
                card.attributes("-topmost", True)
                W_c, H_c = 420, 210
                rx = root.winfo_rootx() + (root.winfo_width()  - W_c) // 2
                ry = root.winfo_rooty() + (root.winfo_height() - H_c) // 2
                card.geometry(f"{W_c}x{H_c}+{rx}+{ry}")
                _cartao_ref[0] = card

                C_BG    = "#1B4F6A"
                C_GOLD  = "#C9A84C"
                C_WHITE = "#EAEAEA"
                C_MUTED = "#7A8FA6"

                card.configure(bg=C_BG)
                cv = tk.Canvas(card, width=W_c, height=H_c,
                               bg=C_BG, bd=0, highlightthickness=0)
                cv.pack(fill="both", expand=True)

                # Fundo sólido (garante cor no Windows)
                cv.create_rectangle(0, 0, W_c, H_c, fill=C_BG, outline="")
                # Borda dourada
                cv.create_rectangle(2, 2, W_c-2, H_c-2, outline=C_GOLD, width=1)
                # Barra esquerda dourada
                cv.create_rectangle(0, 0, 6, H_c, fill=C_GOLD, outline="")

                # Nome
                cv.create_text(30, 68, text="WALTER VOGA", anchor="w",
                               fill=C_WHITE, font=("Segoe UI", 22, "bold"))

                # Linha separadora dourada
                cv.create_line(30, 97, W_c-22, 97, fill=C_GOLD, width=1)

                # Cargo
                cv.create_text(30, 121, text="Desenvolvedor", anchor="w",
                               fill=C_GOLD, font=("Segoe UI", 12))

                # Telefone
                cv.create_text(30, 155, text="(22) 99939-0202", anchor="w",
                               fill=C_MUTED, font=("Segoe UI", 12))

                cv.bind("<Button-1>", lambda e: card.destroy())
                card.bind("<FocusOut>",  lambda e: card.destroy())

            lbl_logo.bind("<Button-1>", mostrar_cartao_visitas)
        except Exception:
            pass

    lbl_res_formula = ttkb.Label(f_resumo_container, text="Aguardando inserção de produtos...", font=("Segoe UI", 13, "bold"), bootstyle="danger")
    lbl_res_formula.pack(side="left", expand=True, pady=2)

    # =========================================================
    # IMPORTAÇÃO DE XML NF-e
    # =========================================================

    def _preencher_tela_xml(dados_xml, itens):
        from tkinter import filedialog as _fd
        root.ignorando_validacao = True
        limpar_nota(pergunta=False, add_linha=False)

        # Fornecedor: busca por CNPJ (prioridade) ou fuzzy por nome
        cnpj_xml  = re.sub(r'\D', '', dados_xml.get('cnpj_fornecedor', ''))
        nome_emit = dados_xml.get('nome_fornecedor', '')
        nomes_forn = list(combo_forn.master_list) if hasattr(combo_forn, 'master_list') else []
        encontrado = ''

        if cnpj_xml:
            for f in cache_fornecedores:
                if re.sub(r'\D', '', str(f.get('cnpj', ''))) == cnpj_xml:
                    encontrado = f['fabricante']
                    break

        if not encontrado and nomes_forn and nome_emit:
            matches = difflib.get_close_matches(nome_emit.upper(),
                                                [n.upper() for n in nomes_forn], n=1, cutoff=0.4)
            if matches:
                idx = [n.upper() for n in nomes_forn].index(matches[0])
                encontrado = nomes_forn[idx]

        if encontrado:
            combo_forn.set(encontrado)
        else:
            combo_forn.set(nome_emit)
        ao_trocar_fornecedor()

        var_num_nota.set(dados_xml.get('num_nf', ''))
        var_dt_emissao.set(dados_xml.get('dt_emissao', ''))
        frete_xml = dados_xml.get('mod_frete', '')
        if frete_xml in ('CIF', 'FOB', 'TERCEIRIZADO'):
            var_tipo_frete.set(frete_xml)

        for item in itens:
            adicionar_linha()
            r = linhas_nota[-1]
            cod_fdc = item.get('cod_fdc_sugerido') or ''
            r['var_cod'].set(cod_fdc)
            if cod_fdc:
                buscar_produto(r)
            qtd = item.get('qtd', 0)
            r['var_qtd_nf'].set(str(int(qtd)) if float(qtd) == int(qtd) else str(qtd))
            r['var_unit_nf'].set(formatar_moeda(item.get('val_unit', 0.0)))
            ipi = item.get('ipi_perc', 0.0)
            if ipi > 0:
                r['var_ipi'].set(formatar_percentual(ipi))

        root.ignorando_validacao = False
        atualizar_tudo_real_time()
        if not encontrado and nome_emit:
            messagebox.showinfo("Fornecedor não encontrado",
                f"Fornecedor '{nome_emit}' não está cadastrado.\nSelecione manualmente no campo Fornecedor.")

    def abrir_janela_resolucao_xml(dados_xml, itens_cruzados):
        from tkinter import ttk
        import difflib as _diff

        jan = tk.Toplevel(root)
        jan.title("Importar XML — Resolução de Produtos")
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = int(sw * 0.92), int(sh * 0.82)
        jan.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        jan.transient(root); jan.grab_set()
        bg_mod = "#ecf0f1" if root.tema_atual == 'claro' else "#2e3440"
        fg_mod = "black" if root.tema_atual == 'claro' else "white"
        jan.config(bg=bg_mod)

        # Cabeçalho informativo
        f_cab = ttkb.Frame(jan, bootstyle="secondary", padding=10)
        f_cab.pack(fill="x", side="top")
        info_campos = [
            ("Fornecedor:", dados_xml.get('nome_fornecedor', '')),
            ("NF Nº:", dados_xml.get('num_nf', '')),
            ("Emissão:", dados_xml.get('dt_emissao', '')),
            ("Frete:", dados_xml.get('mod_frete', '')),
            ("Total NF:", formatar_moeda(dados_xml.get('val_total', 0))),
        ]
        for i, (lbl, val) in enumerate(info_campos):
            ttkb.Label(f_cab, text=lbl, font=("Segoe UI", 9, "bold")).grid(row=0, column=i*2, padx=(15,2), pady=4, sticky="e")
            ttkb.Label(f_cab, text=val, font=("Segoe UI", 9)).grid(row=0, column=i*2+1, padx=(0,15), pady=4, sticky="w")

        # Treeview de produtos
        f_tree = ttkb.Frame(jan, padding=5)
        f_tree.pack(fill="both", expand=True, padx=8, pady=4)

        colunas = ("Cód NF", "Descrição NF", "Qtd", "Val Unit", "IPI%", "Status", "Cód FDC", "Nome FDC")
        tree = ttk.Treeview(f_tree, columns=colunas, show="headings", selectmode="browse")
        sb_y = ttkb.Scrollbar(f_tree, orient="vertical", command=tree.yview)
        sb_x = ttkb.Scrollbar(f_tree, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side="right", fill="y"); sb_x.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        largs = {"Cód NF": 80, "Descrição NF": 260, "Qtd": 55, "Val Unit": 80,
                 "IPI%": 55, "Status": 110, "Cód FDC": 75, "Nome FDC": 230}
        for col in colunas:
            tree.heading(col, text=col)
            tree.column(col, width=largs.get(col, 80),
                        anchor="w" if col in ("Descrição NF", "Nome FDC") else "center")

        tree.tag_configure("CONFIRMADO",    background="#1A5276", foreground="white")
        tree.tag_configure("EAN_DIRETO",    background="#154360", foreground="white")
        tree.tag_configure("SUGESTAO",      background="#7D6608", foreground="white")
        tree.tag_configure("NAO_ENCONTRADO",background="#641E16", foreground="white")

        # estado mutável dos itens (copiado para permitir edição)
        itens_estado = [dict(i) for i in itens_cruzados]

        def _recarregar_tree():
            for row in tree.get_children(): tree.delete(row)
            for idx, item in enumerate(itens_estado):
                st = item.get('status', 'NAO_ENCONTRADO')
                tree.insert("", "end", iid=str(idx), tags=(st,), values=(
                    item.get('cod_nf', ''),
                    item.get('descricao_nf', ''),
                    item.get('qtd', ''),
                    formatar_moeda(item.get('val_unit', 0)),
                    f"{item.get('ipi_perc',0):.2f}%",
                    st,
                    item.get('cod_fdc_sugerido') or '',
                    item.get('nome_fdc_sugerido') or '',
                ))

        _recarregar_tree()

        # Dica de uso
        ttkb.Label(jan, text="Duplo-clique numa linha para resolver manualmente",
                   font=("Segoe UI", 8, "italic"), bootstyle="secondary").pack()

        def _abrir_selecao(idx):
            item = itens_estado[idx]
            sugestoes = item.get('sugestoes', [])

            sel_jan = tk.Toplevel(jan)
            sel_jan.title("Selecionar Produto FDC")
            sel_jan.geometry(f"700x420+{(sw-700)//2}+{(sh-420)//2}")
            sel_jan.transient(jan); sel_jan.grab_set()
            sel_jan.config(bg=bg_mod)

            ttkb.Label(sel_jan, text=f"Produto NF: {item.get('descricao_nf','')}",
                       font=("Segoe UI", 10, "bold")).pack(pady=(10,4), padx=10, anchor="w")

            # Sugestões
            f_sug = ttkb.Labelframe(sel_jan, text=" Sugestões automáticas ", padding=8)
            f_sug.pack(fill="x", padx=10, pady=4)
            lb_var = tk.StringVar()
            lb = tk.Listbox(f_sug, height=5, font=("Segoe UI", 9), activestyle="dotbox",
                            selectmode="single", listvariable=lb_var)
            lb.pack(fill="x")
            sugestoes_lista = []
            for s in sugestoes:
                texto = f"[{s['codigo']}]  {s['nome']}  ({s['score']*100:.0f}%)"
                lb.insert("end", texto)
                sugestoes_lista.append(s)
            if sugestoes_lista:
                lb.selection_set(0)

            # Busca manual por código FDC
            f_man = ttkb.Labelframe(sel_jan, text=" Ou digitar código FDC manualmente ", padding=8)
            f_man.pack(fill="x", padx=10, pady=4)
            ent_cod = ttkb.Entry(f_man, font=("Segoe UI", 10), width=20)
            ent_cod.pack(side="left", padx=4)
            lbl_nome_manual = ttkb.Label(f_man, text="", font=("Segoe UI", 9))
            lbl_nome_manual.pack(side="left", padx=8)

            def _validar_manual(*_):
                cod = ent_cod.get().strip()
                df_bas = cache_fdc.get('basico')
                if df_bas is not None and not df_bas.empty and '_cod_str' in df_bas.columns:
                    m = df_bas[df_bas['_cod_str'] == cod]
                    if not m.empty:
                        lbl_nome_manual.config(text=m.iloc[0]['_nome_str'], foreground="#2ECC71")
                        return
                lbl_nome_manual.config(text="Não encontrado" if cod else "", foreground="#E74C3C")

            ent_cod.bind("<KeyRelease>", _validar_manual)

            var_salvar = tk.BooleanVar(value=True)
            ttkb.Checkbutton(sel_jan, text="Salvar mapeamento para uso futuro",
                             variable=var_salvar).pack(padx=10, pady=4, anchor="w")

            def _confirmar():
                cod_escolhido = nome_escolhido = ''
                cod_manual = ent_cod.get().strip()
                if cod_manual:
                    df_bas = cache_fdc.get('basico')
                    if df_bas is not None and '_cod_str' in df_bas.columns:
                        m = df_bas[df_bas['_cod_str'] == cod_manual]
                        if not m.empty:
                            cod_escolhido  = cod_manual
                            nome_escolhido = m.iloc[0]['_nome_str']
                if not cod_escolhido and lb.curselection() and sugestoes_lista:
                    s = sugestoes_lista[lb.curselection()[0]]
                    cod_escolhido = s['codigo']; nome_escolhido = s['nome']
                if not cod_escolhido:
                    messagebox.showwarning("Atenção", "Selecione ou digite um código FDC.", parent=sel_jan)
                    return
                itens_estado[idx]['cod_fdc_sugerido']  = cod_escolhido
                itens_estado[idx]['nome_fdc_sugerido'] = nome_escolhido
                itens_estado[idx]['confirmado']        = True
                itens_estado[idx]['status']            = 'CONFIRMADO'
                if var_salvar.get():
                    salvar_de_para(DB_PATH,
                                   dados_xml.get('cnpj_fornecedor', ''),
                                   item.get('cod_nf', ''),
                                   item.get('descricao_nf', ''),
                                   cod_escolhido, nome_escolhido)
                _recarregar_tree()
                sel_jan.destroy()

            f_btns = tk.Frame(sel_jan, bg=bg_mod)
            f_btns.pack(pady=10)
            ttkb.Button(f_btns, text="✅ Confirmar", bootstyle="success", command=_confirmar).pack(side="left", padx=8)
            ttkb.Button(f_btns, text="❌ Cancelar", bootstyle="danger", command=sel_jan.destroy).pack(side="left", padx=8)

        def _duplo_clique(event):
            iid = tree.identify_row(event.y)
            if iid:
                _abrir_selecao(int(iid))

        tree.bind("<Double-1>", _duplo_clique)

        # Botões inferiores
        f_bots = tk.Frame(jan, bg=bg_mod)
        f_bots.pack(pady=10)

        def _importar(so_confirmados):
            if so_confirmados:
                itens_imp = [i for i in itens_estado if i.get('status') in ('CONFIRMADO', 'EAN_DIRETO')]
            else:
                itens_imp = itens_estado
            if not itens_imp:
                messagebox.showinfo("Nenhum item", "Nenhum produto para importar.", parent=jan)
                return
            jan.destroy()
            _preencher_tela_xml(dados_xml, itens_imp)

        ttkb.Button(f_bots, text="✅ IMPORTAR CONFIRMADOS",
                    bootstyle="success", padding=(12,8),
                    command=lambda: _importar(True)).pack(side="left", padx=8)
        ttkb.Button(f_bots, text="⚠️ IMPORTAR TODOS COM PENDÊNCIAS",
                    bootstyle="warning", padding=(12,8),
                    command=lambda: _importar(False)).pack(side="left", padx=8)
        ttkb.Button(f_bots, text="❌ CANCELAR",
                    bootstyle="danger", padding=(12,8),
                    command=jan.destroy).pack(side="left", padx=8)

    def importar_xml_nfe():
        from tkinter import filedialog as _fd
        if not cache_fdc.get('carregado'):
            messagebox.showwarning("FDC não carregado",
                "Carregue os dados do FDC antes de importar um XML.")
            return
        tem_dados = any(r['var_cod'].get().strip() for r in linhas_nota)
        if tem_dados:
            if not messagebox.askyesno("Limpar tela?",
                "Há produtos na tela. Deseja limpar antes de importar o XML?"):
                return
            limpar_nota(pergunta=False, add_linha=False)
        caminho = _fd.askopenfilename(
            title="Selecionar XML de NF-e",
            filetypes=[("XML NF-e", "*.xml"), ("Todos os arquivos", "*.*")])
        if not caminho:
            return
        try:
            dados_xml = ler_xml_nfe(caminho)
            if not dados_xml['itens']:
                messagebox.showwarning("XML vazio", "Nenhum produto encontrado no XML.")
                return
            itens_cruzados = cruzar_produtos(dados_xml['itens'], cache_fdc, DB_PATH,
                                             dados_xml['cnpj_fornecedor'])
            abrir_janela_resolucao_xml(dados_xml, itens_cruzados)
        except Exception as ex:
            messagebox.showerror("Erro ao ler XML", str(ex))

    # =========================================================
    # JANELA ATUALIZAR FDC (processa CSVs brutos)
    # =========================================================
    def abrir_janela_atualizar_fdc():
        from tkinter import scrolledtext as _st
        from tkinter import filedialog as _fd
        from preparador_fdc import executar as _exec
        import threading as _thr

        jan = tk.Toplevel(root)
        jan.title("Atualizar FDC — Processamento de CSVs")
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = 680, 520
        jan.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        jan.transient(root); jan.grab_set(); jan.resizable(False, False)
        jan.config(bg="#1E1E1E")

        tk.Label(jan, text="PROCESSAMENTO DE RELATÓRIOS FDC",
                 font=("Segoe UI", 12, "bold"), bg="#1E1E1E", fg="#D4D4D4", pady=6).pack()

        # Seleção de pasta
        pasta_var = tk.StringVar(value=_ler_pasta_fdc() or "")
        f_pasta = tk.Frame(jan, bg="#1E1E1E")
        f_pasta.pack(fill="x", padx=10, pady=(0, 4))
        tk.Label(f_pasta, text="Pasta dos CSVs:", font=("Segoe UI", 8, "bold"),
                 bg="#1E1E1E", fg="#D4D4D4").pack(side="left")
        lbl_pasta = tk.Label(f_pasta, textvariable=pasta_var, font=("Segoe UI", 8),
                             bg="#1E1E1E", fg="#888888", wraplength=480, anchor="w", justify="left")
        lbl_pasta.pack(side="left", padx=6, fill="x", expand=True)

        def _selecionar_pasta():
            nova = _fd.askdirectory(title="Selecionar pasta com os CSVs do FDC", parent=jan)
            if nova:
                pasta_var.set(nova)
                _salvar_pasta_fdc(nova)

        tk.Button(f_pasta, text="📁 Alterar", font=("Segoe UI", 8), bg="#444444", fg="white",
                  relief="flat", cursor="hand2", padx=6, pady=2,
                  command=_selecionar_pasta).pack(side="right")

        log_area = _st.ScrolledText(jan, height=17, width=80,
                                    font=("Consolas", 9), state="disabled",
                                    bg="#1E1E1E", fg="#D4D4D4", insertbackground="white",
                                    relief="flat")
        log_area.pack(padx=10, pady=6, fill="both", expand=True)

        f_bots = tk.Frame(jan, bg="#1E1E1E")
        f_bots.pack(pady=8)
        btn_proc = tk.Button(f_bots, text="▶  Processar CSVs",
                             font=("Segoe UI", 10, "bold"), bg="#0078D4", fg="white",
                             padx=20, pady=6, relief="flat", cursor="hand2",
                             activebackground="#005A9E")
        btn_proc.pack(side="left", padx=8)
        btn_fechar = tk.Button(f_bots, text="Fechar",
                               font=("Segoe UI", 10), bg="#444444", fg="white",
                               padx=16, pady=6, relief="flat", cursor="hand2",
                               command=jan.destroy)
        btn_fechar.pack(side="left", padx=8)

        def log_fn(msg):
            def _u():
                log_area.config(state="normal")
                log_area.insert(tk.END, msg + "\n")
                log_area.see(tk.END)
                log_area.config(state="disabled")
            root.after(0, _u)

        def on_done(success):
            def _u():
                pasta_atual = pasta_var.get()
                if success:
                    # Copia arquivos processados para a pasta do programa
                    copiados = []
                    try:
                        from preparador_fdc import eh_produto_basico, ARQUIVO_SAIDA_POSICAO
                        import glob as _gl
                        arquivos = (_gl.glob(os.path.join(pasta_atual, "*.csv")) +
                                    _gl.glob(os.path.join(pasta_atual, "*.xlsx")))
                        for arq in arquivos:
                            if eh_produto_basico(arq) or os.path.basename(arq).lower() == ARQUIVO_SAIDA_POSICAO.lower():
                                destino = os.path.join(diretorio_atual, os.path.basename(arq))
                                shutil.copy2(arq, destino)
                                copiados.append(os.path.basename(arq))
                        if copiados:
                            log_fn(f"\nCopiado para pasta do programa: {', '.join(copiados)}")
                    except Exception as e:
                        log_fn(f"\n[AVISO] Não foi possível copiar arquivos: {e}")
                    s, msg, out = carregar_dados_memoria(diretorio_atual)
                    _atualizar_lbl_fdc(s, msg, out, False)
                    btn_proc.config(state="disabled", text="✅ Concluído", bg="#107C10")
                    btn_fechar.config(bg="#107C10")
                else:
                    btn_proc.config(state="normal", text="↺ Tentar novamente", bg="#C50F1F")
                    btn_fechar.config(bg="#C50F1F")
            root.after(0, _u)

        def iniciar():
            pasta_atual = pasta_var.get().strip()
            if not pasta_atual:
                messagebox.showwarning("Pasta não configurada",
                    "Selecione a pasta onde estão os CSVs do FDC.", parent=jan)
                return
            btn_proc.config(state="disabled", text="⏳ Processando...", bg="#555555")
            log_area.config(state="normal"); log_area.delete("1.0", tk.END); log_area.config(state="disabled")
            from datetime import datetime as _dt
            log_fn(f"Iniciado: {_dt.now().strftime('%d/%m/%Y  %H:%M:%S')}")
            log_fn(f"Pasta: {pasta_atual}\n")
            _thr.Thread(target=_exec, args=(pasta_atual, log_fn, on_done), daemon=True).start()

        btn_proc.config(command=iniciar)
        if not pasta_var.get():
            root.after(200, _selecionar_pasta)

    # =========================================================
    # BARRA DE AÇÕES E ALERTAS (NOVO LAYOUT)
    # =========================================================
    f_controle = ttkb.Frame(root, padding=5)
    f_controle.pack(fill="x", side="top", padx=20)
    
    # Botoes todos alinhados à esquerda para dar espaço e limpeza visual
    f_botoes_acao = ttkb.Frame(f_controle)
    f_botoes_acao.pack(side="left")

    btn_add_linha = ttkb.Button(f_botoes_acao, text="➕ ADD LINHA", style="Lilas.TButton", command=adicionar_linha)
    btn_add_linha.pack(side="left", padx=3)

    btn_limpar = ttkb.Button(f_botoes_acao, text="🧹 LIMPAR", style="Vermelho.TButton", command=lambda: limpar_nota(pergunta=True))
    btn_limpar.pack(side="left", padx=3)
    ToolTip(btn_limpar, text="Limpar todos os campos (Ctrl+L)")

    btn_xml = ttkb.Button(f_botoes_acao, text="📄 XML", style="Ciano.TButton", cursor="hand2", command=lambda: importar_xml_nfe())
    btn_xml.pack(side="left", padx=3)
    ToolTip(btn_xml, text="Importar XML de NF-e (Ctrl+I)")

    btn_buscar = ttkb.Button(f_botoes_acao, text="🔍 BUSCAR", style="Azul.TButton", command=pesquisar_carga_salva)
    btn_buscar.pack(side="left", padx=3)
    ToolTip(btn_buscar, text="Pesquisar processo (Ctrl+F)")

    btn_salvar_reimprimir = ttkb.Button(f_botoes_acao, text="💾 REIMPRIMIR", style="VerdeSalvar.TButton", command=reimprimir_processo)
    btn_salvar_reimprimir.pack(side="left", padx=3)
    ToolTip(btn_salvar_reimprimir, text="Salvar preços e reimprimir espelho")

    btn_ex = ttkb.Button(f_botoes_acao, text="🔐 AUDITAR", style="VermelhoClaro.TButton", command=abrir_cofre_auditoria)
    btn_ex.pack(side="left", padx=3)
    ToolTip(btn_ex, text="Auditar e fechar carga (Ctrl+S)")

    btn_enviar_avisos = ttkb.Button(f_botoes_acao, text="📲 ENVIAR AVISOS", style="Ciano.TButton", cursor="hand2",
                                    command=abrir_dialogo_enviar_avisos)
    btn_enviar_avisos.pack(side="left", padx=3)
    ToolTip(btn_enviar_avisos, text="Enviar imagem para as lojas e/ou para o chefe via WhatsApp")

    btn_fretes = ttkb.Button(f_botoes_acao, text="🚚 FRETES", style="Marrom.TButton", command=lambda: abrir_modulo_fretes(root, pasta_fretes))
    btn_fretes.pack(side="left", padx=3)

    # Lado direito: FDC status + botão ATUALIZAR FDC
    btn_atualizar_fdc = ttkb.Button(f_controle, text="🔄 ATUALIZAR FDC",
                                    style="VerdeClaro.TButton", cursor="hand2",
                                    command=abrir_janela_atualizar_fdc)
    btn_atualizar_fdc.pack(side="right", padx=(0, 4))
    ToolTip(btn_atualizar_fdc, text="Processar CSVs brutos do FDC e recarregar dados")

    lbl_fdc = tk.Label(f_controle, text="⚪ FDC não carregado",
                       font=("Segoe UI", 8), fg="#888888",
                       bg=root.style.colors.bg if hasattr(root, 'style') else "white",
                       cursor="arrow")
    lbl_fdc.pack(side="right", padx=(0, 12))

    def _atualizar_lbl_fdc(sucesso, msg, is_outdated, brutos=False):
        if not sucesso:
            lbl_fdc.config(text="⚪ FDC não carregado", fg="#888888")
            btn_atualizar_fdc.config(style="Vermelho.TButton")
            return
        if is_outdated or brutos:
            aviso = "⚠️ FDC desatualizado" if is_outdated else "⚠️ CSVs brutos pendentes"
            lbl_fdc.config(text=aviso, fg="#E67E22")
            btn_atualizar_fdc.config(style="Laranja.TButton")
        else:
            # extrai "DD/MM HH:MM" da mensagem de status
            try:
                bas_info = msg.split("Básica:")[-1].split("|")[0].strip()[:11]
            except Exception:
                bas_info = ""
            lbl_fdc.config(text=f"🟢 FDC: {bas_info}", fg="#2ECC71")
            btn_atualizar_fdc.config(style="VerdeClaro.TButton")

    # Botão de pendências vai para a direita (mais à esquerda que FDC)
    btn_pendencias = ttkb.Button(f_controle, text="", style="VermelhoEscuro.TButton", command=lambda: mostrar_pendencias())

    def atualizar_alerta_pendencias():
        pendentes = glob.glob(os.path.join(pasta_arquivo, "*_PENDENTE.xlsx"))
        if pendentes:
            btn_pendencias.config(text=f"⚠️ {len(pendentes)} PEDIDO(S) PENDENTE(S)")
            btn_pendencias.pack(side="right", padx=20)
        else:
            btn_pendencias.pack_forget()

    # Inicialização: carrega FDC, atualiza label, avisa se desatualizado
    def _pasta_fdc_efetiva():
        return _ler_pasta_fdc() or diretorio_atual

    def verificar_db_startup():
        sucesso, msg, is_outdated = carregar_dados_memoria(diretorio_atual)
        brutos = tem_brutos_novos(_pasta_fdc_efetiva())
        _atualizar_lbl_fdc(sucesso, msg, is_outdated, brutos)
        if is_outdated:
            messagebox.showwarning("FDC Desatualizado",
                f"Os relatórios do FDC estão com mais de 24h!\n\n{msg}\n\n"
                "Clique em '🔄 ATUALIZAR FDC' para processar os novos CSVs.")
        elif brutos:
            messagebox.showinfo("CSVs FDC pendentes",
                "Há arquivos CSV do FDC aguardando processamento.\n"
                "Clique em '🔄 ATUALIZAR FDC' para processar.")
        atualizar_alerta_pendencias()

    root.after(500, verificar_db_startup)

    # Verificação periódica silenciosa a cada 30 minutos
    def _verificar_fdc_periodicamente():
        try:
            s, msg, out = carregar_dados_memoria(diretorio_atual)
            brutos = tem_brutos_novos(_pasta_fdc_efetiva())
            _atualizar_lbl_fdc(s, msg, out, brutos)
        except Exception:
            pass
        root.after(1800000, _verificar_fdc_periodicamente)

    root.after(1800000, _verificar_fdc_periodicamente)
    root.bind("<FocusIn>", lambda e: _verificar_fdc_periodicamente() if e.widget is root else None)

    # === ATALHOS GLOBAIS DE TECLADO ===
    root.bind("<Control-n>", lambda e: pular_foco(ent_nota))
    root.bind("<Control-N>", lambda e: pular_foco(ent_nota))
    
    root.bind("<Control-l>", lambda e: limpar_nota(pergunta=True))
    root.bind("<Control-L>", lambda e: limpar_nota(pergunta=True))
    
    root.bind("<Control-s>", lambda e: abrir_cofre_auditoria())
    root.bind("<Control-S>", lambda e: abrir_cofre_auditoria())
    
    root.bind("<Control-f>", lambda e: pesquisar_carga_salva())
    root.bind("<Control-F>", lambda e: pesquisar_carga_salva())

    root.bind("<Control-i>", lambda e: importar_xml_nfe())
    root.bind("<Control-I>", lambda e: importar_xml_nfe())

    root.after(100, lambda: limpar_nota(pergunta=False, add_linha=True))
    if _CONFIG_INI_NOVO or not _banco_acessivel:
        root.after(600, lambda: abrir_config_banco(primeiro_acesso=True))
    root.mainloop()

if __name__ == "__main__":
    criar_tela()