"""
PREPARAR RELATÓRIO DE POSIÇÃO FINANCEIRA - FDC
===============================================
Como usar:
  1. Coloque o executável e os arquivos CSV do FDC na mesma pasta
  2. Dê duplo clique no executável
  3. Clique em "Gerar Relatório"

O script faz:
  - "Relatório de Produto Basico.csv": troca pontos por vírgulas e salva com mesmo nome
  - Demais CSVs (posição financeira): limpa totalizadores, une e salva como
    relatorio-posicao-financiera.csv (sobrescreve)
"""

import os
import sys
import threading
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext

from preparador_fdc import (
    executar,
    ARQUIVO_SAIDA_POSICAO, ENCODING_CSV, SEPARADOR_CSV, COLUNAS_ESPERADAS,
    _normalizar, eh_produto_basico, trocar_pontos_virgulas,
    processar_produto_basico, processar_posicao,
)


def main():
    if getattr(sys, "frozen", False):
        pasta = os.path.dirname(sys.executable)
    else:
        pasta = os.path.dirname(os.path.abspath(__file__))

    root = tk.Tk()
    root.title("Relatorio FDC")
    root.geometry("620x480")
    root.resizable(False, False)
    root.configure(bg="#F3F3F3")

    tk.Label(
        root, text="PREPARACAO DO RELATORIO - FDC",
        font=("Segoe UI", 13, "bold"), bg="#F3F3F3", pady=8
    ).pack()

    tk.Label(
        root, text=f"Pasta: {pasta}",
        font=("Segoe UI", 8), fg="#666666", bg="#F3F3F3", wraplength=600
    ).pack()

    log_area = scrolledtext.ScrolledText(
        root, height=18, width=74,
        font=("Consolas", 9), state="disabled",
        bg="#1E1E1E", fg="#D4D4D4", insertbackground="white",
        relief="flat"
    )
    log_area.pack(padx=10, pady=8)

    btn = tk.Button(
        root, text="Gerar Relatorio",
        font=("Segoe UI", 11, "bold"),
        bg="#0078D4", fg="white",
        padx=24, pady=8, relief="flat", cursor="hand2",
        activebackground="#005A9E", activeforeground="white"
    )
    btn.pack(pady=4)

    def log_fn(msg):
        def _up():
            log_area.config(state="normal")
            log_area.insert(tk.END, msg + "\n")
            log_area.see(tk.END)
            log_area.config(state="disabled")
        root.after(0, _up)

    def on_done(success):
        def _up():
            if success:
                btn.config(state="normal", text="Gerar novamente", bg="#107C10")
            else:
                btn.config(state="normal", text="Tentar novamente", bg="#C50F1F")
        root.after(0, _up)

    def iniciar():
        btn.config(state="disabled", text="Processando...", bg="#555555")
        log_area.config(state="normal")
        log_area.delete("1.0", tk.END)
        log_area.config(state="disabled")
        log_fn(f"Iniciado: {datetime.now().strftime('%d/%m/%Y  %H:%M:%S')}")
        log_fn(f"Pasta: {pasta}")
        log_fn("")
        threading.Thread(target=executar, args=(pasta, log_fn, on_done), daemon=True).start()

    btn.config(command=iniciar)
    root.mainloop()


if __name__ == "__main__":
    main()
