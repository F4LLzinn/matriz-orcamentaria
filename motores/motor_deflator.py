import os
import pandas as pd

# 🌟 CORREÇÃO DE DIRETÓRIO: Garante que o script suba um nível para achar a raiz do projeto
PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
RAIZ_PROJETO = os.path.abspath(os.path.join(PASTA_ATUAL, '..'))

# Aponta para as pastas corretas localizadas na raiz
DIR_PARAMETROS = os.path.join(RAIZ_PROJETO, 'parametros')
DIR_OUTPUTS = os.path.join(RAIZ_PROJETO, 'outputs_processados')

for pasta in [DIR_PARAMETROS, DIR_OUTPUTS]:
    if not os.path.exists(pasta):
        os.makedirs(pasta)

print("[SYSTEM::INIT] Ativando motor extrator do índice de deflacionamento (IPCA)...")

# 1. Busca pelo arquivo do Ipeadata
arquivos = os.listdir(DIR_PARAMETROS)
arquivo_ipca = []

for f in arquivos:
    if 'ipeadata' in f.lower() and (f.endswith('.csv') or f.endswith('.txt') or f.endswith('.xls') or f.endswith('.xlsx')):
        arquivo_ipca.append(f)

if not arquivo_ipca:
    print("[DIR::FAIL] Falha de dependência: Série do Ipeadata não encontrada em 'parametros'.")
    exit()

nome_final_arquivo = arquivo_ipca[0]
caminho_ipca = os.path.join(DIR_PARAMETROS, nome_final_arquivo)
print(f"[DATA::DETECT] Matriz inflacionária identificada: '{nome_final_arquivo}'")

# 2. Leitura Dinâmica
if nome_final_arquivo.endswith('.xls') or nome_final_arquivo.endswith('.xlsx'):
    df_ipca = pd.read_excel(caminho_ipca, skiprows=0)
else:
    df_ipca = pd.read_csv(caminho_ipca, sep=',', skiprows=0)

df_ipca.columns = ['data', 'indice']
df_ipca['data'] = df_ipca['data'].astype(str).str.strip()

# 3. Filtragem Estrita (Isolar Dezembros)
df_dezembros = df_ipca[df_ipca['data'].str.endswith('.12')].copy()
df_dezembros['ano'] = df_dezembros['data'].str.split('.').str[0].astype(int)
df_dezembros['indice'] = pd.to_numeric(df_dezembros['indice'], errors='coerce')

ano_maximo_disponivel = df_dezembros['ano'].max()
ano_minimo_disponivel = df_dezembros['ano'].min()

caminho_config_ano = os.path.join(DIR_PARAMETROS, 'config_ano_base.txt')

# Verificação de parâmetros do ecossistema
if os.path.exists(caminho_config_ano):
    try:
        with open(caminho_config_ano, 'r', encoding='utf-8') as f:
            ANO_BASE = int(f.read().strip())
        print(f"[CONFIG::LOAD] Parâmetro de Ano-Base interceptado com sucesso: {ANO_BASE}")
    except Exception:
        ANO_BASE = ano_maximo_disponivel
        print(f"[CONFIG::WARN] Falha ao interceptar bilhete. Forçando teto recente: {ANO_BASE}")
else:
    try:
        entrada_usuario = input(f"[INPUT::PROMPT] Informe o Ano-Base para indexação ({ano_minimo_disponivel} a {ano_maximo_disponivel}): ").strip()
        ANO_BASE = int(entrada_usuario)
    except ValueError:
        ANO_BASE = ano_maximo_disponivel
        print(f"[CONFIG::WARN] Entrada inválida no terminal. Travando no limite superior: {ANO_BASE}")

linha_ano_base = df_dezembros[df_dezembros['ano'] == ANO_BASE]

if linha_ano_base.empty:
    ANO_BASE = ano_maximo_disponivel
    linha_ano_base = df_dezembros[df_dezembros['ano'] == ANO_BASE]
    print(f"[CONFIG::WARN] Ciclo temporal ausente na série. Ajustado para o máximo: {ANO_BASE}")

indice_base = linha_ano_base['indice'].values[0]
print(f"[DEFLATE::LOCK] Indexador travado no Ano-Base: {ANO_BASE} | Índice de referência: {indice_base}")

# 5. Cálculo do Fator Deflator
df_dezembros['fator_deflator'] = indice_base / df_dezembros['indice']
tabela_fatores = df_dezembros[['ano', 'fator_deflator']].copy()

caminho_fatores_saida = os.path.join(DIR_OUTPUTS, 'fatores_calculados.csv')
with open(caminho_fatores_saida, 'w', encoding='cp1252', errors='replace', newline='') as f:
    f.write("sep=;\n")
    tabela_fatores.to_csv(f, index=False, sep=';')

print(f"[MATRIX::SAVE] Tabela vetorial de fatores persistida em '{caminho_fatores_saida}'.")