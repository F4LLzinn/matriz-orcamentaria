import os
import pandas as pd
from utils.arquivos import DIR_OUTPUTS

def calcular_indicadores_regionais(df_trabalho, col_territorio, col_setor, col_variavel, indicador_desejado, exportar_intermediarias=False):
    print(f"\n\033[1;34m[PMQA :: REGIONAL::MATH]\033[0m Executando equações matriciais para: {indicador_desejado.upper()}")
    
    df_matriz_base = df_trabalho.pivot(index=col_territorio, columns=col_setor, values=col_variavel).fillna(0.0)

    E_j = df_matriz_base.sum(axis=1)
    E_i = df_matriz_base.sum(axis=0)
    E   = df_matriz_base.sum().sum()

    if exportar_intermediarias:
        print("\033[36m-> [EXPORT]\033[0m Gerando matrizes estruturais intermediárias (Matriz I e II)...")
        
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

        df_m2_wide = df_matriz_base.div(E_i.replace(0, 1), axis=1).round(4)
        df_m2_wide['TOTAL'] = (E_j / E).round(4)
        linha_total_m2 = pd.Series(1.0000, index=df_m2_wide.columns)
        linha_total_m2.name = 'TOTAL BRASIL'
        df_m2_wide = pd.concat([df_m2_wide, pd.DataFrame([linha_total_m2])])
        df_m2_wide.index.name = col_territorio
        df_m2_wide = df_m2_wide.reset_index()
        
        with open(os.path.join(DIR_OUTPUTS, 'matriz_II_structure_regional.csv'), 'w', encoding='cp1252', errors='replace', newline='') as f:
            f.write("sep=;\n")
            df_m2_wide.to_csv(f, index=False, sep=';')

    if indicador_desejado == 'ql_tradicional':
        numerador = df_matriz_base.div(E_j.replace(0, 1), axis=0)
        denominador = E_i / (1 if E == 0 else E)
        df_saida_final = numerador.div(denominador.replace(0, 1), axis=1).round(4)
        df_saida_final['TOTAL'] = 1.0000
        linha_total = pd.Series(1.0000, index=df_saida_final.columns)
        linha_total.name = 'TOTAL BRASIL'
        df_saida_final = pd.concat([df_saida_final, pd.DataFrame([linha_total])])

    elif indicador_desejado == 'ce':
        numerador = df_matriz_base.div(E_j.replace(0, 1), axis=0)
        denominador = E_i / (1 if E == 0 else E)
        df_saida_final = (numerador - denominador).round(4)
        df_saida_final['TOTAL'] = (0.5 * (numerador - denominador).abs().sum(axis=1)).round(4)
        linha_total_ce = pd.Series(0.0000, index=df_saida_final.columns)
        linha_total_ce.name = 'TOTAL BRASIL'
        df_saida_final = pd.concat([df_saida_final, pd.DataFrame([linha_total_ce])])

    elif indicador_desejado == 'ql_loo':
        num_loo = df_matriz_base.div(E_j.replace(0, 1), axis=0)
        df_E_i = pd.DataFrame([E_i] * len(df_matriz_base), index=df_matriz_base.index)
        den_loo = df_E_i.sub(df_matriz_base).div((E - E_j).replace(0, 1), axis=0)
        df_saida_final = num_loo.div(den_loo.replace(0, 1)).round(4)
        df_saida_final['TOTAL'] = 1.0000
        linha_total_loo = pd.Series(1.0000, index=df_saida_final.columns)
        linha_total_loo.name = 'TOTAL BRASIL'
        df_saida_final = pd.concat([df_saida_final, pd.DataFrame([linha_total_loo])])

    df_saida_final.index.name = col_territorio
    df_saida_final = df_saida_final.reset_index()

    nome_saida = f"analise_regional_autonoma_{indicador_desejado}.csv"
    caminho_saida = os.path.join(DIR_OUTPUTS, nome_saida)

    with open(caminho_saida, 'w', encoding='cp1252', errors='replace', newline='') as f:
        f.write("sep=;\n")
        df_saida_final.to_csv(f, index=False, sep=';')

    print(f"\033[1;32m[SUCESSO]\033[0m Relatório final de indicadores persistido em: '{caminho_saida}'")
    return {"status": "sucesso", "arquivo_gerado": nome_saida, "dados_df": df_saida_final}