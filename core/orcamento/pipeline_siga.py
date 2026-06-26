import os
import re
import json
import pandas as pd
from utils.arquivos import DIR_INPUTS_ORCAMENTO, DIR_OUTPUTS, RAIZ_PROJETO

def normalizar_rotulo(texto):
    t = str(texto).lower().strip()
    t = re.sub(r'\(.*?\)', '', t).strip()
    for termo in ['siafi', 'oficial', 'bruto', 'valor']:
        t = re.sub(r'\b' + termo + r'\b', '', t).strip()
    substituicoes = {
        'á': 'a', 'ã': 'a', 'â': 'a', 'é': 'e', 'ê': 'e',
        'í': 'i', 'ó': 'o', 'ô': 'o', 'ú': 'u', 'ç': 'c'
    }
    for original, sub in substituicoes.items():
        t = t.replace(original, sub)
    return re.sub(r'\s+', ' ', t).strip()

def detectar_estrutura_arquivo(caminho):
    linhas_pular = 0
    sep_detectado = ';'
    if caminho.endswith('.xlsx'):
        df_teste = pd.read_excel(caminho, nrows=10, header=None)
    else:
        try:
            df_teste = pd.read_csv(caminho, sep=';', nrows=10, header=None)
        except Exception:
            df_teste = pd.read_csv(caminho, sep=',', encoding='latin1', nrows=10, header=None)
            sep_detectado = ','
    for i, linha in df_teste.iterrows():
        linha_str = " ".join([str(v).lower() for v in list(linha.values) if pd.notna(v)])
        if any(termo in linha_str for termo in ['funç', 'func', 'dota', 'universo', 'ano', 'cod', 'descr', 'pl']):
            linhas_pular = i
            break
    return linhas_pular, sep_detectado

def executar_unificacao_matrizes():
    print("\n\033[1;34m[PMQA :: ORÇAMENTO]\033[0m Inicializando pipeline de consolidação estrutural...")
    
    arquivos_orcamento = [
        arq for arq in os.listdir(DIR_INPUTS_ORCAMENTO)
        if not arq.startswith('~$') and (arq.endswith('.xlsx') or arq.endswith('.csv'))
    ]

    if not arquivos_orcamento:
        print("\033[1;31m[ERRO :: DATA]\033[0m Nenhuma matriz orçamentária localizada em 'inputs_orcamento'.")
        raise FileNotFoundError()

    arquivos_orcamento.sort()
    lista_df_anos = []
    colunas_financeiras_detectadas = []

    arquivo_lider = arquivos_orcamento[0]
    caminho_lider = os.path.join(DIR_INPUTS_ORCAMENTO, arquivo_lider)
    pular_lider, sep_lider = detectar_estrutura_arquivo(caminho_lider)

    print(f"\033[1;32m[PMQA :: REFERENCE]\033[0m Matriz de simetria travada no arquivo líder: '{arquivo_lider}'")

    if arquivo_lider.endswith('.xlsx'):
        df_lider = pd.read_excel(caminho_lider, skiprows=pular_lider)
    else:
        df_lider = pd.read_csv(caminho_lider, sep=sep_lider, encoding='cp1252', skiprows=pular_lider)

    colunas_gabarito = [str(c).strip() for c in df_lider.columns if not str(c).startswith('Unnamed:')]
    df_lider.columns = [str(c).strip() for c in df_lider.columns]
    df_lider = df_lider.loc[:, ~df_lider.columns.str.contains('^unnamed:')]

    mapa_comparativo_lider = {normalizar_rotulo(c): c for c in colunas_gabarito}

    for col in colunas_gabarito:
        amostra = df_lider[col].dropna().head(10).astype(str).str.replace(' ', '')
        if df_lider[col].dtype in ['float64', 'int64'] or amostra.str.contains(r'[\$,\.]').any():
            if not any(a in col.lower() for a in ['ano', 'exerc', 'cod', 'id']):
                colunas_financeiras_detectadas.append(col.lower())

    for arquivo in arquivos_orcamento:
        caminho_arquivo = os.path.join(DIR_INPUTS_ORCAMENTO, arquivo)
        ano_detectado = re.search(r'(20\d{2})', arquivo)
        ano_final = int(ano_detectado.group(1)) if ano_detectado else 2025

        print(f"  \033[36m-> [PROCESS]\033[0m Higienizando e normalizando registros: '{arquivo}'")
        pular, sep = detectar_estrutura_arquivo(caminho_arquivo)

        if arquivo.endswith('.xlsx'):
            df_ano = pd.read_excel(caminho_arquivo, skiprows=pular)
        else:
            try:
                df_ano = pd.read_csv(caminho_arquivo, sep=sep, encoding='cp1252', skiprows=pular)
            except Exception:
                df_ano = pd.read_csv(caminho_arquivo, sep=sep, encoding='utf-8', skiprows=pular)

        df_ano = df_ano.loc[:, ~df_ano.columns.str.contains('^unnamed:')]

        mapa_renomear_atual = {}
        for col_atual in df_ano.columns:
            raiz_atual = normalizar_rotulo(col_atual)
            if raiz_atual in mapa_comparativo_lider:
                mapa_renomear_atual[col_atual] = mapa_comparativo_lider[raiz_atual]

        df_ano = df_ano.rename(columns=mapa_renomear_atual)
        df_ano.columns = [str(c).strip().lower() for c in df_ano.columns]
        colunas_gabarito_minusculo = [c.lower() for c in colunas_gabarito]
        df_ano = df_ano.reindex(columns=colunas_gabarito_minusculo)
        df_ano['ano'] = ano_final

        for col in colunas_financeiras_detectadas:
            if col in df_ano.columns:
                if df_ano[col].dtype == object:
                    df_ano[col] = df_ano[col].astype(str).str.replace(' ', '').str.replace(',', '.', regex=False)
                df_ano[col] = pd.to_numeric(df_ano[col], errors='coerce').fillna(0.0)

        lista_df_anos.append(df_ano)

    if lista_df_anos:
        base_unificada = pd.concat(lista_df_anos, ignore_index=True)
        if 'ano' not in colunas_gabarito_minusculo:
            colunas_gabarito_minusculo.insert(1, 'ano')
        base_unificada = base_unificada.reindex(columns=colunas_gabarito_minusculo)

        caminho_saida = os.path.join(DIR_OUTPUTS, 'base_unificada_bruta.csv')
        with open(caminho_saida, 'w', encoding='cp1252', errors='replace', newline='') as f:
            f.write("sep=;\n")
            base_unificada.to_csv(f, index=False, sep=';')

        print(f"\033[1;32m[SUCESSO]\033[0m Matriz unificada persistida em: '{caminho_saida}'")

        caminho_config_json = os.path.join(RAIZ_PROJETO, 'config_mapeamento.json')
        config_automatico = {
            "coluna_ano": "ano",
            "colunas_financeiras": colunas_financeiras_detectadas
        }
        with open(caminho_config_json, 'w', encoding='utf-8') as f:
            json.dump(config_automatico, f, indent=2, ensure_ascii=False)

    return {"status": "sucesso", "colunas_financeiras": colunas_financeiras_detectadas}