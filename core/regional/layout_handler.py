import os
import pandas as pd
import re

def processar_e_padronizar_layout(caminho_completo):
    print("\n\033[1;34m[PMQA :: REGIONAL::LAYOUT]\033[0m Analisando estrutura semântica da matriz...")
    
    arquivo_alvo = os.path.basename(caminho_completo)
    
    if arquivo_alvo.endswith('.xlsx') or arquivo_alvo.endswith('.xls'):
        df_bruto = pd.read_excel(caminho_completo)
    else:
        codificacao = 'utf-8'
        try:
            with open(caminho_completo, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
        except UnicodeDecodeError:
            codificacao = 'latin1'
            with open(caminho_completo, 'r', encoding='latin1') as f:
                linhas = f.readlines()
            
        separador = ';' if any(';' in linha for linha in linhas[:5]) else ','
        radicais_territorio = ['mesorreg', 'municip', 'uf', 'localid', 'territor', 'regia', 'regiã', 'codigo', 'código']
        
        linha_cabecalho_idx = 0
        for idx, linha in enumerate(linhas):
            primeira_celula = linha.split(separador)[0].strip().lower()
            if any(radical in primeira_celula for radical in radicais_territorio):
                linha_cabecalho_idx = idx
                break
                
        linhas_validas = linhas[linha_cabecalho_idx:]
        caminho_temporario = caminho_completo + '.tmp'
        with open(caminho_temporario, 'w', encoding=codificacao) as f:
            f.writelines(linhas_validas)
            
        df_bruto = pd.read_csv(caminho_temporario, sep=separador, encoding=codificacao)
        if os.path.exists(caminho_temporario):
            os.remove(caminho_temporario)

    # 1. Mapeamento dos nomes dos setores antes da limpeza numérica
    mapeamento_setores = {}
    novas_colunas = []
    for i, c in enumerate(df_bruto.columns):
        c_str = str(c).strip()
        if i == 0:
            novas_colunas.append(c_str)
        else:
            num_setor = re.findall(r'^\d+', c_str)
            if num_setor:
                mapeamento_setores[num_setor[0]] = c_str
                novas_colunas.append(num_setor[0])
            else:
                novas_colunas.append(c_str)
    df_bruto.columns = novas_colunas

    col_territorio = df_bruto.columns[0]

    # 2. Passar o rodo definitivo em linhas fantasmas e metadados duplicados
    padrao_remover = 'Seleções|SeleÃ§Ãµes|Variável|VariÃ¡vel|{ñ class}|{Ã± class}|Critério|CritÃ©rio|Total|Ano|Vínculo|VÃnculo|IBGE Setor|Coluna|mesorreg'
    
    df_bruto = df_bruto[
        df_bruto[col_territorio].notna() & 
        (df_bruto[col_territorio].astype(str).str.strip() != '') &
        (~df_bruto[col_territorio].astype(str).str.contains(padrao_remover, case=False, na=False))
    ].copy()

    setores_potenciais = [c for c in df_bruto.columns if c != col_territorio and str(c).upper() != 'TOTAL']
    
    for col in setores_potenciais:
        df_bruto[col] = df_bruto[col].astype(str).str.replace('.', '', regex=False)
        df_bruto[col] = df_bruto[col].str.replace(',', '.', regex=False)
        df_bruto[col] = pd.to_numeric(df_bruto[col], errors='coerce').fillna(0.0)

    colunas_numericas = df_bruto.select_dtypes(include=['float64', 'int64']).columns.tolist()
    if col_territorio in colunas_numericas: 
        colunas_numericas.remove(col_territorio)

    if len(colunas_numericas) > 1:
        print("\033[1;32m[PMQA :: DETECT]\033[0m Padrão 'Wide Matrix' identificado. Executando empilhamento...")
        for t in ['Total', 'TOTAL', 'total']:
            if t in colunas_numericas: colunas_numericas.remove(t)
            if t in df_bruto.columns: df_bruto.drop(columns=[t], inplace=True)
        
        df_trabalho = pd.melt(
            df_bruto, id_vars=[col_territorio], value_vars=colunas_numericas,
            var_name='Setor', value_name='Empregos'
        )
        col_setor, col_variavel = 'Setor', 'Empregos'
    else:
        print("\033[1;32m[PMQA :: DETECT]\033[0m Padrão 'Long Table' identificado. Mapeando colunas...")
        df_trabalho = df_bruto.copy()
        col_variavel = colunas_numericas[0] if colunas_numericas else df_trabalho.columns[-1]
        colunas_texto = [c for c in df_trabalho.columns if c != col_variavel]
        col_territorio = colunas_texto[0]
        col_setor = colunas_texto[1] if len(colunas_texto) > 1 else colunas_texto[0]

    df_trabalho[col_variavel] = pd.to_numeric(df_trabalho[col_variavel], errors='coerce').fillna(0.0)
    
    # Devolve o descritivo completo para a coluna de setores antes do retorno
    df_trabalho[col_setor] = df_trabalho[col_setor].astype(str).map(mapeamento_setores).fillna(df_trabalho[col_setor])
    
    # Retorna uma lista única de regiões encontradas para alimentar a sua tela do Front-end
    regioes_detectadas = sorted(df_trabalho[col_territorio].unique().tolist())
    
    return df_trabalho, col_territorio, col_setor, col_variavel, regioes_detectadas