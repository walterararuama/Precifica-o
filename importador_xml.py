import xml.etree.ElementTree as ET
import sqlite3
import difflib
import unicodedata
import re
from datetime import datetime

_NS = 'http://www.portalfiscal.inf.br/nfe'
_TAG = lambda t: f'{{{_NS}}}{t}'

# ─────────────────────────────────────────────
# PARSER XML NF-e
# ─────────────────────────────────────────────

def ler_xml_nfe(caminho_xml):
    tree = ET.parse(caminho_xml)
    raiz = tree.getroot()

    # Localiza infNFe independente do nó raiz (nfeProc ou NFe)
    infNFe = raiz.find('.//' + _TAG('infNFe'))
    if infNFe is None:
        raise ValueError("Arquivo XML inválido: elemento infNFe não encontrado.")

    def txt(elemento, *tags):
        for t in tags:
            el = elemento.find('.//' + _TAG(t))
            if el is not None and el.text:
                return el.text.strip()
        return ''

    def num(elemento, *tags):
        v = txt(elemento, *tags)
        try: return float(v.replace(',', '.'))
        except: return 0.0

    # Cabeçalho
    ide   = infNFe.find(_TAG('ide'))
    emit  = infNFe.find(_TAG('emit'))
    total = infNFe.find(_TAG('total'))
    transp = infNFe.find(_TAG('transp'))

    cnpj_emit  = txt(emit, 'CNPJ')
    nome_emit  = txt(emit, 'xNome')
    num_nf     = txt(ide, 'nNF')

    # Data de emissão: pode ser dhEmi (com hora) ou dEmi
    raw_data = txt(ide, 'dhEmi', 'dEmi')
    try:
        if 'T' in raw_data:
            dt_emissao = datetime.fromisoformat(raw_data[:19]).strftime('%d/%m/%Y')
        else:
            dt_emissao = datetime.strptime(raw_data[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
    except:
        dt_emissao = raw_data[:10]

    # Tipo de frete
    mod_frete_raw = txt(transp, 'modFrete') if transp is not None else '9'
    _mapa_frete = {'0': 'CIF', '1': 'FOB', '2': 'TERCEIRIZADO',
                   '3': 'CIF', '4': 'FOB', '9': 'TERCEIRIZADO'}
    mod_frete = _mapa_frete.get(mod_frete_raw, 'TERCEIRIZADO')

    val_total_nf = num(total, 'vNF') if total is not None else 0.0

    # Itens
    itens = []
    for det in infNFe.findall(_TAG('det')):
        prod    = det.find(_TAG('prod'))
        imposto = det.find(_TAG('imposto'))
        if prod is None:
            continue

        ean = txt(prod, 'cEAN')
        if ean.upper() in ('SEM GTIN', 'SEMGTIN', ''):
            ean = ''

        ipi_perc = 0.0
        if imposto is not None:
            ipi_trib = imposto.find('.//' + _TAG('IPITrib'))
            if ipi_trib is not None:
                ipi_perc = num(ipi_trib, 'pIPI')

        itens.append({
            'cod_nf':      txt(prod, 'cProd'),
            'ean_nf':      ean,
            'descricao_nf': txt(prod, 'xProd'),
            'qtd':         num(prod, 'qCom'),
            'val_unit':    num(prod, 'vUnCom'),
            'val_total':   num(prod, 'vProd'),
            'ipi_perc':    ipi_perc,
        })

    return {
        'cnpj_fornecedor': cnpj_emit,
        'nome_fornecedor': nome_emit,
        'num_nf':          num_nf,
        'dt_emissao':      dt_emissao,
        'mod_frete':       mod_frete,
        'val_total':       val_total_nf,
        'itens':           itens,
    }


# ─────────────────────────────────────────────
# FUNÇÕES DB — TABELA de_para_produtos
# ─────────────────────────────────────────────

def buscar_de_para_exato(db_path, cnpj, cod_nf, ean_nf):
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            codigos = list({c for c in [cod_nf, ean_nf] if c})
            if not codigos:
                return None
            placeholders = ','.join('?' * len(codigos))
            row = cur.execute(
                f"SELECT * FROM de_para_produtos WHERE cnpj_fornecedor=? AND codigo_nf IN ({placeholders}) LIMIT 1",
                [cnpj] + codigos
            ).fetchone()
            return dict(row) if row else None
    except Exception:
        return None


def salvar_de_para(db_path, cnpj, cod_nf, desc_nf, cod_fdc, nome_fdc, usuario=''):
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            cur = conn.cursor()
            existente = cur.execute(
                "SELECT id FROM de_para_produtos WHERE cnpj_fornecedor=? AND codigo_nf=?",
                (cnpj, cod_nf)
            ).fetchone()
            if existente:
                cur.execute(
                    "UPDATE de_para_produtos SET codigo_fdc=?, nome_fdc=?, confirmado_por=?, data_criacao=? WHERE id=?",
                    (cod_fdc, nome_fdc, usuario, datetime.now().strftime('%d/%m/%Y %H:%M'), existente[0])
                )
            else:
                cur.execute(
                    """INSERT INTO de_para_produtos
                       (cnpj_fornecedor, codigo_nf, descricao_nf, codigo_fdc, nome_fdc, confirmado_por, data_criacao, total_usos)
                       VALUES (?,?,?,?,?,?,?,0)""",
                    (cnpj, cod_nf, desc_nf, cod_fdc, nome_fdc, usuario, datetime.now().strftime('%d/%m/%Y %H:%M'))
                )
            conn.commit()
    except Exception:
        pass


def incrementar_uso_de_para(db_path, id_registro):
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            conn.execute("UPDATE de_para_produtos SET total_usos=total_usos+1 WHERE id=?", (id_registro,))
            conn.commit()
    except Exception:
        pass


def listar_de_para(db_path):
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute(
                "SELECT * FROM de_para_produtos ORDER BY cnpj_fornecedor, codigo_nf"
            ).fetchall()]
    except Exception:
        return []


def deletar_de_para(db_path, id_registro):
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            conn.execute("DELETE FROM de_para_produtos WHERE id=?", (id_registro,))
            conn.commit()
    except Exception:
        pass


# ─────────────────────────────────────────────
# MOTOR DE CRUZAMENTO
# ─────────────────────────────────────────────

def _normalizar(texto):
    s = unicodedata.normalize('NFKD', str(texto).upper())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^A-Z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def cruzar_produtos(itens_nf, cache_fdc, db_path, cnpj_fornecedor):
    df = cache_fdc.get('basico')
    resultados = []

    # Monta lista de (cod_str, nome_str) para busca fuzzy — feito uma vez
    fdc_lista = []
    if df is not None and not df.empty and '_cod_str' in df.columns and '_nome_str' in df.columns:
        fdc_lista = list(zip(df['_cod_str'].tolist(), df['_nome_str'].tolist()))
    fdc_nomes_norm = [(_normalizar(n), c, n) for c, n in fdc_lista]

    for item in itens_nf:
        cod_nf = item['cod_nf']
        ean_nf = item['ean_nf']
        desc   = item['descricao_nf']

        resultado = dict(item)
        resultado.update({
            'cod_fdc_sugerido':  None,
            'nome_fdc_sugerido': None,
            'sugestoes':         [],
            'confirmado':        False,
            'status':            'NAO_ENCONTRADO',
            'de_para_id':        None,
        })

        # ── ETAPA 1: De-Para exato ───────────────────────────────
        dp = buscar_de_para_exato(db_path, cnpj_fornecedor, cod_nf, ean_nf)
        if dp:
            resultado['cod_fdc_sugerido']  = dp['codigo_fdc']
            resultado['nome_fdc_sugerido'] = dp['nome_fdc']
            resultado['confirmado']        = True
            resultado['status']            = 'CONFIRMADO'
            resultado['de_para_id']        = dp['id']
            incrementar_uso_de_para(db_path, dp['id'])
            resultados.append(resultado)
            continue

        # ── ETAPA 2: EAN ou código direto no FDC ────────────────
        if fdc_lista:
            for busca in [ean_nf, cod_nf]:
                if not busca:
                    continue
                match = df[df['_cod_str'] == busca] if '_cod_str' in df.columns else None
                if match is not None and not match.empty:
                    resultado['cod_fdc_sugerido']  = match.iloc[0]['_cod_str']
                    resultado['nome_fdc_sugerido'] = match.iloc[0]['_nome_str']
                    resultado['confirmado']        = True
                    resultado['status']            = 'EAN_DIRETO'
                    break

        if resultado['confirmado']:
            resultados.append(resultado)
            continue

        # ── ETAPA 3: Fuzzy na descrição ─────────────────────────
        if fdc_nomes_norm:
            desc_norm = _normalizar(desc)
            scored = []
            for nome_norm, cod, nome_orig in fdc_nomes_norm:
                score = difflib.SequenceMatcher(None, desc_norm, nome_norm).ratio()
                if score >= 0.35:
                    scored.append({'codigo': cod, 'nome': nome_orig, 'score': score, 'origem': 'fuzzy'})

            scored.sort(key=lambda x: x['score'], reverse=True)
            top5 = scored[:5]
            resultado['sugestoes'] = top5

            if top5 and top5[0]['score'] >= 0.60:
                resultado['cod_fdc_sugerido']  = top5[0]['codigo']
                resultado['nome_fdc_sugerido'] = top5[0]['nome']
                resultado['status'] = 'SUGESTAO'
            else:
                resultado['status'] = 'NAO_ENCONTRADO'

        resultados.append(resultado)

    return resultados
