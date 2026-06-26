import os
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename

from utils.arquivos import (
    DIR_INPUTS_ORCAMENTO, DIR_PARAMETROS, DIR_OUTPUTS,
    validar_extensao
)
from core.orcamento.pipeline_siga import executar_unificacao_matrizes
from core.orcamento.indexador_ipca import executar_indexacao_precos
from core.orcamento.engine_real import executar_calculo_deflacionamento

blueprint_orcamento = Blueprint('orcamento_bp', __name__)

@blueprint_orcamento.route('/orcamento')
def modulo_orcamento():
    try:
        arquivos_orcamento = [f for f in os.listdir(DIR_INPUTS_ORCAMENTO) if not f.startswith('~$') and validar_extensao(f)]
        arquivos_orcamento.sort()
        total_arquivos = len(arquivos_orcamento)
        arquivo_lider = arquivos_orcamento[0] if total_arquivos > 0 else "Nenhuma planilha carregada"
        
        arquivos_param = os.listdir(DIR_PARAMETROS)
        arquivo_ipca = None
        for f in arquivos_param:
            if 'ipeadata' in f.lower() and validar_extensao(f):
                arquivo_ipca = f
                break
    except Exception:
        total_arquivos = 0
        arquivo_lider = "Erro ao acessar diretório"
        arquivo_ipca = None
        arquivos_orcamento = []
        
    return render_template('orcamento.html', 
                           total_arquivos=total_arquivos, 
                           arquivo_lider=arquivo_lider, 
                           arquivo_ipca=arquivo_ipca,
                           lista_arquivos=arquivos_orcamento)

@blueprint_orcamento.route('/upload/orcamento', methods=['POST'])
def upload_orcamento():
    if 'arquivo' not in request.files:
        return jsonify({"status": "erro", "mensagem": "Arquivo ausente."}), 400
    arquivo = request.files['arquivo']
    if arquivo and validar_extensao(arquivo.filename):
        nome_seguro = secure_filename(arquivo.filename)
        arquivo.save(os.path.join(DIR_INPUTS_ORCAMENTO, nome_seguro))
        return jsonify({"status": "sucesso"})
    return jsonify({"status": "erro", "mensagem": "Extensão inválida."}), 400

@blueprint_orcamento.route('/limpar/orcamento/<filename>', methods=['POST'])
def remover_arquivo_orcamento(filename):
    try:
        nome_seguro = secure_filename(filename)
        caminho_arquivo = os.path.join(DIR_INPUTS_ORCAMENTO, nome_seguro)
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
            return jsonify({"status": "sucesso", "mensagem": f"Matriz '{nome_seguro}' removida do repositório local."})
        return jsonify({"status": "erro", "mensagem": "Arquivo não encontrado."}), 404
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Falha operacional: {str(e)}"}), 500

@blueprint_orcamento.route('/upload/ipca', methods=['POST'])
def upload_ipca():
    if 'arquivo' not in request.files:
        return jsonify({"status": "erro", "mensagem": "Arquivo ausente."}), 400
    arquivo = request.files['arquivo']
    if arquivo and arquivo.filename != '' and validar_extensao(arquivo.filename):
        nome_seguro = secure_filename(arquivo.filename)
        arquivo.save(os.path.join(DIR_PARAMETROS, nome_seguro))
        return jsonify({"status": "sucesso", "mensagem": f"Série do IPCA carregada: '{nome_seguro}'."})
    return jsonify({"status": "erro", "mensagem": "Falha no arquivo enviado."}), 400

@blueprint_orcamento.route('/limpar/ipca', methods=['POST'])
def limpar_ipca():
    try:
        arquivos_param = os.listdir(DIR_PARAMETROS)
        for f in arquivos_param:
            if 'ipeadata' in f.lower():
                os.remove(os.path.join(DIR_PARAMETROS, f))
        return jsonify({"status": "sucesso", "mensagem": "Série histórica removida de parâmetros."})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Falha na limpeza: {str(e)}"}), 500

@blueprint_orcamento.route('/processar', methods=['POST'])
def processar_pipeline():
    try:
        dados = request.get_json() or {}
        ano_base = dados.get('ano_base', '2025')
        modo = dados.get('modo', 'completo')

        if modo in ['completo', 'apenas_unificar']:
            executar_unificacao_matrizes()
            
        if modo in ['completo', 'gerar_fator']:
            executar_indexacao_precos(ano_base_usuario=ano_base)

        if modo == 'completo':
            executar_calculo_deflacionamento()

        mensagens_sucesso = {
            "completo": f"Ajuste inflacionário e consolidação concluídos com sucesso para o ano-base {ano_base}.",
            "apenas_unificar": "Alinhamento estrutural e unificação das matrizes orçamentárias executados.",
            "gerar_fator": f"Geração da série de fatores de correção concluída para o ano-base {ano_base}."
        }
        return jsonify({"status": "sucesso", "mensagem": mensagens_sucesso.get(modo, "Concluído.")})

    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Quebra no pipeline de orçamento: {str(e)}"}), 500