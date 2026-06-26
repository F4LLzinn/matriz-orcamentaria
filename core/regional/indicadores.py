import os
import pandas as pd
import numpy as np
import unicodedata

def normalizar_texto_geografico(texto):
    if pd.isna(texto):
        return ""
    # Transforma em string, remove acentos e caracteres ocultos
    nfkd_form = unicodedata.normalize('NFKD', str(texto).lower().strip())
    texto_limpo = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    # Tratamento de contingência para hífens e variações da RAIS
    texto_limpo = texto_limpo.replace('-', ' ').replace('bahia', 'baia')
    texto_limpo = texto_limpo.replace('bahiano', 'baiano').replace('bahiana', 'baiana')
    texto_limpo = texto_limpo.replace('piauiensi', 'piauiense')
    return " ".join(texto_limpo.split())

def calcular_indicadores_regionais(df_trabalho, col_territorio, col_setor, col_variavel, indicador_desejado, exportar_intermediarias=False, filtro_macroregiao='Todos', macroregioes=None):
    print(f"\n\033[1;32m[PMQA :: CACHE INTEGRADO]\033[0m Processando via JSON. Filtro: {filtro_macroregiao}")
    
    df_limpo = df_trabalho.copy()
    df_limpo = df_limpo[df_limpo[col_territorio].notna()].copy()
    
    padrao_lixo = r'(?i)(vínculo|vinculo|seleç|selec|total|variáv|variav|ano|ibge)'
    df_limpo = df_limpo[~df_limpo[col_territorio].astype(str).str.contains(padrao_lixo, na=False)].copy()

    df_matriz_base = df_limpo.pivot_table(
        index=col_territorio, 
        columns=col_setor, 
        values=col_variavel, 
        aggfunc='sum'
    ).fillna(0.0)

    termos_invalidos = ['nan', 'mesorregião', 'mesorregiões', 'mesorregiaes']
    df_matriz_base = df_matriz_base[~df_matriz_base.index.astype(str).str.lower().str.strip().isin(termos_invalidos)].copy()

    E_i = df_matriz_base.sum(axis=1) 
    E_j = df_matriz_base.sum(axis=0) 
    E   = df_matriz_base.sum().sum()   

    diretorio_output = r"D:\Trabalhos\Meus\Projeto_Kairoz\outputs_processados"
    os.makedirs(diretorio_output, exist_ok=True)

    params_salvamento = {"sep": ",", "decimal": ".", "encoding": "utf-8-sig"}

    dicionario_normalizado = {}
    if macroregioes is not None:
        for k, v in macroregioes.items():
            dicionario_normalizado[normalizar_texto_geografico(k)] = v

    if indicador_desejado == 'ql_tradicional':
        num_ql = df_matriz_base.div(E_i.replace(0, 1), axis=0)
        den_ql = E_j / E
        df_saida_final = num_ql.div(den_ql.replace(0, 1), axis=1).round(4)
        linha_ref_final = pd.Series(1.0000, index=df_saida_final.columns)
        linha_ref_final.name = 'TOTAL BRASIL'
    elif indicador_desejado == 'coeficiente_especializacao':
        num_ce = df_matriz_base.div(E_i.replace(0, 1), axis=0)
        den_ce = E_j / E
        df_saida_final = num_ce.sub(den_ce, axis=1).abs()
        df_saida_final['TOTAL'] = (0.5 * df_saida_final.sum(axis=1)).round(4)
        linha_ref_final = pd.Series(0.0000, index=df_saida_final.columns)
        linha_ref_final.name = 'TOTAL BRASIL'
    elif indicador_desejado == 'ql_loo':
        num_loo = df_matriz_base.div(E_i.replace(0, 1), axis=0)
        df_E_j = pd.DataFrame([E_j.values] * len(df_matriz_base), index=df_matriz_base.index, columns=df_matriz_base.columns)
        den_loo = df_E_j.sub(df_matriz_base).div((E - E_i.values).reshape(-1, 1), axis=0)
        df_saida_final = num_loo.div(den_loo.replace(0, 1)).round(4)
        linha_ref_final = pd.Series(1.0000, index=df_saida_final.columns)
        linha_ref_final.name = 'TOTAL BRASIL'

    df_saida_final = df_saida_final.reset_index()
    df_saida_final['Macroregiao'] = df_saida_final[col_territorio].map(lambda x: dicionario_normalizado.get(normalizar_texto_geografico(x), 'Outros'))

    if filtro_macroregiao != 'Todos':
        df_corpo = df_saida_final[df_saida_final['Macroregiao'] == filtro_macroregiao].drop(columns=['Macroregiao'])
    else:
        df_corpo = df_saida_final.drop(columns=['Macroregiao'])
        
    df_corpo = df_corpo.set_index(col_territorio).sort_index()
    df_saida_salvamento = pd.concat([df_corpo, pd.DataFrame([linha_ref_final])])

    caminho_final = os.path.join(diretorio_output, f"analise_regional_autonoma_{indicador_desejado}.csv")
    df_saida_salvamento.to_csv(caminho_final, **params_salvamento)

    df_visualizacao = df_corpo.copy()
    df_visualizacao.index.name = col_territorio
    df_longo_retorno = df_visualizacao.reset_index().melt(
        id_vars=[col_territorio],
        var_name=col_setor,
        value_name='QL' if indicador_desejado == 'ql_tradicional' else 'Valor'
    )

    return {"dados_df": df_longo_retorno, "caminho_arquivo": caminho_final}