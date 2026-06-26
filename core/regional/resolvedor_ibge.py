import requests
import pandas as pd
import os
import json
import unicodedata

def normalizar_texto_geografico(texto):
    """
    Remove acentos, hífens, espaços extras e corrige anomalias ortográficas 
    comuns em bases antigas do MTE (ex: bahiano -> baiano).
    """
    if pd.isna(texto):
        return ""
    nfkd_form = unicodedata.normalize('NFKD', str(texto).lower().strip())
    texto_limpo = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    # Padronização ortográfica defensiva para casamento de padrões
    texto_limpo = texto_limpo.replace('-', ' ').replace('bahia', 'baia')
    texto_limpo = texto_limpo.replace('bahiano', 'baiano').replace('bahiana', 'baiana')
    texto_limpo = texto_limpo.replace('piauiensi', 'piauiense')
    
    return " ".join(texto_limpo.split())

class ResolvedorTerritorialIBGE:
    def __init__(self):
        self.mapa_municipios = {}
        self.mapa_mesorregioes = {}
        self._inicializar_base_ibge()

    def _inicializar_base_ibge(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        caminho_cache = os.path.join(base_dir, '..', 'metadata', 'regional', 'cache_ibge_completo.json')
        
        if os.path.exists(caminho_cache):
            try:
                with open(caminho_cache, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.mapa_municipios = data.get('municipios', {})
                    self.mapa_mesorregioes = data.get('mesorregioes', {})
                print("\033[1;32m[PMQA :: IBGE]\033[0m Cache territorial universal carregado com sucesso.")
                return
            except Exception as e:
                print(f"[PMQA :: IBGE] Falha ao ler cache local, reconsultando API: {e}")

        print("\033[1;33m[PMQA :: IBGE]\033[0m Sincronizando malha territorial com a API do IBGE (Aguarde)...")
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/distritos"
        
        try:
            resposta = requests.get(url, timeout=10)
            if resposta.status_code == 200:
                distritos = resposta.json()
                
                for d in distritos:
                    municipio_obj = d.get('municipio')
                    if not municipio_obj:
                        continue
                        
                    nome_mun = str(municipio_obj.get('nome', '')).strip().lower()
                    micro_obj = municipio_obj.get('microrregiao')
                    if micro_obj:
                        nome_micro = micro_obj.get('nome', 'Ignorado')
                        meso_obj = micro_obj.get('mesorregiao')
                        if meso_obj:
                            nome_meso = meso_obj.get('nome', 'Ignorado')
                            uf_obj = meso_obj.get('UF')
                            if uf_obj:
                                sigla_uf = uf_obj.get('sigla', 'NL')
                                regiao_obj = uf_obj.get('regiao')
                                nome_macro = regiao_obj.get('nome', 'Outros') if regiao_obj else 'Outros'
                            else:
                                sigla_uf, nome_macro = 'NL', 'Outros'
                        else:
                            nome_meso, sigla_uf, nome_macro = 'Ignorado', 'NL', 'Outros'
                    else:
                        nome_micro, nome_meso, sigla_uf, nome_macro = 'Ignorado', 'Ignorado', 'NL', 'Outros'
                    
                    if nome_mun:
                        self.mapa_municipios[nome_mun] = {
                            "Microrregiao": nome_micro,
                            "Mesorregiao": nome_meso,
                            "UF": sigla_uf,
                            "Macroregiao": nome_macro
                        }

                        if nome_meso != 'Ignorado':
                            self.mapa_mesorregioes[nome_meso.strip().lower()] = nome_macro

                os.makedirs(os.path.dirname(caminho_cache), exist_ok=True)
                with open(caminho_cache, 'w', encoding='utf-8') as f:
                    json.dump({"municipios": self.mapa_municipios, "mesorregioes": self.mapa_mesorregioes}, f, indent=2, ensure_ascii=False)
                    
                print("\033[1;32m[PMQA :: IBGE]\033[0m Malha universal do Brasil sincronizada e salva em cache!")
        except Exception as e:
            print(f"[PMQA :: CRÍTICO] Falha ao conectar com o serviço do IBGE: {e}")

    def enriquecer_dataframe(self, df, col_territorio, tipo_dado):
        """
        Injeta dinamicamente as colunas de hierarquia geográfica com normalização tolerante
        para evitar que erros ortográficos da planilha quebrem os matches do JSON.
        """
        df_enriquecido = df.copy()
        
        # 🌟 Cria uma versão normalizada em cache do mapa de mesorregiões do JSON para o cruzamento
        mapa_meso_norm = {normalizar_texto_geografico(k): v for k, v in self.mapa_mesorregioes.items()}
        
        if tipo_dado == 'municipio':
            df_enriquecido['Microrregiao'] = df_enriquecido[col_territorio].astype(str).map(lambda x: self.mapa_municipios.get(x.strip().lower(), {}).get('Microrregiao', 'Não Localizado'))
            df_enriquecido['Mesorregiao'] = df_enriquecido[col_territorio].astype(str).map(lambda x: self.mapa_municipios.get(x.strip().lower(), {}).get('Mesorregiao', 'Não Localizado'))
            df_enriquecido['UF'] = df_enriquecido[col_territorio].astype(str).map(lambda x: self.mapa_municipios.get(x.strip().lower(), {}).get('UF', 'NL'))
            df_enriquecido['Macroregiao'] = df_enriquecido[col_territorio].astype(str).map(lambda x: self.mapa_municipios.get(x.strip().lower(), {}).get('Macroregiao', 'Outros'))
            
        elif tipo_dado == 'mesorregiao':
            # 🌟 O PULO DO GATO: Normaliza o nome que vem da planilha antes de checar contra o cache normalizado do JSON
            df_enriquecido['Macroregiao'] = df_enriquecido[col_territorio].astype(str).map(
                lambda x: mapa_meso_norm.get(normalizar_texto_geografico(x), 'Outros')
            )
            
        return df_enriquecido