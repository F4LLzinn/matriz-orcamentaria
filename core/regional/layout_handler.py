import os
import re
import pandas as pd

def detectar_layout(caminho_arquivo, resolvedor_ibge=None):
    """
    Carrega planilhas regionais brutas da RAIS/MTE de forma 100% agnóstica.
    Varre o topo do arquivo para localizar onde o cabeçalho real começa,
    evitando que o Pandas mutile colunas por causa de títulos acessórios.
    """
    encoding_alvo = 'utf-8'
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as f:
            amostra_linhas = [f.readline() for _ in range(15)]
    except Exception:
        with open(caminho_arquivo, 'r', encoding='latin-1', errors='ignore') as f:
            amostra_linhas = [f.readline() for _ in range(15)]
            encoding_alvo = 'latin-1'

    total_pv = sum(l.count(';') for l in amostra_linhas)
    total_v = sum(l.count(',') for l in amostra_linhas)
    sep_detectado = ';' if total_pv >= total_v else ','

    max_colunas = 0
    linha_header_idx = 0
    for idx, l in enumerate(amostra_linhas):
        num_cols = len(l.split(sep_detectado))
        if num_cols > max_colunas:
            max_colunas = num_cols
            linha_header_idx = idx

    print(f"\033[1;34m[PMQA :: PARSER]\033[0m Separador: '{sep_detectado}' | Header Real na Linha: {linha_header_idx}")

    try:
        df = pd.read_csv(caminho_arquivo, sep=sep_detectado, skiprows=linha_header_idx, encoding='utf-8')
    except (UnicodeDecodeError, Exception):
        # Se falhar de verdade no UTF-8, aí sim recorre ao padrão antigo do Excel
        df = pd.read_csv(caminho_arquivo, sep=sep_detectado, skiprows=linha_header_idx, encoding='latin-1')

    col_territorio = df.columns[0]
    col_setores = [c for c in df.columns[1:] if c != 'Total' and not str(c).startswith('Unnamed')]
    
    df = df[df[col_territorio].notna()].copy()
    df[col_territorio] = df[col_territorio].astype(str).str.strip()
    
    linhas_para_ignorar = ['variável', 'ano', 'vínculo', 'total', 'ibge setor', 'seleções vigentes']
    df = df[~df[col_territorio].str.lower().str.strip().isin(linhas_para_ignorar)].copy()

    for col in col_setores:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    
    df['Total'] = df[col_setores].sum(axis=1)

    df_longo = df.melt(
        id_vars=[col_territorio],
        value_vars=col_setores,
        var_name='Setor',
        value_name='Emprego'
    )

    macroregioes = {}
    localidades_unicas = df_longo[col_territorio].unique()
    
    if len(localidades_unicas) == 0:
        raise ValueError("Erro crítico: Nenhuma localidade sobrou após a filtragem de layout.")
        
    primeira_localidade = str(localidades_unicas[0]).strip()
    
    if re.match(r'^\d+', primeira_localidade):
        print("\033[1;32m[PMQA :: TERRITÓRIO]\033[0m Modo ID Ativado. Decodificando via prefixos do IBGE.")
        mapa_regioes_ibge = {'1': 'Norte', '2': 'Nordeste', '3': 'Sudeste', '4': 'Sul', '5': 'Centro-Oeste'}
        for loc in localidades_unicas:
            match_id = re.match(r'^\d+', str(loc).strip())
            if match_id:
                macroregioes[loc] = mapa_regioes_ibge.get(match_id.group(0)[0], 'Outros')
            else:
                macroregioes[loc] = 'Outros'

    elif resolvedor_ibge is not None:
        var_nome_normalizado = str(col_territorio).strip().lower()
        print(f"\033[1;32m[PMQA :: TERRITÓRIO]\033[0m Modo API/Cache Ativado para: '{col_territorio}'")
        
        if 'municip' in var_nome_normalizado:
            for loc in localidades_unicas:
                info = resolvedor_ibge.mapa_municipios.get(str(loc).strip().lower(), {})
                macroregioes[loc] = info.get('Macroregiao', 'Outros')
        else:
            for loc in localidades_unicas:
                macroregioes[loc] = resolvedor_ibge.mapa_mesorregioes.get(str(loc).strip().lower(), 'Outros')
    
    else:
        print("\033[1;33m[PMQA :: AVISO]\033[0m Resolvedor IBGE indisponível. Escopo amplo.")
        for loc in localidades_unicas: macroregioes[loc] = 'Todos'

    return df_longo, col_territorio, 'Setor', 'Emprego', macroregioes