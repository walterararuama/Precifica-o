import os
import sqlite3
import pandas as pd
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttkb
import html as html_escape_module
import tempfile
import webbrowser

def inicializar_banco_fornecedores(db_path, diretorio_atual):
    with sqlite3.connect(db_path, timeout=10) as conn:
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
                            if fabricante and fabricante.lower() != 'nan':
                                ipi_calc = pd.to_numeric(str(row.iloc[1]).replace(',','.'), errors='coerce') if len(row) > 1 else 0.0
                                frete_val = pd.to_numeric(str(row.iloc[2]).replace(',','.'), errors='coerce') if len(row) > 2 else 0.0
                                markup_val = pd.to_numeric(str(row.iloc[3]).replace(',','.'), errors='coerce') if len(row) > 3 else 1.0
                                if pd.isna(ipi_calc): ipi_calc = 0.0
                                if pd.isna(frete_val): frete_val = 0.0
                                if pd.isna(markup_val): markup_val = 1.0
                                cursor.execute('INSERT INTO fornecedores (fabricante, uf, ipi_calculo, frete, markup) VALUES (?, "", ?, ?, ?)', (fabricante, ipi_calc, frete_val, markup_val))
                        except: pass
                    conn.commit()
                except: pass

def carregar_fornecedores_db(db_path):
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.cursor().execute("SELECT * FROM fornecedores ORDER BY fabricante").fetchall()]
    except: return []

def get_lista_nomes_fornecedores(db_path):
    return [f['fabricante'] for f in carregar_fornecedores_db(db_path)]

def abrir_gerenciador_fornecedores(root, combo_forn, db_path):
    janela_forn = tk.Toplevel(root)
    janela_forn.title("Gerenciador de Fornecedores")
    largura_janela, altura_janela = 1000, 650
    janela_forn.update_idletasks() 
    pos_x = (janela_forn.winfo_screenwidth() // 2) - (largura_janela // 2)
    pos_y = (janela_forn.winfo_screenheight() // 2) - (altura_janela // 2)
    janela_forn.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
    janela_forn.transient(root); janela_forn.grab_set()
    
    f_lista = ttkb.Labelframe(janela_forn, text=" Fornecedores Cadastrados ", padding=10)
    f_lista.pack(fill="both", expand=True, padx=10, pady=5)
    
    colunas = ("ID", "Fabricante", "UF", "IPI (%)", "Frete (%)", "Markup (%)")
    tree = ttkb.Treeview(f_lista, columns=colunas, show="headings", bootstyle="info")
    
    scrollbar_y = ttkb.Scrollbar(f_lista, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar_y.set)
    scrollbar_y.pack(side="right", fill="y")
    
    for col in colunas: tree.heading(col, text=col); tree.column(col, width=100, anchor="center")
    tree.column("Fabricante", width=250, anchor="w")
    tree.column("UF", width=60, anchor="center")
    tree.pack(side="left", fill="both", expand=True) 
    
    f_form = ttkb.Labelframe(janela_forn, text=" Editar / Novo Fornecedor ", padding=10)
    f_form.pack(fill="x", padx=10, pady=5)
    entradas = {}
    
    campos = [("Fabricante:", "fabricante"), ("UF (Estado):", "uf"), ("IPI de Cálculo (%):", "ipi_calculo"), ("Frete (%):", "frete"), ("MarkUp (% ex: 130):", "markup")]
    for i, (label_text, key) in enumerate(campos):
        r, c = i // 3, (i % 3) * 2
        ttkb.Label(f_form, text=label_text, font=("Segoe UI", 10, "bold")).grid(row=r, column=c, padx=5, pady=8, sticky="e")
        ent = ttkb.Entry(f_form, font=("Segoe UI", 10), width=18); ent.grid(row=r, column=c+1, padx=5, pady=8, sticky="w")
        entradas[key] = ent
        
    id_selecionado = tk.StringVar()

    def carregar_dados():
        for row in tree.get_children(): tree.delete(row)
        for l in carregar_fornecedores_db(db_path):
            tree.insert("", "end", values=(l['id'], l['fabricante'], l['uf'], f"{l['ipi_calculo']*100:.2f}%", f"{l['frete']*100:.2f}%", f"{l['markup']*100:.2f}%"))

    def ao_selecionar(event):
        try:
            valores = tree.item(tree.selection()[0], "values"); id_selecionado.set(valores[0])
            with sqlite3.connect(db_path, timeout=10) as conn:
                dados = conn.cursor().execute("SELECT fabricante, uf, ipi_calculo, frete, markup FROM fornecedores WHERE id=?", (valores[0],)).fetchone()
            for key in entradas: entradas[key].delete(0, tk.END)
            entradas["fabricante"].insert(0, dados[0] or ""); entradas["uf"].insert(0, dados[1] or "")
            entradas["ipi_calculo"].insert(0, str(round((dados[2] or 0)*100, 2))); entradas["frete"].insert(0, str(round((dados[3] or 0)*100, 2)))
            entradas["markup"].insert(0, str(round((dados[4] or 1.0)*100, 2)))
        except IndexError: pass

    tree.bind("<<TreeviewSelect>>", ao_selecionar)

    def salvar_fornecedor(event=None):
        fab, uf = entradas["fabricante"].get().strip().upper(), entradas["uf"].get().strip().upper()
        if not fab: return messagebox.showerror("Erro", "O nome do fabricante é obrigatório!", parent=janela_forn)
        try:
            ipi_raw = float(entradas["ipi_calculo"].get().replace(',','.') or 0)
            frete_raw = float(entradas["frete"].get().replace(',','.') or 0)
            markup_raw = float(entradas["markup"].get().replace(',','.') or 130.0)

            ipi_val = max(0.0, ipi_raw) / 100.0
            frete_val = max(0.0, frete_raw) / 100.0
            markup_val = max(1.0, markup_raw) / 100.0

            with sqlite3.connect(db_path, timeout=10) as conn:
                if id_selecionado.get(): conn.cursor().execute('UPDATE fornecedores SET fabricante=?, uf=?, ipi_calculo=?, frete=?, markup=? WHERE id=?', (fab, uf, ipi_val, frete_val, markup_val, id_selecionado.get()))
                else: conn.cursor().execute('INSERT INTO fornecedores (fabricante, uf, ipi_calculo, frete, markup) VALUES (?, ?, ?, ?, ?)', (fab, uf, ipi_val, frete_val, markup_val))
                conn.commit()
            carregar_dados(); limpar_form()

            combo_forn.master_list = get_lista_nomes_fornecedores(db_path)
            combo_forn['values'] = combo_forn.master_list
            if hasattr(root, 'atualizar_cache_fornecedores'):
                root.atualizar_cache_fornecedores()

            messagebox.showinfo("Sucesso", "Fornecedor salvo!", parent=janela_forn)
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                messagebox.showwarning("Banco Ocupado", "O sistema está sendo usado por outro usuário.\nAguarde alguns segundos e tente novamente.", parent=janela_forn)
            else:
                messagebox.showerror("Erro", f"Falha ao salvar: {e}", parent=janela_forn)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}", parent=janela_forn)
        
        return "break"

    def apagar_fornecedor():
        if id_selecionado.get():
            top = tk.Toplevel(janela_forn)
            top.attributes('-topmost', True)
            top.withdraw()
            confirmou = messagebox.askyesno("Confirmar", "Deseja apagar o fornecedor selecionado?", parent=top)
            top.destroy()
            if confirmou:
                try:
                    with sqlite3.connect(db_path, timeout=10) as conn:
                        conn.cursor().execute("DELETE FROM fornecedores WHERE id=?", (id_selecionado.get(),))
                    carregar_dados()
                    limpar_form()
                    combo_forn.master_list = get_lista_nomes_fornecedores(db_path)
                    combo_forn['values'] = combo_forn.master_list
                    if hasattr(root, 'atualizar_cache_fornecedores'):
                        root.atualizar_cache_fornecedores()
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        messagebox.showwarning("Banco Ocupado", "O sistema está sendo usado por outro usuário.\nAguarde alguns segundos e tente novamente.", parent=janela_forn)
                    else:
                        messagebox.showerror("Erro", f"Falha ao apagar: {e}", parent=janela_forn)

    def limpar_form():
        id_selecionado.set(""); [ent.delete(0, tk.END) for ent in entradas.values()]; entradas["fabricante"].focus_set()

    f_botoes = tk.Frame(janela_forn); f_botoes.pack(pady=10)
    ttkb.Button(f_botoes, text="➕ Novo", command=limpar_form, bootstyle="info").pack(side="left", padx=5)
    ttkb.Button(f_botoes, text="💾 Salvar", command=salvar_fornecedor, bootstyle="success").pack(side="left", padx=5)
    ttkb.Button(f_botoes, text="🗑️ Apagar", command=apagar_fornecedor, bootstyle="danger").pack(side="left", padx=5)
    ttkb.Button(f_botoes, text="🔙 VOLTAR", command=janela_forn.destroy, bootstyle="warning").pack(side="left", padx=5)
    
    entradas["fabricante"].bind("<Return>", lambda e: entradas["uf"].focus_set() or "break")
    entradas["uf"].bind("<Return>", lambda e: entradas["ipi_calculo"].focus_set() or "break")
    entradas["ipi_calculo"].bind("<Return>", lambda e: entradas["frete"].focus_set() or "break")
    entradas["frete"].bind("<Return>", lambda e: entradas["markup"].focus_set() or "break")
    entradas["markup"].bind("<Return>", salvar_fornecedor)

    carregar_dados()