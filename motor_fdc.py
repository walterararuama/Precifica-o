import pandas as pd
import glob
import os
import time
from datetime import datetime

# Memória virtual do sistema
cache_fdc = {'posicao': pd.DataFrame(), 'basico': pd.DataFrame(), 'carregado': False, 'info_bas': "", 'info_pos': ""}

def buscar_arquivo_recente(palavra_chave, diretorio_atual):
    arquivos = glob.glob(os.path.join(diretorio_atual, f"*{palavra_chave}*.csv")) + glob.glob(os.path.join(diretorio_atual, f"*{palavra_chave}*.xlsx"))
    return max(arquivos, key=os.path.getmtime) if arquivos else None

def carregar_planilha(caminho):
    try:
        if caminho.endswith('.csv'):
            try: df = pd.read_csv(caminho, sep=';', encoding='latin-1')
            except: df = pd.read_csv(caminho, sep=';', encoding='utf-8')
        else: df = pd.read_excel(caminho)
        df.columns = df.columns.astype(str).str.strip().str.upper().str.replace(r'[^A-Z0-9]', '', regex=True)
        return df
    except: return pd.DataFrame()

def carregar_dados_memoria(diretorio_atual):
    arq_pos = buscar_arquivo_recente("posicao", diretorio_atual)
    arq_bas = buscar_arquivo_recente("basico", diretorio_atual)
    
    if not arq_pos or not arq_bas: return False, "Arquivos FDC não encontrados.", False
    
    agora = time.time()
    tempo_bas, tempo_pos = os.path.getmtime(arq_bas), os.path.getmtime(arq_pos)
    is_outdated = (agora - tempo_bas > 86400) or (agora - tempo_pos > 86400)
    
    dt_bas = datetime.fromtimestamp(tempo_bas).strftime('%d/%m %H:%M')
    dt_pos = datetime.fromtimestamp(tempo_pos).strftime('%d/%m %H:%M')
    
    cache_fdc['info_bas'], cache_fdc['info_pos'] = dt_bas, dt_pos
    df_pos, df_bas = carregar_planilha(arq_pos), carregar_planilha(arq_bas)
    
    col_cod_bas = next((c for c in ['IDPRODUTO', 'COD', 'CODIGO'] if c in df_bas.columns), None)
    col_nome_bas = next((c for c in ['DESCRICAOPRODUTO', 'NOME', 'PRODUTO'] if c in df_bas.columns), None)
    if col_cod_bas: 
        df_bas['_cod_str'] = df_bas[col_cod_bas].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    if col_nome_bas:
        df_bas['_nome_str'] = df_bas[col_nome_bas].astype(str).str.strip()
        
    col_cod_pos = next((c for c in ['COD', 'CODIGO', 'IDPRODUTO'] if c in df_pos.columns), None)
    if col_cod_pos: 
        df_pos['_cod_str'] = df_pos[col_cod_pos].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    
    cache_fdc['posicao'], cache_fdc['basico'], cache_fdc['carregado'] = df_pos, df_bas, True
    
    msg_status = f"⚠️ ALERTA (> 24h) | Básica: {dt_bas} | Posição: {dt_pos}" if is_outdated else f"🟢 Atualizado | Básica: {dt_bas} | Posição: {dt_pos}"
    return True, msg_status, is_outdated