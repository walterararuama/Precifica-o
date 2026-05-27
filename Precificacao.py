# Apenas os módulos leves necessários para exibir o splash imediatamente
import sys
import os
import tkinter as tk
import ctypes

# --- ATIVAÇÃO DE ALTA RESOLUÇÃO ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

if getattr(sys, 'frozen', False):
    diretorio_atual = os.path.dirname(sys.executable)
else:
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))

# --- CRIAÇÃO DAS PASTAS ---
pasta_arquivo = os.path.join(diretorio_atual, "ARQUIVO")
os.makedirs(pasta_arquivo, exist_ok=True)

pasta_fretes = os.path.join(diretorio_atual, "FRETES")
os.makedirs(pasta_fretes, exist_ok=True)

DB_PATH = os.path.join(diretorio_atual, "fornecedores.db")

# =====================================================================
# SPLASH SCREEN — aparece antes dos imports pesados
# =====================================================================
splash = tk.Tk()
splash.overrideredirect(True)
splash.attributes("-topmost", True)
splash_w, splash_h = 400, 200
splash_x = (splash.winfo_screenwidth() // 2) - (splash_w // 2)
splash_y = (splash.winfo_screenheight() // 2) - (splash_h // 2)
splash.geometry(f"{splash_w}x{splash_h}+{splash_x}+{splash_y}")
splash.configure(bg="#2C3E50")

tk.Label(splash, text="⏳", font=("Segoe UI", 48), bg="#2C3E50", fg="#F1C40F").pack(pady=(20, 10))
tk.Label(splash, text="Bruno Eletromóveis", font=("Segoe UI", 14, "bold"), bg="#2C3E50", fg="white").pack()
tk.Label(splash, text="Carregando Engenharia de Custos...", font=("Segoe UI", 10), bg="#2C3E50", fg="#BDC3C7").pack(pady=(5, 0))
splash.update()

# --- IMPORTS PESADOS (executados enquanto o splash está visível) ---
import re
import pandas as pd
from tkinter import ttk, messagebox, filedialog
import glob
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

try:
    from ttkbootstrap.widgets import ToolTip
except ImportError:
    from ttkbootstrap.tooltip import ToolTip

from datetime import datetime
import time
import logging
import shutil

from edicao_de_fretes import abrir_modulo_fretes
from exportacao import processar_exportacao_carga, salvar_edicao_precos
from db_fornecedores import inicializar_banco_fornecedores, carregar_fornecedores_db, get_lista_nomes_fornecedores, abrir_gerenciador_fornecedores
from utils import converter_moeda, formatar_moeda, formatar_percentual, auto_selecionar, arredondar_preco, check_nota_duplicada
from motor_fdc import cache_fdc, carregar_dados_memoria

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('precificacao.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)

# --- INICIALIZAÇÃO DO BANCO (enquanto splash ainda está visível) ---
inicializar_banco_fornecedores(DB_PATH, diretorio_atual)
cache_fornecedores = carregar_fornecedores_db(DB_PATH)
splash.destroy()

# =====================================================================
# --- TELA PRINCIPAL ---
# =====================================================================

def criar_tela():
    global cache_fornecedores
    root = ttkb.Window(themename="litera")
    root.title("Bruno Eletromóveis - Engenharia de Custos V4")
    root.geometry("1400x850")
    root.state('zoomed')

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
        if root.focus_get() is None: return False
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
    ]:
        style.configure(f"{_nome}.TButton", background=_bg, foreground="white",
                        font=("Segoe UI", 10, "bold"), borderwidth=0, padding=6)
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
            btn_tema.config(text="☀️ Modo Dia", bg="#f39c12", fg="black")
        else:
            root.tema_atual = "claro"
            root.style.theme_use('litera')
            btn_tema.config(text="🌙 Modo Noite", bg="#2c3e50", fg="white")
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

    tk.Button(f_header, text="✖ Sair", bg="#FF0000", activebackground="#CC0000", activeforeground="white", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2", padx=15, pady=5, command=sair_seguro).pack(side="right")
    btn_tema = tk.Button(f_header, text="🌙 Modo Noite", bg="#2c3e50", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, cursor="hand2", padx=10, command=alternar_tema)
    btn_tema.pack(side="right", padx=10)

    # REFORMULANDO A ÁREA DE NOTA (SEM FUNDOS FIXOS)
    f_dados_nota = ttkb.Frame(root, padding=8)
    f_dados_nota.pack(fill="x", side="top", padx=20)

    lbl_nota = ttkb.Label(f_dados_nota, text="Nº DA NOTA:", font=("Segoe UI", 9, "bold"))
    lbl_nota.pack(side="left", padx=(0, 2))
    ToolTip(lbl_nota, text="Atalho: Ctrl + N")
    
    ent_nota = ttkb.Entry(f_dados_nota, textvariable=var_num_nota, width=15, font=("Segoe UI", 10))
    ent_nota.pack(side="left", padx=5)
    ToolTip(ent_nota, text="Atalho: Ctrl + N")

    lbl_emissao = ttkb.Label(f_dados_nota, text="DT. EMISSÃO:", font=("Segoe UI", 9, "bold"))
    lbl_emissao.pack(side="left", padx=(20, 2))
    ent_emissao = ttkb.Entry(f_dados_nota, textvariable=var_dt_emissao, width=12, font=("Segoe UI", 10), justify="center")
    ent_emissao.pack(side="left", padx=5)

    lbl_chegada = ttkb.Label(f_dados_nota, text="DT. CHEGADA:", font=("Segoe UI", 9, "bold"))
    lbl_chegada.pack(side="left", padx=(20, 2))
    ent_chegada = ttkb.Entry(f_dados_nota, textvariable=var_dt_chegada, width=12, font=("Segoe UI", 10), justify="center")
    ent_chegada.pack(side="left", padx=5)

    lbl_t_frete = ttkb.Label(f_dados_nota, text="TIPO DE FRETE:", font=("Segoe UI", 9, "bold"))
    lbl_t_frete.pack(side="left", padx=(30, 2))
    combo_frete = ttk.Combobox(f_dados_nota, textvariable=var_tipo_frete, values=["FOB", "CIF", "TERCEIRIZADO"], width=15, state="readonly", font=("Segoe UI", 10))
    combo_frete.pack(side="left", padx=5)

    lbl_t_vlr = ttkb.Label(f_dados_nota, text="VLR TERCEIRO:", font=("Segoe UI", 9, "bold"))
    lbl_t_vlr.pack(side="left", padx=(20, 2))
    ent_val_terceiro = ttkb.Entry(f_dados_nota, textvariable=var_val_terceirizado, width=12, font=("Segoe UI", 10, "bold"), justify="right", state="disabled")
    ent_val_terceiro.pack(side="left", padx=5)
    
    lbl_mkp_geral = ttkb.Label(f_dados_nota, text="MARKUP (%):", font=("Segoe UI", 9, "bold"))
    lbl_mkp_geral.pack(side="left", padx=(20, 2))
    ent_mkp_geral = ttkb.Entry(f_dados_nota, textvariable=var_markup_geral, width=8, font=("Segoe UI", 10, "bold"), justify="center")
    ent_mkp_geral.pack(side="left", padx=5)

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
            modal.geometry("650x750")
            modal.transient(root)
            modal.grab_set()
            
            bg_mod = "#34495e" if getattr(root, 'tema_atual', 'claro') == 'claro' else "#1a1a2e"
            
            f_t = tk.Frame(modal, bg=bg_mod, pady=15)
            f_t.pack(fill="x")
            tk.Label(f_t, text="TOTAL MERCADORIA + IPI A PAGAR:", fg="white", bg=bg_mod, font=("Segoe UI", 10)).pack()
            tk.Label(f_t, text=formatar_moeda(tot_nf), fg="#f1c40f", bg=bg_mod, font=("Segoe UI", 18, "bold")).pack()
            
            tipo_f = var_tipo_frete.get().strip()
            val_blog = 0.0
            if tipo_f == "CIF":
                txt_aviso = "🚚 FRETE CIF: B-LOG ISENTA (Receita R$ 0,00)"
                fg_aviso = "#7f8c8d" if getattr(root, 'tema_atual', 'claro') == 'claro' else "#9ca3af"
            elif tipo_f == "FOB":
                frete_perc = converter_moeda(linhas_nota[0]['var_frete'].get()) / 100 if linhas_nota else 0
                val_blog = tot_nf * frete_perc
                txt_aviso = f"🚚 FRETE FOB: Receita B-LOG {formatar_moeda(val_blog)}"
                fg_aviso = "#27ae60" if getattr(root, 'tema_atual', 'claro') == 'claro' else "#4ade80"
            else:
                txt_aviso = "🚚 FRETE TERCEIRIZADO"
                fg_aviso = "#e67e22" if getattr(root, 'tema_atual', 'claro') == 'claro' else "#fbbf24"
                
            tk.Label(f_t, text=txt_aviso, fg=fg_aviso, bg=bg_mod, font=("Segoe UI", 11, "bold")).pack(pady=5)
            
            f_p = tk.Frame(modal, pady=10)
            f_p.pack(fill="x", padx=20)
            var_pag = tk.StringVar(value="BOLETOS")
            f_b = tk.Frame(modal, pady=10)
            lbl_d = tk.Label(modal, text="DIFERENÇA: " + formatar_moeda(tot_nf), font=("Segoe UI", 14, "bold"), fg="#c0392b")
            
            var_dinheiro = tk.StringVar(value="R$ 0,00")
            f_dinheiro = tk.Frame(f_b)
            tk.Label(f_dinheiro, text="Entrada em Dinheiro:", width=18, anchor="e", font=("Segoe UI", 10, "bold"), fg="#27ae60").pack(side="left")
            ent_dinheiro = tk.Entry(f_dinheiro, textvariable=var_dinheiro, width=16, justify="right", font=("Segoe UI", 10, "bold"))
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
                    lbl_d.config(text="LIBERADO (BLU / À VISTA)", fg="#27ae60")
                    btn_e.config(state="normal")
                elif var_pag.get() == "PENDENTES": 
                    f_b.pack_forget()
                    f_dinheiro.pack_forget()
                    lbl_d.config(text="⚠️ LIBERADO COM PENDÊNCIA", fg="#f39c12")
                    btn_e.config(state="normal")
                elif var_pag.get() == "DINHEIRO + BOLETO":
                    f_b.pack(fill="x", padx=20)
                    f_dinheiro.pack(fill="x", pady=(0, 10))
                    recalcular()
                else: 
                    f_b.pack(fill="x", padx=20)
                    f_dinheiro.pack_forget()
                    var_dinheiro.set("R$ 0,00")
                    recalcular()
                    
            tk.Radiobutton(f_p, text="BLU / Transferência À Vista", variable=var_pag, value="BLU / À VISTA", command=check).pack(anchor="w")
            tk.Radiobutton(f_p, text="Pagamento em Boletos", variable=var_pag, value="BOLETOS", command=check).pack(anchor="w")
            tk.Radiobutton(f_p, text="Dinheiro + Boleto (Misto)", variable=var_pag, value="DINHEIRO + BOLETO", command=check).pack(anchor="w")
            tk.Radiobutton(f_p, text="⏳ Boletos Pendentes (Aguardando Retorno)", variable=var_pag, value="PENDENTES", command=check).pack(anchor="w")
            
            f_boletos = tk.Frame(f_b)
            f_boletos.pack(fill="x")
            
            vars_b = []
            entradas_b = []
            prazos = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300]
            
            def recalcular(*args):
                s_boletos = sum(converter_moeda(v.get()) for v in vars_b)
                v_dinheiro = converter_moeda(var_dinheiro.get()) if var_pag.get() == "DINHEIRO + BOLETO" else 0.0
                
                diff = tot_nf - v_dinheiro - s_boletos
                
                if abs(diff) < 0.05: 
                    lbl_d.config(text="🟢 BATEU! R$ 0,00", fg="#27ae60")
                    btn_e.config(state="normal")
                else: 
                    lbl_d.config(text="🔴 DIFERENÇA: " + formatar_moeda(diff), fg="#c0392b")
                    btn_e.config(state="disabled")

            var_dinheiro.trace_add("write", recalcular)
            
            def add_boleto():
                idx = len(vars_b)
                if idx >= 10: return
                var = tk.StringVar()
                vars_b.append(var)
                row_frame = tk.Frame(f_boletos)
                row_frame.pack(fill="x", pady=2)
                tk.Label(row_frame, text=f"Boleto {idx+1} ({prazos[idx]} Dias):", width=16, anchor="e").pack(side="left")
                e = tk.Entry(row_frame, textvariable=var, width=16, justify="right", font=("Segoe UI", 10))
                e.pack(side="left", padx=10, ipady=3)
                e.bind("<FocusOut>", lambda ev, v=var: v.set(formatar_moeda(converter_moeda(v.get())) if v.get() else ""))
                e.bind("<Return>", lambda ev: btn_add.invoke() if len(vars_b) < 10 else btn_e.focus_set())
                var.trace_add("write", recalcular)
                entradas_b.append(e)
                e.focus_set()
                
            btn_add = tk.Button(f_b, text="+ Adicionar Boleto", command=add_boleto, font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", padx=10, pady=5)
            btn_add.pack(pady=10)
            add_boleto()
            lbl_d.pack(pady=15)
            
            # === FUNÇÃO DE COPIAR EMBUTIDA NA AUDITORIA ===
            def copiar_resumo_area_transferencia():
                # Cabeçalho da mensagem
                texto_copia = f"📌 *RESUMO DE PRECIFICAÇÃO - {combo_forn.get()}*\n"
                texto_copia += f"📝 Nota: {var_num_nota.get()} | Pedido: {var_pedido.get()}\n"
                texto_copia += f"==============================\n\n"

                # Loop pelos produtos
                for r in linhas_nota:
                    nome = r['var_nome'].get()
                    if r['var_cod'].get().strip() and nome not in ["---", "❌ PRODUTO NÃO ENCONTRADO"]:
                        custo = r['var_novo_custo'].get()
                        venda = r['var_venda'].get()
                        prazo = r['var_prazo'].get()
                        texto_copia += f"▪ {nome}\n   Custo: {custo} | Venda: {venda} | Prazo: {prazo}\n\n"
                        
                texto_copia += f"==============================\n"

                # Limpeza do rodapé
                resumo_base = lbl_res_formula.cget("text")
                resumo_limpo = re.sub(r'Itens:\s*\d+\s*\|\s*', '', resumo_base)
                
                texto_copia += resumo_limpo + "\n\nBoas vendas!"
                
                root.clipboard_clear()
                root.clipboard_append(texto_copia)
                messagebox.showinfo("Copiado!", "Resumo copiado para o WhatsApp!")

            def copiar_aviso_lojas():
                regime_av = var_regime.get()
                texto = f"🏪 *AVISO DE NOVOS PREÇOS - {combo_forn.get()}*\n"
                texto += f"==============================\n\n"
                for r in linhas_nota:
                    if r['var_cod'].get().strip() and r['var_nome'].get() not in ["---", "❌ PRODUTO NÃO ENCONTRADO"]:
                        cod   = r['var_cod'].get().strip()
                        nome  = r['var_nome'].get()
                        q_nf  = r['var_qtd_nf'].get()
                        q_bon = r['var_qtd_rom'].get()
                        venda = r['var_venda'].get()
                        prazo = r['var_prazo'].get()
                        if regime_av == "MISTA (NF + Romaneio)":
                            qtd_txt = q_bon
                        elif regime_av == "NOTA + BONIFICAÇÃO":
                            qtd_txt = f"{q_nf} NF + {q_bon} Bon = {int(float(q_nf or 0)+float(q_bon or 0))} un"
                        else:
                            qtd_txt = q_nf
                        texto += f"▪ Cód: {cod} | {nome}\n   Qtd: {qtd_txt} | Venda: {venda} | Prazo: {prazo}\n\n"
                texto += f"=============================="
                root.clipboard_clear()
                root.clipboard_append(texto)
                messagebox.showinfo("Copiado!", "Aviso para as lojas copiado!\n\nAgora é só apertar Ctrl+V no WhatsApp das lojas.")

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
                
            f_botoes_modal = tk.Frame(modal, bg=bg_mod)
            f_botoes_modal.pack(fill="x", padx=20, pady=10)

            # Linha 1 — botões de cópia lado a lado
            f_linha1 = tk.Frame(f_botoes_modal, bg=bg_mod)
            f_linha1.pack(fill="x", pady=(0, 6))

            btn_copiar = tk.Button(f_linha1, text="📋 COPIAR RESUMO P/ CHEFE", bg="#f39c12", fg="white", activebackground="#d68910", activeforeground="white", font=("Segoe UI", 10, "bold"), relief="flat", pady=10, command=copiar_resumo_area_transferencia)
            btn_copiar.pack(side="left", fill="x", expand=True, padx=(0, 5))

            btn_aviso_lojas = tk.Button(f_linha1, text="🏪 CRIAR AVISO PARA AS LOJAS", bg="#27ae60", fg="white", activebackground="#1e8449", activeforeground="white", font=("Segoe UI", 10, "bold"), relief="flat", pady=10, command=copiar_aviso_lojas)
            btn_aviso_lojas.pack(side="left", fill="x", expand=True, padx=(5, 0))

            # Linha 2 — confirmar e gerar (largura total)
            f_linha2 = tk.Frame(f_botoes_modal, bg=bg_mod)
            f_linha2.pack(fill="x")

            btn_e = tk.Button(f_linha2, text="✅ CONFIRMAR E GERAR", bg="#2980b9", fg="white", activebackground="#1f618d", activeforeground="white", font=("Segoe UI", 10, "bold"), relief="flat", pady=10, command=executar_exportacao)
            btn_e.pack(fill="x")
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


    f_resumo_container = ttkb.Labelframe(root, text=" 📊 DEMONSTRATIVO FINANCEIRO DA CARGA ", bootstyle="primary", padding=5)
    f_resumo_container.pack(fill="x", side="bottom", padx=10, pady=5)
    
    lbl_res_formula = ttkb.Label(f_resumo_container, text="Aguardando inserção de produtos...", font=("Segoe UI", 13, "bold"), bootstyle="danger")
    lbl_res_formula.pack(expand=True, pady=2)

    # =========================================================
    # BARRA DE AÇÕES E ALERTAS (NOVO LAYOUT)
    # =========================================================
    f_controle = ttkb.Frame(root, padding=5)
    f_controle.pack(fill="x", side="top", padx=20)
    
    # Botoes todos alinhados à esquerda para dar espaço e limpeza visual
    f_botoes_acao = ttkb.Frame(f_controle)
    f_botoes_acao.pack(side="left")

    btn_add_linha = ttkb.Button(f_botoes_acao, text="➕ ADICIONAR LINHA", style="Lilas.TButton", command=adicionar_linha)
    btn_add_linha.pack(side="left", padx=5)
    
    btn_limpar = ttkb.Button(f_botoes_acao, text="🧹 LIMPAR", style="Vermelho.TButton", command=lambda: limpar_nota(pergunta=True))
    btn_limpar.pack(side="left", padx=5)
    ToolTip(btn_limpar, text="Limpar todos os campos (Atalho: Ctrl + L)")
    
    btn_buscar = ttkb.Button(f_botoes_acao, text="🔍 PESQUISAR PROCESSO", style="Azul.TButton", command=pesquisar_carga_salva)
    btn_buscar.pack(side="left", padx=5)
    ToolTip(btn_buscar, text="Pesquisar por Nota, Pedido ou Fornecedor (Atalho: Ctrl + F)")
    
    btn_abrir = ttkb.Button(f_botoes_acao, text="📂 ABRIR SALVA", style="VerdeClaro.TButton", command=abrir_precificacao_salva)
    btn_abrir.pack(side="left", padx=5)

    btn_salvar_reimprimir = ttkb.Button(f_botoes_acao, text="💾 SALVAR E REIMPRIMIR", style="VerdeSalvar.TButton", command=reimprimir_processo)
    btn_salvar_reimprimir.pack(side="left", padx=5)
    ToolTip(btn_salvar_reimprimir, text="Salva os preços editados no arquivo original e reabre o espelho")

    btn_ex = ttkb.Button(f_botoes_acao, text="🔐 AUDITAR E FECHAR CARGA", style="VermelhoClaro.TButton", command=abrir_cofre_auditoria)
    btn_ex.pack(side="left", padx=10)
    ToolTip(btn_ex, text="Auditar e fechar carga (Atalho: Ctrl + S)")

    btn_fretes = ttkb.Button(f_botoes_acao, text="🚚 EDITAR FRETES", style="Marrom.TButton", command=lambda: abrir_modulo_fretes(root, pasta_fretes))
    btn_fretes.pack(side="left", padx=10)

    # Botão de pendências vai para a direita para não embolar
    btn_pendencias = ttkb.Button(f_controle, text="", style="VermelhoEscuro.TButton", command=lambda: mostrar_pendencias())

    def atualizar_alerta_pendencias():
        pendentes = glob.glob(os.path.join(pasta_arquivo, "*_PENDENTE.xlsx"))
        if pendentes: 
            btn_pendencias.config(text=f"⚠️ {len(pendentes)} PEDIDO(S) PENDENTE(S)")
            btn_pendencias.pack(side="right", padx=20) 
        else: 
            btn_pendencias.pack_forget()

    # Aviso inteligente APENAS na inicialização
    def verificar_db_startup():
        sucesso, msg, is_outdated = carregar_dados_memoria(diretorio_atual)
        if is_outdated:
            # Pula na tela apenas se o arquivo tiver mais de 24h
            messagebox.showwarning("Aviso de Banco Desatualizado", f"Atenção: Os relatórios do FDC estão com atraso de mais de 24 horas!\n\n{msg}\n\nLembre-se de gerar relatórios novos para garantir que os preços e estoques estejam corretos.")
        atualizar_alerta_pendencias()
            
    root.after(500, verificar_db_startup)

    # === ATALHOS GLOBAIS DE TECLADO ===
    root.bind("<Control-n>", lambda e: pular_foco(ent_nota))
    root.bind("<Control-N>", lambda e: pular_foco(ent_nota))
    
    root.bind("<Control-l>", lambda e: limpar_nota(pergunta=True))
    root.bind("<Control-L>", lambda e: limpar_nota(pergunta=True))
    
    root.bind("<Control-s>", lambda e: abrir_cofre_auditoria())
    root.bind("<Control-S>", lambda e: abrir_cofre_auditoria())
    
    root.bind("<Control-f>", lambda e: pesquisar_carga_salva())
    root.bind("<Control-F>", lambda e: pesquisar_carga_salva())

    root.after(100, lambda: limpar_nota(pergunta=False, add_linha=True))
    root.mainloop()

if __name__ == "__main__":
    criar_tela()