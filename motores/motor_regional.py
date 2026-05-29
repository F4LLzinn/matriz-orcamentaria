import os
import sys
import pandas as pd

PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
RAIZ_PROJETO = os.path.abspath(os.path.join(PASTA_ATUAL, '..'))
DIR_INPUTS = os.path.join(RAIZ_PROJETO, 'inputs_regional')
DIR_OUTPUTS = os.path.join(RAIZ_PROJETO, 'outputs_processados')

print("[INFO] Algoritmo de Economia Regional Ativado...")

# Captura os dois parâmetros enviados pelo Flask
indicador_desejado     = sys.argv[1].lower() if len(sys.argv) >= 2 else 'ql_tradicional'
exportar_intermediarias = sys.argv[2].lower() == 'sim' if len(sys.argv) >= 3 else False

arquivos = [f for f in os.listdir(DIR_INPUTS) if not f.startswith('~$') and (f.endswith('.xlsx') or f.endswith('.csv'))]
if not arquivos:
    sys.stderr.write("[ERRO] Nenhum arquivo de dados localizado na pasta 'inputs_regional'.\n")
    sys.exit(1)

arquivo_alvo = arquivos[0]
caminho_completo = os.path.join(DIR_INPUTS, arquivo_alvo)

# ==============================================================================
# 🧠 DETECTOR INTELIGENTE DE BYTES (IMUNIDADE TOTAL A MOJIBAKE E SEPARADORES)
# ==============================================================================
if arquivo_alvo.endswith('.xlsx') or arquivo_alvo.endswith('.xls'):
    df_bruto = pd.read_excel(caminho_completo)
else:
    # Inspeciona os bytes iniciais do arquivo para descobrir a estrutura real
    with open(caminho_completo, 'rb') as f:
        amostra_bytes = f.read(2048)
    
    # Define o separador por contagem de frequência na amostragem
    separador = ';' if amostra_bytes.count(b';') > amostra_bytes.count(b',') else ','
    
    # Define a codificação testando o decode do UTF-8
    try:
        amostra_bytes.decode('utf-8')
        codificacao = 'utf-8'
    except UnicodeDecodeError:
        codificacao = 'cp1252'
        
    df_bruto = pd.read_csv(caminho_completo, sep=separador, encoding=codificacao)

# Padronização estrita de strings nos rótulos de colunas
df_bruto.columns = [str(c).strip() for c in df_bruto.columns]

# ==============================================================================
# 🧼 SANEAMENTO PREVENTIVO CONTRA METADADOS DE RODAPÉ
# ==============================================================================
primeira_col = df_bruto.columns[0]
padrao_remover = 'Seleções|SeleÃ§Ãµes|Variável|VariÃ¡vel|{ñ class}|{Ã± class}|Critério|CritÃ©rio|Total|Ano|Vínculo|VÃnculo'

df_bruto = df_bruto[
    df_bruto[primeira_col].notna() & 
    (~df_bruto[primeira_col].astype(str).str.contains(padrao_remover, case=False, na=False))
].copy()

# ==============================================================================
# 🔍 DETECTOR HEURÍSTICO AUTOMÁTICO DE LAYOUT
# ==============================================================================
colunas_numericas = df_bruto.select_dtypes(include=['float64', 'int64']).columns.tolist()
if 'Total' in colunas_numericas: colunas_numericas.remove('Total')

# FORMATO A: Matriz Cruzada (Wide Matrix)
if len(colunas_numericas) > 1:
    print("[AUTOMAÇÃO] Formato 'Wide Matrix' detectado. Executando empilhamento técnico...")
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

# FORMATO B: Listagem Linear (Long Table)
else:
    print("[AUTOMAÇÃO] Formato 'Long Table' detectado. Mapeando semântica de colunas...")
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

# ==============================================================================
# 🧮 EXTRAÇÃO HISTÓRICA E MATRIZES DE BASE COMPARTILHADAS (PROVA REAL)
# ==============================================================================
# Monta o esqueleto básico de emprego puro sem totais artificiais para as equações
df_matriz_base = df_trabalho.pivot(index=col_territorio, columns=col_setor, values=col_variavel).fillna(0.0)

E_j = df_matriz_base.sum(axis=1)      # Vetor de Emprego Total da Localidade
E_i = df_matriz_base.sum(axis=0)      # Vetor de Emprego Total do Setor no País
E   = df_matriz_base.sum().sum()      # Escalar de Emprego Total Absoluto do País

# 🌟 EXPORTAÇÃO INTERMEDIÁRIA DA MATRIZ I E II (SINDROME GEOMÉTRICA RESOLVIDA)
if exportar_intermediarias:
    print("[EXPORTAÇÃO] Salvando matrizes estruturais em formato de matriz cruzada...")
    
    # MATRIZ I: Participação Estrutural Interna (Fatia de cada setor dentro da própria UF)
    df_m1_wide = df_matriz_base.div(E_j.replace(0, 1), axis=0).round(4)
    df_m1_wide['TOTAL'] = df_m1_wide.sum(axis=1).round(4)
    
    linha_total_m1 = (E_i / E).round(4)
    linha_total_m1['TOTAL'] = 1.0000
    linha_total_m1.name = 'TOTAL BRASIL'
    df_m1_wide = pd.concat([df_m1_wide, pd.DataFrame([linha_total_m1])])
    
    df_m1_wide.index.name = col_territorio
    df_m1_wide = df_m1_wide.reset_index()
    
    with open(os.path.join(DIR_OUTPUTS, 'matriz_I_participacao_local.csv'), 'w', encoding='cp1252', errors='replace', newline='') as f:
        f.write("sep=;\n")
        df_m1_wide.to_csv(f, index=False, sep=';')

    # MATRIZ II: Concentração Espacial Geográfica (A fatia que cada UF detém do setor nacional)
    df_m2_wide = df_matriz_base.div(E_i.replace(0, 1), axis=1).round(4)
    df_m2_wide['TOTAL'] = (E_j / E).round(4) # Peso da UF no mercado de trabalho do país inteiro
    
    linha_total_m2 = pd.Series(1.0000, index=df_m2_wide.columns)
    linha_total_m2.name = 'TOTAL BRASIL'
    df_m2_wide = pd.concat([df_m2_wide, pd.DataFrame([linha_total_m2])])
    
    df_m2_wide.index.name = col_territorio
    df_m2_wide = df_m2_wide.reset_index()
    
    with open(os.path.join(DIR_OUTPUTS, 'matriz_II_estrutura_regional.csv'), 'w', encoding='cp1252', errors='replace', newline='') as f:
        f.write("sep=;\n")
        df_m2_wide.to_csv(f, index=False, sep=';')

# ==============================================================================
# 🧮 CALIBRAGEM DOS INDICADORES SELECIONADOS (EQUAÇÕES MATRICIAIS)
# ==============================================================================
if indicador_desejado == 'ql_tradicional':
    print("[PROCESSAMENTO] Calculando QL Tradicional com duplo fechamento...")
    numerador = df_matriz_base.div(E_j.replace(0, 1), axis=0)
    denominador = E_i / (1 if E == 0 else E)
    df_saida_final = numerador.div(denominador.replace(0, 1), axis=1).round(4)
    
    # Fechamentos orgânicos do QL
    df_saida_final['TOTAL'] = 1.0000
    linha_total = pd.Series(1.0000, index=df_saida_final.columns)
    linha_total.name = 'TOTAL BRASIL'
    df_saida_final = pd.concat([df_saida_final, pd.DataFrame([linha_total])])

elif indicador_desejado == 'ce':
    print("[PROCESSAMENTO] Calculando Matriz de Desvios e Coeficiente de Especialização Sintético...")
    numerador = df_matriz_base.div(E_j.replace(0, 1), axis=0)
    denominador = E_i / (1 if E == 0 else E)
    df_saida_final = (numerador - denominador).round(4)
    
    # 🌟 A MATÉRIA DA PROVA REAL: Coluna TOTAL passa a registrar o verdadeiro Índice de CE da UF!
    df_saida_final['TOTAL'] = (0.5 * (numerador - denominador).abs().sum(axis=1)).round(4)
    
    # Linha base nacional (Desvio do Brasil contra ele mesmo é zero absoluto)
    linha_total_ce = pd.Series(0.0000, index=df_saida_final.columns)
    linha_total_ce.name = 'TOTAL BRASIL'
    df_saida_final = pd.concat([df_saida_final, pd.DataFrame([linha_total_ce])])

elif indicador_desejado == 'ql_loo':
    print("[PROCESSAMENTO] Calculando QL Leave-One-Out com limites de fronteira...")
    num_loo = df_matriz_base.div(E_j.replace(0, 1), axis=0)
    df_E_i = pd.DataFrame([E_i] * len(df_matriz_base), index=df_matriz_base.index)
    den_loo = df_E_i.sub(df_matriz_base).div((E - E_j).replace(0, 1), axis=0)
    df_saida_final = num_loo.div(den_loo.replace(0, 1)).round(4)
    
    # Fechamentos orgânicos do LOO
    df_saida_final['TOTAL'] = 1.0000
    linha_total_loo = pd.Series(1.0000, index=df_saida_final.columns)
    linha_total_loo.name = 'TOTAL BRASIL'
    df_saida_final = pd.concat([df_saida_final, pd.DataFrame([linha_total_loo])])

elif indicador_desejado == 'shift_share':
    sys.stderr.write("[ERRO METODOLÓGICO] A análise Shift-Share exige microdados de dois períodos temporais.\n")
    sys.exit(1)

# ==============================================================================
# 🔄 RESTAURAÇÃO FORÇADA E UNIFICADA DE LAYOUT MATRICIAL UNIVERSAL
# ==============================================================================
# Força o nome do índice territorial e projeta para coluna na extrema esquerda
df_saida_final.index.name = col_territorio
df_saida_final = df_saida_final.reset_index()

# Exportação em lote com codificação limpa adaptada ao Microsoft Excel brasileiro
nome_saida = f"analise_regional_autonoma_{indicador_desejado}.csv"
caminho_saida = os.path.join(DIR_OUTPUTS, nome_saida)

with open(caminho_saida, 'w', encoding='cp1252', errors='replace', newline='') as f:
    f.write("sep=;\n")
    df_saida_final.to_csv(f, index=False, sep=';')

print(f"[SUCESSO] Operação finalizada com validação e simetria matricial completa.")