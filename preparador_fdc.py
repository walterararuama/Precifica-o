import os
import glob
import unicodedata
import pandas as pd
from datetime import datetime

ARQUIVO_SAIDA_POSICAO = "relatorio-posicao-financiera.csv"
ENCODING_CSV          = "latin1"
SEPARADOR_CSV         = ";"

COLUNAS_ESPERADAS = [
    "Filial", "Cod.", "EAN", "Descricao do Produto", "Ult.Compra",
    "Q.Gerencial", "Q.Somado", "Custo", "Subtotal", "Venda", "Subtotal.1"
]


def _normalizar(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()


def eh_produto_basico(caminho: str) -> bool:
    nome = _normalizar(os.path.basename(caminho))
    return "produto" in nome and ("basico" in nome or "básico" in nome)


def trocar_pontos_virgulas(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        df[col] = df[col].apply(
            lambda v: str(v).replace(".", ",")
            if pd.notna(v) and str(v) not in ("nan", "NaN", "") else v
        )
    return df


def processar_produto_basico(caminho: str, log_fn):
    nome = os.path.basename(caminho)
    log_fn(f"[Produto Basico] Lendo: {nome}")
    df = pd.read_csv(caminho, sep=SEPARADOR_CSV, encoding=ENCODING_CSV,
                     dtype=str, header=0, on_bad_lines="skip")
    df.columns = [c.strip() for c in df.columns]
    total = len(df)
    df = trocar_pontos_virgulas(df)
    df.to_csv(caminho, sep=SEPARADOR_CSV, encoding=ENCODING_CSV, index=False)
    log_fn(f"  {total} linhas — pontos trocados por virgulas")
    log_fn(f"  Salvo: {nome}")


def processar_posicao(caminho: str, log_fn) -> pd.DataFrame:
    nome = os.path.basename(caminho)
    log_fn(f"[Posicao] Lendo: {nome}")
    df = pd.read_csv(caminho, sep=SEPARADOR_CSV, encoding=ENCODING_CSV,
                     dtype=str, header=0, on_bad_lines="skip")
    total_lidas = len(df)
    df.columns = [c.strip() for c in df.columns]

    if "Subtotal.1" not in df.columns:
        log_fn(f"  [AVISO] '{nome}' nao possui coluna 'Subtotal.1' — ignorado.")
        return pd.DataFrame()

    mascara = df["Subtotal.1"].apply(lambda v: str(v).strip() == "0" if pd.notna(v) else False)
    df = df[mascara].copy()
    removidas = total_lidas - len(df)
    log_fn(f"  {len(df)} registros validos  |  {removidas} linhas removidas")

    for col in COLUNAS_ESPERADAS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUNAS_ESPERADAS].copy()
    df = trocar_pontos_virgulas(df)
    return df


def executar(pasta, log_fn, on_done):
    todos_csvs = sorted(glob.glob(os.path.join(pasta, "*.csv")))

    if not todos_csvs:
        log_fn("[ERRO] Nenhum arquivo .csv encontrado nesta pasta.")
        on_done(False)
        return

    basico_csvs  = [f for f in todos_csvs if eh_produto_basico(f)]
    posicao_csvs = [f for f in todos_csvs if not eh_produto_basico(f)
                    and os.path.basename(f).lower() != ARQUIVO_SAIDA_POSICAO.lower()]

    log_fn(f"{len(todos_csvs)} arquivo(s) CSV encontrado(s):")
    for f in todos_csvs:
        tipo = "Produto Basico" if eh_produto_basico(f) else "Posicao Financeira"
        log_fn(f"  [{tipo}] {os.path.basename(f)}")
    log_fn("")

    erros = []

    # ── Produto Básico ─────────────────────────────────────────────────────────
    if basico_csvs:
        log_fn("─── Produto Basico ───────────────────────────────")
        for caminho in basico_csvs:
            try:
                processar_produto_basico(caminho, log_fn)
            except Exception as e:
                log_fn(f"  [ERRO] {os.path.basename(caminho)}: {e}")
                erros.append(caminho)
        log_fn("")
    else:
        log_fn("[AVISO] Nenhum 'Relatorio de Produto Basico' encontrado.")
        log_fn("")

    # ── Posição Financeira ─────────────────────────────────────────────────────
    if posicao_csvs:
        log_fn("─── Posicao Financeira ───────────────────────────")
        frames = []
        for caminho in posicao_csvs:
            try:
                df = processar_posicao(caminho, log_fn)
                if not df.empty:
                    frames.append(df)
            except Exception as e:
                log_fn(f"  [ERRO] {os.path.basename(caminho)}: {e}")
                erros.append(caminho)

        if frames:
            log_fn("")
            log_fn("Unindo e ordenando por Filial ...")
            df_final = pd.concat(frames, ignore_index=True)
            df_final = df_final.sort_values("Filial").reset_index(drop=True)
            saida = os.path.join(pasta, ARQUIVO_SAIDA_POSICAO)
            df_final.to_csv(saida, sep=SEPARADOR_CSV, encoding=ENCODING_CSV, index=False)
            log_fn(f"  {len(df_final)} registros salvos em: {ARQUIVO_SAIDA_POSICAO}")

            for caminho in posicao_csvs:
                if os.path.basename(caminho).lower() != ARQUIVO_SAIDA_POSICAO.lower():
                    try:
                        os.remove(caminho)
                        log_fn(f"  Apagado: {os.path.basename(caminho)}")
                    except Exception as e:
                        log_fn(f"  [AVISO] Nao foi possivel apagar {os.path.basename(caminho)}: {e}")
        else:
            log_fn("[ERRO] Nenhum dado valido nos arquivos de posicao.")
            erros.append("posicao")
        log_fn("")
    else:
        log_fn("[AVISO] Nenhum arquivo de posicao financeira bruto encontrado.")
        log_fn("")

    log_fn("=" * 48)
    if erros:
        log_fn(f"  CONCLUIDO COM {len(erros)} ERRO(S). Verifique acima.")
    else:
        log_fn("  TUDO GERADO COM SUCESSO!")
    log_fn("=" * 48)
    on_done(len(erros) == 0)


def tem_brutos_novos(pasta: str) -> bool:
    csvs = glob.glob(os.path.join(pasta, "*.csv"))
    return any(
        not eh_produto_basico(f) and
        os.path.basename(f).lower() != ARQUIVO_SAIDA_POSICAO.lower()
        for f in csvs
    )
