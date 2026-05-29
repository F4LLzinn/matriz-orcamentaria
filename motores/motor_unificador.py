import os
import re
import json
import pandas as pd

# 🌟 CORREÇÃO DE DIRETÓRIO: Garante que o script suba um nível para achar a raiz do projeto
PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
RAIZ_PROJETO = os.path.abspath(os.path.join(PASTA_ATUAL, '..'))

# Aponta para as pastas corretas localizadas na raiz
DIR_INPUTS = os.path.join(RAIZ_PROJETO, 'inputs_orcamento')
DIR_OUTPUTS = os.path.join(RAIZ_PROJETO, 'outputs_processados') # Ajuste o nome se a pasta de saída do orçamento for outra

if not os.path.exists(DIR_OUTPUTS):
    os.makedirs(DIR_OUTPUTS)

print("[SYSTEM::INIT] Inicializando pipeline macro do unificador de matrizes...")

arquivos_orcamento = [
    arq for arq in os.listdir(DIR_INPUTS)
    if not arq.startswith('~$') and (arq.endswith('.xlsx') or arq.endswith('.csv'))
]

if not arquivos_orcamento:
    print("[DIR::FAIL] Nenhum arquivo de dados localizado na pasta 'inputs_orcamento'.")
    raise FileNotFoundError("Nenhum arquivo válido encontrado na pasta 'inputs_orcamento'.")

arquivos_orcamento.sort()

lista_df_anos = []
colunas_gabarito = []
colunas_financeiras_detectadas = []

def normalizar_cabecalho(texto):
    t = str(texto).lower().strip()
    t = re.sub(r'\(.*?\)', '', t).strip()
    termos_descartaveis = ['siafi', 'oficial', 'bruto', 'valor']
    for termo in termos_descartaveis:
        t = re.sub(r'\b' + termo + r'\b', '', t).strip()
    substituicoes = {
        'á': 'a', 'ã': 'a', 'â': 'a', 'é': 'e', 'ê': 'e',
        'í': 'i', 'ó': 'o', 'ô': 'o', 'ú': 'u', 'ç': 'c'
    }
    for original, sub in substituicoes.items():
        t = t.replace(original, sub)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def achar_linhas_pular_e_separador(caminho):
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

# Arquivo líder (gabarito)
arquivo_lider = arquivos_orcamento[0]
caminho_lider = os.path.join(DIR_INPUTS, arquivo_lider)
pular_lider, sep_lider = achar_linhas_pular_e_separador(caminho_lider)

print(f"[MATRIX::REF] Gabarito estrutural travado no arquivo líder: '{arquivo_lider}'")

if arquivo_lider.endswith('.xlsx'):
    df_lider = pd.read_excel(caminho_lider, skiprows=pular_lider)
else:
    df_lider = pd.read_csv(caminho_lider, sep=sep_lider, encoding='cp1252', skiprows=pular_lider)

colunas_gabarito = [str(c).strip() for c in df_lider.columns if not str(c).startswith('Unnamed:')]
df_lider.columns = [str(c).strip() for c in df_lider.columns]
df_lider = df_lider.loc[:, ~df_lider.columns.str.contains('^unnamed:')]

mapa_comparativo_lider = {normalizar_cabecalho(c): c for c in colunas_gabarito}

for col in colunas_gabarito:
    amostra = df_lider[col].dropna().head(10).astype(str).str.replace(' ', '')
    if df_lider[col].dtype in ['float64', 'int64'] or amostra.str.contains(r'[\$,\.]').any():
        if not any(a in col.lower() for a in ['ano', 'exerc', 'cod', 'id']):
            colunas_financeiras_detectadas.append(col.lower())

print(f"[MAP::SUCCESS] Varredura estrutural concluída. {len(colunas_gabarito)} campos mapeados no dicionário.")

# Loop de alinhamento
for arquivo in arquivos_orcamento:
    caminho_arquivo = os.path.join(DIR_INPUTS, arquivo)
    ano_detectado = re.search(r'(20\d{2})', arquivo)
    ano_final = int(ano_detectado.group(1)) if ano_detectado else 2025

    print(f"[ALIGN::EXEC] Higienizando e reindexando rótulos: '{arquivo}'")

    pular, sep = achar_linhas_pular_e_separador(caminho_arquivo)

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
        raiz_atual = normalizar_cabecalho(col_atual)
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

    print(f"  --> [ALIGN::OK] {len(df_ano)} linhas consolidadas para o período {ano_final}.")
    lista_df_anos.append(df_ano)

# Consolidação
if lista_df_anos:
    base_unificada = pd.concat(lista_df_anos, ignore_index=True)
    if 'ano' not in colunas_gabarito_minusculo:
        colunas_gabarito_minusculo.insert(1, 'ano')
    base_unificada = base_unificada.reindex(columns=colunas_gabarito_minusculo)

    caminho_saida = os.path.join(DIR_OUTPUTS, 'base_unificada_bruta.csv')
    with open(caminho_saida, 'w', encoding='cp1252', errors='replace', newline='') as f:
        f.write("sep=;\n")
        base_unificada.to_csv(f, index=False, sep=';')

    print(f"[MATRIX::SAVE] Matriz consolidada persistida com sucesso em '{caminho_saida}'.")

    caminho_config_json = os.path.join(RAIZ_PROJETO, 'config_mapeamento.json')
    config_automatico = {
        "coluna_ano": "ano",
        "colunas_financeiras": colunas_financeiras_detectadas
    }
    with open(caminho_config_json, 'w', encoding='utf-8') as f:
        json.dump(config_automatico, f, indent=2, ensure_ascii=False)

    print("[CONFIG::SAVE] Metadados gravados em 'config_mapeamento.json'. Unidade de unificação pronta.")