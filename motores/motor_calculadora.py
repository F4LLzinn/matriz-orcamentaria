import os
import json
import pandas as pd

# 🌟 CORREÇÃO DE DIRETÓRIO: Garante que o script suba um nível para achar a raiz do projeto
PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
RAIZ_PROJETO = os.path.abspath(os.path.join(PASTA_ATUAL, '..'))

# Aponta para as pastas corretas localizadas na raiz
DIR_OUTPUTS = os.path.join(RAIZ_PROJETO, 'outputs_processados')
CAMINHO_CONFIG = os.path.join(RAIZ_PROJETO, 'config_mapeamento.json')

print("[SYSTEM::INIT] Ativando calculadora vetorial adaptável...")

if not os.path.exists(CAMINHO_CONFIG):
    print("[CONFIG::FAIL] Quebra de pipeline: 'config_mapeamento.json' não encontrado.")
    exit()

with open(CAMINHO_CONFIG, 'r', encoding='utf-8') as f:
    config_usuario = json.load(f)

col_ano_usuario = config_usuario['coluna_ano']
colunas_financeiras_usuario = config_usuario['colunas_financeiras']

caminho_base = os.path.join(DIR_OUTPUTS, 'base_unificada_bruta.csv')
caminho_fatores = os.path.join(DIR_OUTPUTS, 'fatores_calculados.csv')

if not os.path.exists(caminho_base) or not os.path.exists(caminho_fatores):
    print("[DATA::FAIL] Erro de integridade física: Arquivos base ou fatores ausentes.")
    exit()

print("[DATA::LOAD] Carregando matrizes estruturadas para a memória ram...")
base_bruta = pd.read_csv(caminho_base, sep=';', encoding='cp1252', skiprows=1, low_memory=False)

try:
    fatores = pd.read_csv(caminho_fatores, sep=';', encoding='cp1252', skiprows=1, names=['ano', 'fator_deflator'])
    fatores = fatores[pd.to_numeric(fatores['ano'], errors='coerce').notna()].copy()
except Exception:
    fatores = pd.read_csv(caminho_fatores, sep=',', encoding='cp1252', skiprows=1, names=['ano', 'fator_deflator'])
    fatores = fatores[pd.to_numeric(fatores['ano'], errors='coerce').notna()].copy()

base_bruta[col_ano_usuario] = pd.to_numeric(base_bruta[col_ano_usuario], errors='coerce')
fatores['ano'] = pd.to_numeric(fatores['ano'], errors='coerce').astype(int)

print(f"[RELATION::MERGE] Mesclando tabelas via chave dinâmica: '[{col_ano_usuario}]'")
base_real = pd.merge(base_bruta, fatores, left_on=col_ano_usuario, right_on='ano', how='left')
base_real['fator_deflator'] = pd.to_numeric(base_real['fator_deflator'], errors='coerce').fillna(1.0)

if col_ano_usuario != 'ano' and 'ano' in base_real.columns:
    base_real = base_real.drop(columns=['ano'])

def limpar_moeda_universal(serie):
    if serie.dtype in ['float64', 'int64']:
        return serie.fillna(0.0)
    s = serie.astype(str).str.replace(' ', '').str.strip()
    s = s.str.replace('$', '', regex=False)
    if s.str.contains(r'\.').any() and s.str.contains(',').any():
        s = s.str.replace(',', '', regex=False)
    elif s.str.contains(',').any() and not s.str.contains(r'\.').any():
        s = s.str.replace(',', '.', regex=False)
    return pd.to_numeric(s, errors='coerce').fillna(0.0)

# Processamento aritmético das colunas
for col in colunas_financeiras_usuario:
    if col in base_real.columns:
        print(f"  --> [MATH::DEFLATE] Calculando valores reais na coluna: '{col}'")
        base_real[col] = limpar_moeda_universal(base_real[col])
        nova_coluna_real = f"{col}_real"
        base_real[nova_coluna_real] = base_real[col] * base_real['fator_deflator']

if 'fator_deflator' in base_real.columns:
    base_real = base_real.drop(columns=['fator_deflator'])

# ==============================================================================
# ✍️ PADRONIZAÇÃO REGIONAL PERMANENTE (FLOAT PADRÃO EN-US)
# ==============================================================================
print("\n[REGIONAL::MASK] Preservando padrão float EN-US (Ponto decimal) de alta precisão...")

# Força todas as colunas financeiras (brutas e reais) a serem floats puros arredondados em 2 casas
for col in base_real.columns:
    if col in colunas_financeiras_usuario or col.endswith('_real'):
        base_real[col] = pd.to_numeric(base_real[col], errors='coerce').round(2).fillna(0.0)

# ==============================================================================
# 🗂️ MONTAGEM DAS DUAS VISÕES REQUISITADAS
# ==============================================================================
print("\n🗂️ Separando os arquivos de acordo com as necessidades de entrega...")

# VISÃO 1: Lado a Lado (Para o seu Power BI)
colunas_lado_a_lado = []
for col in base_bruta.columns:
    colunas_lado_a_lado.append(col)
    col_real = f"{col}_real"
    if col_real in base_real.columns:
        colunas_lado_a_lado.append(col_real)

# VISÃO 2: Apenas Deflacionados (Para o Professor)
colunas_apenas_reais = []
for col in base_bruta.columns:
    if col in colunas_financeiras_usuario:
        col_real = f"{col}_real"
        if col_real in base_real.columns:
            colunas_apenas_reais.append(col_real)
    else:
        colunas_apenas_reais.append(col)

caminho_csv_lado_a_lado = os.path.join(DIR_OUTPUTS, 'orcamento_valores_deflacionados_lado_a_lado.csv')
caminho_csv_professor = os.path.join(DIR_OUTPUTS, 'orcamento_valores_deflacionados_puro.csv')

print("[DATA::EXPORT] Descarregando matrizes estruturadas finais no HD...")
with open(caminho_csv_lado_a_lado, 'w', encoding='cp1252', errors='replace', newline='') as f:
    f.write("sep=;\n")
    base_real[colunas_lado_a_lado].to_csv(f, index=False, sep=';')

with open(caminho_csv_professor, 'w', encoding='cp1252', errors='replace', newline='') as f:
    f.write("sep=;\n")
    base_real[colunas_apenas_reais].to_csv(f, index=False, sep=';')

print("[STATUS::SUCCESS] Operação concluída com 0 erros. Repositório local atualizado.")