import os
import json
import pandas as pd
from utils.arquivos import DIR_OUTPUTS, RAIZ_PROJETO

def limpar_mascara_financeira(serie):
    if serie.dtype in ['float64', 'int64']:
        return serie.fillna(0.0)
    s = serie.astype(str).str.replace(' ', '').str.strip()
    s = s.str.replace('$', '', regex=False)
    if s.str.contains(r'\.').any() and s.str.contains(',').any():
        s = s.str.replace(',', '', regex=False)
    elif s.str.contains(',').any() and not s.str.contains(r'\.').any():
        s = s.str.replace(',', '.', regex=False)
    return pd.to_numeric(s, errors='coerce').fillna(0.0)

def executar_calculo_deflacionamento():
    print("\n\033[1;34m[PMQA :: CALCULADORA]\033[0m Iniciando processamento vetorial de valores reais...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_config = os.path.join(base_dir, '..', 'metadata', 'orcamento', 'mapeamento.json')
    if not os.path.exists(caminho_config):
        print("\033[1;31m[ERRO :: CONFIG]\033[0m Metadados 'mapeamento.json' não encontrados.")
        raise FileNotFoundError()

    with open(caminho_config, 'r', encoding='utf-8') as f:
        config_usuario = json.load(f)

    col_ano = config_usuario['coluna_ano']
    colunas_financeiras = config_usuario['colunas_financeiras']

    caminho_base = os.path.join(DIR_OUTPUTS, 'base_unificada_bruta.csv')
    caminho_fatores = os.path.join(DIR_OUTPUTS, 'fatores_calculados.csv')

    if not os.path.exists(caminho_base) or not os.path.exists(caminho_fatores):
        print("\033[1;31m[ERRO :: INTEGRIDADE]\033[0m Matrizes base ou fatores ausentes no diretório.")
        raise FileNotFoundError()

    print("\033[36m-> [LOAD]\033[0m Alocando matrizes estruturadas na memória RAM...")
    base_bruta = pd.read_csv(caminho_base, sep=';', encoding='cp1252', skiprows=1, low_memory=False)

    try:
        fatores = pd.read_csv(caminho_fatores, sep=';', encoding='cp1252', skiprows=1, names=['ano', 'fator_deflator'])
        fatores = fatores[pd.to_numeric(fatores['ano'], errors='coerce').notna()].copy()
    except Exception:
        fatores = pd.read_csv(caminho_fatores, sep=',', encoding='cp1252', skiprows=1, names=['ano', 'fator_deflator'])
        fatores = fatores[pd.to_numeric(fatores['ano'], errors='coerce').notna()].copy()

    base_bruta[col_ano] = pd.to_numeric(base_bruta[col_ano], errors='coerce')
    fatores['ano'] = pd.to_numeric(fatores['ano'], errors='coerce').astype(int)

    print(f"\033[36m-> [MERGE]\033[0m Mesclando tabelas via chave cronológica: '[{col_ano}]'")
    base_real = pd.merge(base_bruta, fatores, left_on=col_ano, right_on='ano', how='left')
    base_real['fator_deflator'] = pd.to_numeric(base_real['fator_deflator'], errors='coerce').fillna(1.0)

    if col_ano != 'ano' and 'ano' in base_real.columns:
        base_real = base_real.drop(columns=['ano'])

    for col in colunas_financeiras:
        if col in base_real.columns:
            print(f"   \033[1;30m[MATH]\033[0m Corrigindo monetariamente a coluna: '{col}'")
            base_real[col] = limpar_mascara_financeira(base_real[col])
            base_real[f"{col}_real"] = base_real[col] * base_real['fator_deflator']

    if 'fator_deflator' in base_real.columns:
        base_real = base_real.drop(columns=['fator_deflator'])

    for col in base_real.columns:
        if col in colunas_financeiras or col.endswith('_real'):
            base_real[col] = pd.to_numeric(base_real[col], errors='coerce').round(2).fillna(0.0)

    colunas_lado_a_lado = []
    for col in base_bruta.columns:
        colunas_lado_a_lado.append(col)
        col_real = f"{col}_real"
        if col_real in base_real.columns:
            colunas_lado_a_lado.append(col_real)

    colunas_apenas_reais = []
    for col in base_bruta.columns:
        if col in colunas_financeiras:
            col_real = f"{col}_real"
            if col_real in base_real.columns:
                colunas_apenas_reais.append(col_real)
        else:
            colunas_apenas_reais.append(col)

    caminho_lado_a_lado = os.path.join(DIR_OUTPUTS, 'orcamento_valores_deflacionados_lado_a_lado.csv')
    caminho_puro = os.path.join(DIR_OUTPUTS, 'orcamento_valores_deflacionados_puro.csv')

    with open(caminho_lado_a_lado, 'w', encoding='cp1252', errors='replace', newline='') as f:
        f.write("sep=;\n")
        base_real[colunas_lado_a_lado].to_csv(f, index=False, sep=';')

    with open(caminho_puro, 'w', encoding='cp1252', errors='replace', newline='') as f:
        f.write("sep=;\n")
        base_real[colunas_apenas_reais].to_csv(f, index=False, sep=';')

    print("\033[1;32m[SUCESSO]\033[0m Matrizes financeiras deflacionadas geradas com precisão.")
    return {"status": "sucesso"}