import os
import sqlite3
import pandas as pd
import tkinter as tk
from tkinter import messagebox, ttk
import ttkbootstrap as ttkb

def inicializar_banco_fornecedores(db_path, diretorio_atual):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fornecedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fabricante TEXT UNIQUE NOT NULL,
                uf TEXT DEFAULT '',
                ipi_calculo REAL,
                frete REAL,
                markup REAL
            )
        ''')
        try: cursor.execute("ALTER TABLE fornecedores ADD COLUMN uf TEXT DEFAULT ''")
        except sqlite3.OperationalError: pass
            
        cursor.execute("SELECT COUNT(*) FROM fornecedores")
        if cursor.fetchone()[0] == 0:
            opcoes_excel = ["Fornecedores.xlsx", "FOrnecedores.xlsx", "fornecedores.xlsx"]
            excel_path = next((os.path.join(diretorio_atual, o) for o in opcoes_excel if os.path.exists(os.path.join(diretorio_atual, o))), None)
            if excel_path:
                try:
                    df = pd.read_excel(excel_path)
                    for _, row in df.iterrows():
                        try:
                            fabricante = str(row.iloc[0]).strip()
                            if fabricante and str(fabricante).lower() != "nan":
                                ipi = float(row.iloc[1]) if pd.notna(row.iloc[1]) else 0.0
                                frete = float(row.iloc[2]) if pd.notna(row.iloc[2]) else 0.0
                                markup = float(row.iloc[3]) if pd.notna(row.iloc[3]) else 0.0
                                cursor.execute("INSERT OR IGNORE INTO fornecedores (fabricante, ipi_calculo, frete, markup) VALUES (?, ?, ?, ?)", 
                                               (fabricante.upper(), ipi, frete, markup))
                        except Exception: continue
                    conn.commit()
                except Exception as e:
                    print(f"Erro na importação: {e}")

def carregar_fornecedores_db(db_path):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        cursor.execute("SELECT id, fabricante, uf, ipi_calculo, frete, markup FROM fornecedores ORDER BY fabricante")
        return [dict(row) for row in cursor.fetchall()]

def get_lista_nomes_fornecedores(db_path):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT fabricante FROM fornecedores ORDER BY fabricante")
            return [row[0] for row in cursor.fetchall()]
    except: return []

# --- FUNÇÕES DE FORMATAÇÃO INTELIGENTE BR ---
def para_percentual_br(val):
    if val is None or val == "": return "0,0%"
    try:
        v = float(val) * 100
        if v.is_integer():
            return f"{int(v)},0%"
        else:
            s = f"{v:.4f}".rstrip('0')
            if s.endswith('.'): s += '0'
            return s.replace('.', ',') + '%'
    except:
        return "0,0%"

def abrir_gerenciador_fornecedores(root, combo_forn, db_path):
    try:
        janela_forn = ttkb.Toplevel(root)
        janela_forn.title("Gerenciador de Fornecedores")
        janela_forn.geometry("1280x720") 
        janela_forn.transient(root)
        janela_forn.grab_set()

        # ==========================================================
        # LEITURA DO TEMA PARA ADAPTAÇÃO DA ZEBRA
        # ==========================================================
        estilo_global = ttkb.Style()
        cores = estilo_global.colors
        is_dark = estilo_global.theme.type == 'dark'

        # Usando ttk puro para não causar curto-circuito no ttkbootstrap
        estilo_tree = ttk.Style()
        estilo_tree.configure("Treeview", rowheight=28, borderwidth=1)

        # Variáveis de Controle
        id_selecionado = tk.StringVar(janela_forn)
        var_fab = tk.StringVar(janela_forn)
        var_uf = tk.StringVar(janela_forn)
        var_ipi = tk.StringVar(janela_forn)
        var_frete = tk.StringVar(janela_forn)
        var_markup = tk.StringVar(janela_forn)
        
        var_filtro_fab = tk.StringVar(janela_forn)
        var_filtro_uf = tk.StringVar(janela_forn)
        var_filtro_frete = tk.StringVar(janela_forn)
        var_filtro_ipi = tk.StringVar(janela_forn)
        var_filtro_markup = tk.StringVar(janela_forn)

        var_total_forn = tk.StringVar(janela_forn, value="TOTAL de FORNECEDORES: 0")

        # =========================================================================
        #   BLOCO DE FUNÇÕES INTERNAS
        # =========================================================================
        def atualizar_contador_total():
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM fornecedores")
                total = cursor.fetchone()[0]
                var_total_forn.set(f"TOTAL de FORNECEDORES: {total}")

        def limpar_form():
            id_selecionado.set("")
            var_fab.set("")
            var_uf.set("")
            var_ipi.set("")
            var_frete.set("")
            var_markup.set("")
            entradas["fabricante"].focus_set()

        def aplicar_filtros(event=None):
            fab = var_filtro_fab.get().upper()
            uf = var_filtro_uf.get().upper()
            ipi = var_filtro_ipi.get().replace(',', '.')
            frete = var_filtro_frete.get().replace(',', '.')
            markup = var_filtro_markup.get().replace(',', '.')
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                query_full = "SELECT id, fabricante, uf, ipi_calculo, frete, markup FROM fornecedores ORDER BY fabricante"
                linhas = cursor.execute(query_full).fetchall()
                
            for row in tree.get_children():
                tree.delete(row)
                
            idx_visual = 0
            for row in linhas:
                id_f, fab_f, uf_f, ipi_f, frete_f, mkp_f = row
                
                txt_ipi = para_percentual_br(ipi_f)
                txt_frete = para_percentual_br(frete_f)
                txt_markup = para_percentual_br(mkp_f)
                txt_uf = str(uf_f).upper() if uf_f else ""
                
                if fab and fab not in str(fab_f).upper(): continue
                if uf and uf not in txt_uf: continue
                if ipi and ipi not in txt_ipi.replace(',', '.'): continue
                if frete and frete not in txt_frete.replace(',', '.'): continue
                if markup and markup not in txt_markup.replace(',', '.'): continue
                
                tag = 'par' if idx_visual % 2 == 0 else 'impar'
                tree.insert("", "end", values=(id_f, fab_f, txt_uf, txt_ipi, txt_frete, txt_markup), tags=(tag,))
                idx_visual += 1
            
            atualizar_contador_total()

        def salvar_fornecedor(event=None):
            fab = var_fab.get().strip().upper()
            if not fab: return messagebox.showwarning("Aviso", "O nome do Fabricante é obrigatório.")
            
            uf = var_uf.get().strip().upper()
            
            def tratar_num_percentual(val):
                try: return float(str(val).replace(',', '.')) / 100.0
                except: return 0.0
                
            ipi = tratar_num_percentual(var_ipi.get())
            frete = tratar_num_percentual(var_frete.get())
            markup = tratar_num_percentual(var_markup.get())
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                if id_selecionado.get():
                    cursor.execute("UPDATE fornecedores SET fabricante=?, uf=?, ipi_calculo=?, frete=?, markup=? WHERE id=?", 
                                   (fab, uf, ipi, frete, markup, id_selecionado.get()))
                else:
                    try: cursor.execute("INSERT INTO fornecedores (fabricante, uf, ipi_calculo, frete, markup) VALUES (?, ?, ?, ?, ?)", (fab, uf, ipi, frete, markup))
                    except sqlite3.IntegrityError: return messagebox.showerror("Erro", "Fornecedor já existe.")
                conn.commit()
                
            aplicar_filtros()
            limpar_form()
            combo_forn.master_list = get_lista_nomes_fornecedores(db_path)
            combo_forn['values'] = combo_forn.master_list
            if hasattr(root, 'atualizar_cache_fornecedores'): root.atualizar_cache_fornecedores()

        def apagar_fornecedor():
            if not id_selecionado.get(): return messagebox.showwarning("Aviso", "Selecione um fornecedor para excluir.")
            if messagebox.askyesno("Confirmar", "Deseja realmente apagar este fornecedor?"):
                with sqlite3.connect(db_path) as conn:
                    conn.cursor().execute("DELETE FROM fornecedores WHERE id=?", (id_selecionado.get(),))
                    conn.commit()
                aplicar_filtros()
                limpar_form()
                combo_forn.master_list = get_lista_nomes_fornecedores(db_path)
                combo_forn['values'] = combo_forn.master_list
                if hasattr(root, 'atualizar_cache_fornecedores'): root.atualizar_cache_fornecedores()

        # =========================================================================
        # --- ÁREA SUPERIOR: FILTROS DINÂMICOS (Puro ttkbootstrap - Adapta ao fundo!) ---
        # =========================================================================
        f_filtros = ttkb.Labelframe(janela_forn, text=" 🔎 Filtros de Pesquisa Rápida ", padding=10, bootstyle="info")
        f_filtros.pack(fill="x", padx=15, pady=(15, 5))

        ttkb.Label(f_filtros, text="Filtro Fabricante:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=5, pady=2, sticky="e")
        ent_filtro_fab = ttkb.Entry(f_filtros, textvariable=var_filtro_fab, width=22)
        ent_filtro_fab.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttkb.Label(f_filtros, text="Estado (UF):", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=5, pady=2, sticky="e")
        ent_filtro_uf = ttkb.Entry(f_filtros, textvariable=var_filtro_uf, width=8)
        ent_filtro_uf.grid(row=0, column=3, padx=5, pady=2, sticky="w")

        ttkb.Label(f_filtros, text="IPI:", font=("Segoe UI", 9, "bold")).grid(row=0, column=4, padx=5, pady=2, sticky="e")
        ent_filtro_ipi = ttkb.Entry(f_filtros, textvariable=var_filtro_ipi, width=8)
        ent_filtro_ipi.grid(row=0, column=5, padx=5, pady=2, sticky="w")

        ttkb.Label(f_filtros, text="Frete:", font=("Segoe UI", 9, "bold")).grid(row=0, column=6, padx=5, pady=2, sticky="e")
        ent_filtro_frete = ttkb.Entry(f_filtros, textvariable=var_filtro_frete, width=8)
        ent_filtro_frete.grid(row=0, column=7, padx=5, pady=2, sticky="w")

        ttkb.Label(f_filtros, text="Markup:", font=("Segoe UI", 9, "bold")).grid(row=0, column=8, padx=5, pady=2, sticky="e")
        ent_filtro_markup = ttkb.Entry(f_filtros, textvariable=var_filtro_markup, width=8)
        ent_filtro_markup.grid(row=0, column=9, padx=5, pady=2, sticky="w")

        ttkb.Button(f_filtros, text="🔄 Limpar Filtros", bootstyle="danger", 
                    command=lambda: [var_filtro_fab.set(""), var_filtro_uf.set(""), var_filtro_frete.set(""), var_filtro_ipi.set(""), var_filtro_markup.set(""), aplicar_filtros()]).grid(row=0, column=10, padx=15)

        # =========================================================================
        # --- ÁREA DO MEIO: FORMULÁRIO DE CADASTRO/EDIÇÃO ---
        # =========================================================================
        f_form = ttkb.Labelframe(janela_forn, text=" Cadastro / Edição ", padding=15, bootstyle="info")
        f_form.pack(fill="x", padx=15, pady=5)

        campos = [
            ("Fabricante:", var_fab, 35, "fabricante"), 
            ("UF (Estado):", var_uf, 10, "uf"), 
            ("IPI (%):", var_ipi, 10, "ipi"), 
            ("Frete (%):", var_frete, 10, "frete"), 
            ("Markup (%):", var_markup, 10, "markup")
        ]
        
        entradas = {}
        for i, (lbl, var, w, key) in enumerate(campos):
            ttkb.Label(f_form, text=lbl, font=("Segoe UI", 9, "bold")).grid(row=0, column=i*2, padx=5, pady=5, sticky="e")
            ent = ttkb.Entry(f_form, textvariable=var, width=w)
            ent.grid(row=0, column=i*2+1, padx=5, pady=5, sticky="w")
            entradas[key] = ent

        f_botoes = ttkb.Frame(f_form)
        f_botoes.grid(row=1, column=0, columnspan=10, pady=10, sticky="ew")

        f_botoes_esquerda = ttkb.Frame(f_botoes)
        f_botoes_esquerda.pack(side="left")

        ttkb.Button(f_botoes_esquerda, text="➕ Novo", command=limpar_form, bootstyle="primary").pack(side="left", padx=5)
        ttkb.Button(f_botoes_esquerda, text="💾 Salvar", command=salvar_fornecedor, bootstyle="success").pack(side="left", padx=5)
        ttkb.Button(f_botoes_esquerda, text="🗑️ APAGAR FORNECEDOR", command=apagar_fornecedor, bootstyle="danger").pack(side="left", padx=5)
        ttkb.Button(f_botoes_esquerda, text="🔙 VOLTAR", command=janela_forn.destroy, bootstyle="warning").pack(side="left", padx=5)

        ttkb.Label(f_botoes, textvariable=var_total_forn, font=("Segoe UI", 10, "bold"), bootstyle="danger").pack(side="right", padx=15)

        # =========================================================================
        # --- ÁREA INFERIOR: TREEVIEW (ZEBRA COM CORES DE FONTE FORÇADAS) ---
        # =========================================================================
        f_lista = ttkb.Frame(janela_forn)
        f_lista.pack(fill="both", expand=True, padx=15, pady=10)

        scroll_y = ttkb.Scrollbar(f_lista, orient="vertical")
        scroll_y.pack(side="right", fill="y")
        
        colunas = ("ID", "Fabricante", "UF", "IPI (%)", "Frete (%)", "Markup (%)")
        tree = ttk.Treeview(f_lista, columns=colunas, show="headings", yscrollcommand=scroll_y.set)
        scroll_y.config(command=tree.yview)

        larguras = {"ID": 50, "Fabricante": 450, "UF": 80, "IPI (%)": 120, "Frete (%)": 120, "Markup (%)": 120}
        
        for col in colunas:
            tree.heading(col, text=col)
            tree.column(col, width=larguras[col], anchor="center")
        
        tree.pack(fill="both", expand=True)

        # BLINDAGEM DA FONTE: Força as letras a contrastarem com o fundo da Zebra
        if is_dark:
            tree.tag_configure('par', background="#2b303b", foreground="#ffffff")
            tree.tag_configure('impar', background=cores.bg, foreground="#ffffff")
        else:
            tree.tag_configure('par', background="#f0f3f5", foreground="#000000")
            tree.tag_configure('impar', background=cores.bg, foreground="#000000")

        # --- EVENTOS E GATILHOS DE TECLADO/MOUSE ---
        ent_filtro_fab.bind('<KeyRelease>', aplicar_filtros)
        ent_filtro_uf.bind('<KeyRelease>', aplicar_filtros)
        ent_filtro_ipi.bind('<KeyRelease>', aplicar_filtros)
        ent_filtro_frete.bind('<KeyRelease>', aplicar_filtros)
        ent_filtro_markup.bind('<KeyRelease>', aplicar_filtros)

        def on_tree_select(event):
            sel = tree.selection()
            if not sel: return
            item = tree.item(sel[0])['values']
            id_selecionado.set(item[0])
            var_fab.set(item[1])
            var_uf.set(item[2])
            var_ipi.set(str(item[3]).replace('%', ''))
            var_frete.set(str(item[4]).replace('%', ''))
            var_markup.set(str(item[5]).replace('%', ''))

        tree.bind("<<TreeviewSelect>>", on_tree_select)

        entradas["fabricante"].bind("<Return>", lambda e: entradas["uf"].focus_set())
        entradas["uf"].bind("<Return>", lambda e: entradas["ipi"].focus_set())
        entradas["ipi"].bind("<Return>", lambda e: entradas["frete"].focus_set())
        entradas["frete"].bind("<Return>", lambda e: entradas["markup"].focus_set())
        entradas["markup"].bind("<Return>", salvar_fornecedor)

        aplicar_filtros()

    except Exception as e:
        import traceback
        messagebox.showerror("Erro Crítico", f"Ocorreu um problema ao tentar abrir a aba de fornecedores:\n\n{e}\n\n{traceback.format_exc()}")