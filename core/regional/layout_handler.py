import os
import pandas as pd

def processar_e_padronizar_layout(caminho_completo):
    print("\n\033[1;34m[PMQA :: REGIONAL::LAYOUT]\033[0m Analisando estrutura semântica da matriz...")
    
    arquivo_alvo = os.path.basename(caminho_completo)
    
    if arquivo_alvo.endswith('.xlsx') or arquivo_alvo.endswith('.xls'):
        df_bruto = pd.read_excel(caminho_completo)
    else:
        with open(caminho_completo, 'rb') as f:
            amostra_bytes = f.read(2048)
        
        separador = ';' if amostra_bytes.count(b';') > amostra_bytes.count(b',') else ','
        codificacao = 'utf-8'
        try:
            amostra_bytes.decode('utf-8')
        except UnicodeDecodeError:
            codificacao = 'cp1252'
            
        df_bruto = pd.read_csv(caminho_completo, sep=separador, encoding=codificacao)

    df_bruto.columns = [str(c).strip() for c in df_bruto.columns]
    primeira_col = df_bruto.columns[0]
    padrao_remover = 'Seleções|SeleÃ§Ãµes|Variável|VariÃ¡vel|{ñ class}|{Ã± class}|Critério|CritÃ©rio|Total|Ano|Vínculo|VÃnculo'

    df_bruto = df_bruto[
        df_bruto[primeira_col].notna() & 
        (~df_bruto[primeira_col].astype(str).str.contains(padrao_remover, case=False, na=False))
    ].copy()

    colunas_numericas = df_bruto.select_dtypes(include=['float64', 'int64']).columns.tolist()
    if 'Total' in colunas_numericas: colunas_numericas.remove('Total')

    if len(colunas_numericas) > 1:
        print("\033[1;32m[PMQA :: DETECT]\033[0m Padrão 'Wide Matrix' (Matriz Cruzada) identificado. Executando empilhamento...")
        if 'Total' in df_bruto.columns: df_bruto.drop(columns=['Total'], inplace=True)
        if '{ñ class}' in df_bruto.columns: df_bruto.drop(columns=['{ñ class}'], inplace=True)
        if '{Ã± class}' in df_bruto.columns: df_bruto.drop(columns=['{Ã± class}'], inplace=True)
        
        col_territorio = df_bruto.columns[0]
        setores_alvo = [c for c in df_bruto.columns if c != col_territorio]
        
        df_trabalho = pd.melt(
            df_bruto, id_vars=[col_territorio], value_vars=setores_alvo,
            var_name='Setor', value_name='Empregos'
        )
        col_setor, col_variavel = 'Setor', 'Empregos'
    else:
        print("\033[1;32m[PMQA :: DETECT]\033[0m Padrão 'Long Table' (Tabela Linear) identificado. Mapeando colunas...")
        df_trabalho = df_bruto.copy()
        col_variavel = colunas_numericas[0] if colunas_numericas else df_trabalho.columns[-1]
        colunas_texto = [c for c in df_trabalho.columns if c != col_variavel]
        
        col_territorio = colunas_texto[0]
        col_setor = colunas_texto[1] if len(colunas_texto) > 1 else colunas_texto[0]
        
        for c in colunas_texto:
            c_low = c.lower()
            if any(k in c_low for k in ['municipio', 'uf', 'localidade', 'codigo', 'territorio', 'regiao']): col_territorio = c
            elif any(k in c_low for k in ['cnae', 'setor', 'atividade', 'classe', 'subclasse']): col_setor = c

    df_trabalho[col_variavel] = pd.to_numeric(df_trabalho[col_variavel], errors='coerce').fillna(0.0)
    
    return df_trabalho, col_territorio, col_setor, col_variavel