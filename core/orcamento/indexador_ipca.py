import os
import pandas as pd
from utils.arquivos import DIR_PARAMETROS, DIR_OUTPUTS

def executar_indexacao_precos(ano_base_usuario=None):
    print("\n\033[1;34m[PMQA :: INDEXADOR]\033[0m Inicializando análise da série histórica inflacionária...")
    
    arquivos = os.listdir(DIR_PARAMETROS)
    arquivo_ipca = [f for f in arquivos if 'ipeadata' in f.lower() and (f.endswith('.csv') or f.endswith('.txt') or f.endswith('.xls') or f.endswith('.xlsx'))]

    if not arquivo_ipca:
        print("\033[1;31m[ERRO :: PARAM]\033[0m Matriz indexadora do Ipeadata não localizada em 'parametros'.")
        raise FileNotFoundError()

    nome_arquivo = arquivo_ipca[0]
    caminho_ipca = os.path.join(DIR_PARAMETROS, nome_arquivo)
    print(f"\033[1;32m[PMQA :: DETECT]\033[0m Série IPCA identificada com sucesso: '{nome_arquivo}'")

    if nome_arquivo.endswith('.xls') or nome_arquivo.endswith('.xlsx'):
        df_ipca = pd.read_excel(caminho_ipca, skiprows=0)
    else:
        # Detecta dinamicamente se o CSV do Ipeadata é versão BR (;) ou EN (,)
        with open(caminho_ipca, 'rb') as f:
            amostra_bytes = f.read(1024)
        separador = ';' if amostra_bytes.count(b';') > amostra_bytes.count(b',') else ','
        
        df_ipca = pd.read_csv(caminho_ipca, sep=separador, skiprows=0, encoding='utf-8')

    # Garante que vamos pegar as duas primeiras colunas independentemente do nome do cabeçalho
    df_ipca = df_ipca.iloc[:, [0, 1]]
    df_ipca.columns = ['data', 'indice']
    
    df_ipca['data'] = df_ipca['data'].astype(str).str.strip()

    # Se o separador for BR, o Pandas lê o índice como texto por causa da vírgula decimal. Tratamos aqui:
    if df_ipca['indice'].dtype == object:
        df_ipca['indice'] = df_ipca['indice'].astype(str).str.replace(' ', '').str.replace(',', '.', regex=False)

    df_dezembros = df_ipca[df_ipca['data'].str.endswith('.12') | df_ipca['data'].str.endswith('/12')].copy()
    
    # Suporta tanto formato "2025.12" quanto "12/2025" ou "2025/12"
    def extrair_ano(data_str):
        if '.' in data_str:
            return int(data_str.split('.')[0])
        elif '/' in data_str:
            partes = data_str.split('/')
            return int(partes[1]) if len(partes[0]) == 2 else int(partes[0])
        return int(data_str)

    df_dezembros['ano'] = df_dezembros['data'].apply(extrair_ano)
    df_dezembros['indice'] = pd.to_numeric(df_dezembros['indice'], errors='coerce')
    df_dezembros = df_dezembros.dropna(subset=['indice'])

    limite_superior = df_dezembros['ano'].max()

    if ano_base_usuario and str(ano_base_usuario).strip() != "":
        ano_base = int(ano_base_usuario)
    else:
        caminho_config_txt = os.path.join(DIR_PARAMETROS, 'config_ano_base.txt')
        if os.path.exists(caminho_config_txt):
            with open(caminho_config_txt, 'r', encoding='utf-8') as f:
                ano_base = int(f.read().strip())
        else:
            ano_base = limite_superior

    linha_alvo = df_dezembros[df_dezembros['ano'] == ano_base]
    if linha_alvo.empty:
        ano_base = limite_superior
        linha_alvo = df_dezembros[df_dezembros['ano'] == ano_base]
        print(f"\033[1;33m[WARN :: TIMELINE]\033[0m Ciclo temporal ausente. Forçando teto recente: {ano_base}")

    indice_referencia = linha_alvo['indice'].values[0]
    print(f"\033[1;32m[PMQA :: LOCK]\033[0m Indexador travado no Ano-Base: {ano_base} | Índice: {indice_referencia}")

    df_dezembros['fator_deflator'] = indice_referencia / df_dezembros['indice']
    tabela_fatores = df_dezembros[['ano', 'fator_deflator']].copy()

    caminho_fatores_saida = os.path.join(DIR_OUTPUTS, 'fatores_calculados.csv')
    with open(caminho_fatores_saida, 'w', encoding='cp1252', errors='replace', newline='') as f:
        f.write("sep=;\n")
        tabela_fatores.to_csv(f, index=False, sep=';')

    print(f"\033[1;32m[SUCESSO]\033[0m Tabela vetorial de deflação persistida em: '{caminho_fatores_saida}'")
    return {"status": "sucesso", "ano_base_aplicado": ano_base}