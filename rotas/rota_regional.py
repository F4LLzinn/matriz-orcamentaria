import os
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename

from utils.arquivos import DIR_INPUTS_REGIONAL, DIR_PARAMETROS, validar_extensao
from core.regional.layout_handler import processar_e_padronizar_layout
from core.regional.indicadores import calcular_indicadores_regionais
from core.regional.analise_espacial import executar_analise_dependencia_espacial

blueprint_regional = Blueprint('regional_bp', __name__)

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

        arquivos = [f for f in os.listdir(DIR_INPUTS_REGIONAL) if not f.startswith('~$') and validar_extensao(f)]
        if not arquivos:
            return jsonify({"status": "erro", "mensagem": "Nenhum arquivo localizado em inputs_regional."}), 400

        caminho_planilha = os.path.join(DIR_INPUTS_REGIONAL, arquivos[0])
        
        # 🛡️ Integração Corrigida: Recebendo a variável macroregioes para matar o erro de unpack
        df_trabalho, col_territorio, col_setor, col_variavel, macroregioes = processar_e_padronizar_layout(caminho_planilha)

        resultado = calcular_indicadores_regionais(
            df_trabalho, col_territorio, col_setor, col_variavel, 
            indicador, exportar_matrizes
        )

        if indicador == 'ql_tradicional':
            arquivos_param = os.listdir(DIR_PARAMETROS)
            shapefile_alvo = [f for f in arquivos_param if f.endswith('.shp')]
            
            if shapefile_alvo:
                caminho_mapa = os.path.join(DIR_PARAMETROS, shapefile_alvo[0])
                executar_analise_dependencia_espacial(
                    df_ql=resultado['dados_df'],
                    caminho_mapa=caminho_mapa,
                    col_territorio=col_territorio,
                    col_setor_alvo='Indústria de Transformação'
                )

        return jsonify({
            "status": "sucesso",
            "mensagem": "Análise de economia regional e indicadores gerados com sucesso."
        })

    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Falha no pipeline regional: {str(e)}"}), 500