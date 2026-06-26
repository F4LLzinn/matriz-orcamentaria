import os
import pandas as pd
import geopandas as gpd
from libpysal.weights import Queen
from esda.moran import Moran, Moran_Local
from utils.arquivos import DIR_OUTPUTS

def executar_analise_dependencia_espacial(df_ql, caminho_mapa, col_territorio, col_setor_alvo):
    print("\n\033[1;34m[PMQA :: REGIONAL::GEOMETRIA]\033[0m Ativando engine de econometria espacial...")
    
    if not os.path.exists(caminho_mapa):
        print("\033[1;31m[ERRO :: MAPA]\033[0m Malha geográfica não localizada no caminho especificado.")
        raise FileNotFoundError()

    print("\033[36m-> [GEO::LOAD]\033[0m Renderizando polígonos e vetores espaciais...")
    malha = gpd.read_file(caminho_mapa)
    
    col_mapa_meso = None
    for c in malha.columns:
        if any(k in c.lower() for k in ['nm_meso', 'mesorregiao', 'nome', 'nm_regiao']):
            col_mapa_meso = c
            break
            
    if not col_mapa_meso:
        print("\033[1;31m[ERRO :: SEMÂNTICA]\033[0m Não foi possível identificar a coluna de territórios no mapa.")
        raise KeyError()

    malha[col_mapa_meso] = malha[col_mapa_meso].astype(str).str.strip().str.upper()
    df_ql[col_territorio] = df_ql[col_territorio].astype(str).str.strip().str.upper()

    df_setor = df_ql[df_ql[df_ql.columns[1]].astype(str).str.lower() == col_setor_alvo.lower()].copy()

    print("\033[36m-> [GEO::MERGE]\033[0m Acoplando matriz de emprego formal aos polígonos do IBGE...")
    geo_df = malha.merge(df_setor, left_on=col_mapa_meso, right_on=col_territorio, how='inner')

    if geo_df.empty:
        print("\033[1;31m[ERRO :: SIMETRIA]\033[0m Interseção vazia. Nomes das mesorregiões não coincidem com o mapa.")
        return {"status": "erro", "mensagem": "Incompatibilidade de nomes entre base e mapa."}

    print("\033[36m-> [GEO::WEIGHTS]\033[0m Construindo matriz de pesos por vizinhança Rainha (Queen)...")
    w = Queen.from_dataframe(geo_df, use_index=False)
    w.transform = 'R'

    col_valores_ql = geo_df.columns[-1] 
    y = geo_df[col_valores_ql].values

    print("\033[36m-> [GEO::MATH]\033[0m Computando autocorrelação estocástica de Moran...")
    moran_global = Moran(y, w)
    val_moran_global = round(moran_global.I, 4)
    p_value_global = round(moran_global.p_sim, 4)

    moran_local = Moran_Local(y, w, seed=42)
    mapeamento_quadrantes = {1: 'Alto-Alto', 2: 'Baixo-Alto', 3: 'Baixo-Baixo', 4: 'Alto-Baixo'}
    
    quadrantes_lisa = []
    for i in range(len(y)):
        if moran_local.p_sim[i] <= 0.05:
            quadrantes_lisa.append(mapeamento_quadrantes[moran_local.q[i]])
        else:
            quadrantes_lisa.append('Não Significante')

    geo_df['LISA_Quadrante'] = quadrantes_lisa
    geo_df['LISA_pValue'] = moran_local.p_sim

    resultado_tabela = geo_df[[col_territorio, col_valores_ql, 'LISA_Quadrante', 'LISA_pValue']].copy()
    
    nome_saida = f"analise_espacial_moran_lisa.csv"
    caminho_saida = os.path.join(DIR_OUTPUTS, nome_saida)
    
    with open(caminho_saida, 'w', encoding='cp1252', errors='replace', newline='') as f:
        f.write("sep=;\n")
        resultado_tabela.to_csv(f, index=False, sep=';')

    print(f"\033[1;32m[SUCESSO]\033[0m Moran Global: {val_moran_global} | LISA exportado para: '{nome_saida}'")
    
    return {
        "status": "sucesso",
        "moran_global": val_moran_global,
        "p_value_global": p_value_global,
        "arquivo_gerado": nome_saida
    }