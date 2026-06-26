import os
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename

from utils.arquivos import DIR_INPUTS_REGIONAL, DIR_PARAMETROS, validar_extensao
from core.regional.layout_handler import detectar_layout
from core.regional.indicadores import calcular_indicadores_regionais
from core.regional.analise_espacial import executar_analise_dependencia_espacial
from core.regional.resolvedor_ibge import ResolvedorTerritorialIBGE

blueprint_regional = Blueprint('regional_bp', __name__)

resolvedor_ibge = ResolvedorTerritorialIBGE()

@blueprint_regional.route('/regional')
def modulo_regional():
    try:
        arquivos_regionais = [f for f in os.listdir(DIR_INPUTS_REGIONAL) if not f.startswith('~$') and validar_extensao(f)]
        arquivos_regionais.sort()
    except Exception:
        arquivos_regionais = []
    return render_template('regional.html', lista_arquivos=arquivos_regionais)

@blueprint_regional.route('/upload/regional', methods=['POST'])
def upload_regional():
    if 'arquivo' not in request.files:
        return jsonify({"status": "erro", "mensagem": "Arquivo ausente."}), 400
    arquivo = request.files['arquivo']
    if arquivo and validar_extensao(arquivo.filename):
        nome_seguro = secure_filename(arquivo.filename)
        arquivo.save(os.path.join(DIR_INPUTS_REGIONAL, nome_seguro))
        return jsonify({"status": "sucesso"})
    return jsonify({"status": "erro", "mensagem": "Extensão inválida."}), 400

@blueprint_regional.route('/limpar/regional/<filename>', methods=['POST'])
def remover_arquivo_regional(filename):
    try:
        nome_seguro = secure_filename(filename)
        caminho_arquivo = os.path.join(DIR_INPUTS_REGIONAL, nome_seguro)
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
            return jsonify({"status": "sucesso", "mensagem": f"Arquivo '{nome_seguro}' removido com sucesso."})
        return jsonify({"status": "erro", "mensagem": "Arquivo não encontrado."}), 404
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro operacional: {str(e)}"}), 500

@blueprint_regional.route('/processar_regional', methods=['POST'])
def processar_regional():
    try:
        dados = request.get_json() or {}
        indicador = dados.get('indicador', 'ql_tradicional')
        exportar_matrizes = dados.get('exportar_matrizes', False)
        filtro_macroregiao = dados.get('filtro_macroregiao', 'Todos') 
        tipo_espectro = dados.get('espectro', 'interregional')        
        agregar_por = dados.get('agregar_por', 'original')          

        arquivos = [f for f in os.listdir(DIR_INPUTS_REGIONAL) if not f.startswith('~$') and validar_extensao(f)]
        if not arquivos:
            return jsonify({"status": "erro", "mensagem": "Nenhum arquivo localizado em inputs_regional."}), 400

        caminho_planilha = os.path.join(DIR_INPUTS_REGIONAL, arquivos[0])
        
        df_longo, col_territorio, col_setor, col_variavel, macroregioes = detectar_layout(caminho_planilha, resolvedor_ibge)

        tipo_dado = 'municipio' if 'municip' in str(col_territorio).lower() else 'mesorregiao'
        df_enriquecido = resolvedor_ibge.enriquecer_dataframe(df_longo, col_territorio, tipo_dado)

        if tipo_espectro == 'intraregional' and filtro_macroregiao != 'Todos':
            df_calculo = df_enriquecido[df_enriquecido['Macroregiao'] == filtro_macroregiao].copy()
            rotulo_total = f"TOTAL {filtro_macroregiao.upper()} (Referência Interna)"
        else:
            df_calculo = df_enriquecido.copy()
            rotulo_total = "TOTAL BRASIL (Referência Nacional)"

        resultado = calcular_indicadores_regionais(
            df_trabalho=df_calculo, 
            col_territorio=col_territorio, 
            col_setor=col_setor, 
            col_variavel=col_variavel, 
            indicador_desejado=indicador, 
            exportar_intermediarias=exportar_matrizes,
            filtro_macroregiao=filtro_macroregiao,
            macroregioes=macroregioes
        )
        
        df_resultado = resultado['dados_df']

        # ==================== FILTRO PÓS-CÁLCULO CORRIGIDO NA ROTA ====================
        if tipo_espectro == 'interregional' and filtro_macroregiao != 'Todos':
            print(f"\033[1;33m[PMQA :: FILTRO]\033[0m Filtrando visualização pós-cálculo tolerante para: {filtro_macroregiao}")
            
            # Normaliza o dicionário de macroregiões para evitar quebras por maiúsculas/acentos
            from core.regional.indicadores import normalizar_texto_geografico
            dicionario_rota_norm = {normalizar_texto_geografico(k): v for k, v in macroregioes.items()}
            
            # Aplica o mapeamento usando a string normalizada
            df_resultado['Macroregiao'] = df_resultado[col_territorio].astype(str).map(
                lambda x: dicionario_rota_norm.get(normalizar_texto_geografico(x), 'Outros')
            )
            df_resultado = df_resultado[df_resultado['Macroregiao'] == filtro_macroregiao].copy()
        # ==============================================================================

        if agregar_por != 'original' and agregar_por in df_resultado.columns:
            print(f"\033[1;36m[PMQA :: AGREGADOR]\033[0m Agrupando resultados finais por: '{agregar_por}'")
            df_resultado = df_resultado.groupby([agregar_por, col_setor]).sum().reset_index()

        if indicador == 'ql_tradicional':
            arquivos_param = os.listdir(DIR_PARAMETROS)
            shapefile_alvo = [f for f in arquivos_param if f.endswith('.shp')]
            
            if shapefile_alvo:
                caminho_mapa = os.path.join(DIR_PARAMETROS, shapefile_alvo[0])
                try:
                    executar_analise_dependencia_espacial(
                        df_ql=df_resultado,
                        caminho_mapa=caminho_mapa,
                        col_territorio=agregar_por if agregar_por != 'original' else col_territorio,
                        col_setor_alvo='Indústria de Transformação'
                    )
                except Exception as esp_err:
                    print(f"[PMQA :: MAPA] Aviso - Falha no cálculo de dependência espacial: {esp_err}")

        return jsonify({
            "status": "sucesso",
            "dados": df_resultado.to_dict(orient='records'),
            "totalizador": rotulo_total,
            "col_territorio": agregar_por if agregar_por != 'original' else col_territorio
        })

    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Falha no pipeline regional: {str(e)}"}), 500