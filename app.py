import os
import sys
import subprocess
import platform
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ==============================================================================
# 📂 CONFIGURAÇÃO DE DIRETÓRIOS CRÍTICOS (MODULARIZADOS)
# ==============================================================================
PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'

# Módulo 1: Orçamento Público
DIR_INPUTS_ORCAMENTO = os.path.join(PASTA_ATUAL, 'inputs_orcamento')
DIR_PARAMETROS = os.path.join(PASTA_ATUAL, 'parametros')

# Módulo 2: Economia Regional (NOVO!)
DIR_INPUTS_REGIONAL = os.path.join(PASTA_ATUAL, 'inputs_regional')

# Saída unificada de resultados
DIR_OUTPUTS = os.path.join(PASTA_ATUAL, 'outputs_processados')

# Garante a existência física das pastas no HD
os.makedirs(DIR_INPUTS_ORCAMENTO, exist_ok=True)
os.makedirs(DIR_INPUTS_REGIONAL, exist_ok=True)
os.makedirs(DIR_OUTPUTS, exist_ok=True)
os.makedirs(DIR_PARAMETROS, exist_ok=True)

EXTENSOES_PERMITIDAS = {'.csv', '.xlsx', '.xls'}

def arquivo_permitido(filename):
    _, ext = os.path.splitext(filename.lower())
    return ext in EXTENSOES_PERMITIDAS

# ==============================================================================
# 🧭 ROTAS DE NAVEGAÇÃO PRINCIPAL (SISTEMA MULTI-PÁGINAS)
# ==============================================================================

@app.route('/')
def menu_principal():
    """Rota Raiz: Apresenta o menu neumórfico principal para escolha do módulo."""
    return render_template('menu.html')  # <-- Nova tela de Splash/Menu que vamos criar

@app.route('/orcamento')
def modulo_orcamento():
    """Painel Orçamentário (Seu sistema antigo do Siga Brasil)."""
    try:
        arquivos_orcamento = [f for f in os.listdir(DIR_INPUTS_ORCAMENTO) if not f.startswith('~$') and arquivo_permitido(f)]
        arquivos_orcamento.sort()
        total_arquivos = len(arquivos_orcamento)
        arquivo_lider = arquivos_orcamento[0] if total_arquivos > 0 else "Nenhuma planilha carregada"
        
        arquivos_param = os.listdir(DIR_PARAMETROS)
        arquivo_ipca = None
        for f in arquivos_param:
            if 'ipeadata' in f.lower() and (f.endswith('.csv') or f.endswith('.txt') or f.endswith('.xls') or f.endswith('.xlsx')):
                arquivo_ipca = f
                break
    except Exception:
        total_arquivos = 0
        arquivo_lider = "Erro ao ler o diretório"
        arquivo_ipca = None
        arquivos_orcamento = []
        
    # Rentabiliza o layout antigo alterando de index.html para orcamento.html se desejar separar
    return render_template('orcamento.html', 
                           total_arquivos=total_arquivos, 
                           arquivo_lider=arquivo_lider, 
                           arquivo_ipca=arquivo_ipca,
                           lista_arquivos=arquivos_orcamento)

@app.route('/regional')
def modulo_regional():
    """Painel de Economia Regional (Cálculo de QL, CE, Shift-Share)."""
    try:
        arquivos_regionais = [f for f in os.listdir(DIR_INPUTS_REGIONAL) if not f.startswith('~$') and arquivo_permitido(f)]
        arquivos_regionais.sort()
    except Exception:
        arquivos_regionais = []
    return render_template('regional.html', lista_arquivos=arquivos_regionais)

# ==============================================================================
# 📥 PROCESSAMENTO DE UPLOADS E LIMPEZAS (ORÇAMENTO)
# ==============================================================================

@app.route('/upload/orcamento', methods=['POST'])
def upload_orcamento():
    if 'arquivo' not in request.files:
        return jsonify({"status": "erro", "mensagem": "Arquivo ausente."}), 400
    arquivo = request.files['arquivo']
    if arquivo and arquivo_permitido(arquivo.filename):
        nome_seguro = secure_filename(arquivo.filename)
        arquivo.save(os.path.join(DIR_INPUTS_ORCAMENTO, nome_seguro))
        return jsonify({"status": "sucesso"})
    return jsonify({"status": "erro", "mensagem": "Extensão inválida."}), 400

@app.route('/limpar/orcamento/<filename>', methods=['POST'])
def remover_arquivo_orcamento(filename):
    try:
        nome_seguro = secure_filename(filename)
        caminho_arquivo = os.path.join(DIR_INPUTS_ORCAMENTO, nome_seguro)
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
            return jsonify({"status": "sucesso", "mensagem": f"Arquivo '{nome_seguro}' removido do repositório local."})
        return jsonify({"status": "erro", "mensagem": "Arquivo não encontrado."}), 404
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro ao deletar arquivo: {str(e)}"}), 500

@app.route('/upload/ipca', methods=['POST'])
def upload_ipca():
    if 'arquivo' not in request.files:
        return jsonify({"status": "erro", "mensagem": "Arquivo ausente."}), 400
    arquivo = request.files['arquivo']
    if arquivo and arquivo.filename != '':
        if arquivo_permitido(arquivo.filename):
            nome_seguro = secure_filename(arquivo.filename)
            caminho_final = os.path.join(DIR_PARAMETROS, nome_seguro)
            arquivo.save(caminho_final)
            return jsonify({"status": "sucesso", "mensagem": f"Série do IPCA carregada: '{nome_seguro}'."})
    return jsonify({"status": "erro", "mensagem": "Falha no arquivo enviado."}), 400

@app.route('/limpar/ipca', methods=['POST'])
def limpar_ipca():
    try:
        arquivos_param = os.listdir(DIR_PARAMETROS)
        for f in arquivos_param:
            if 'ipeadata' in f.lower():
                os.remove(os.path.join(DIR_PARAMETROS, f))
        return jsonify({"status": "sucesso", "mensagem": "Série histórica removida."})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Falha ao remover arquivo: {str(e)}"}), 500

# ==============================================================================
# 🎮 EXECUÇÃO DOS MOTORES TRASEIROS (VIA SUBPROCESS EM SUBPASTAS)
# ==============================================================================

@app.route('/processar', methods=['POST'])
def processar_pipeline():
    """Chama os motores de orçamento que agora estão abrigados na pasta /motores"""
    try:
        dados = request.get_json() or {}
        ano_base = dados.get('ano_base', '2025')
        modo = dados.get('modo', 'completo')

        print(f"[LOG] Processamento Orçamentário. Modo: {modo} | Ano-base: {ano_base}")

        # 🛡️ ALTERAÇÃO CIRÚRGICA: Aponta para a nova pasta 'motores'
        caminho_unificador = os.path.join(PASTA_ATUAL, 'motores', 'motor_unificador.py')
        caminho_deflator = os.path.join(PASTA_ATUAL, 'motores', 'motor_deflator.py')
        caminho_calculadora = os.path.join(PASTA_ATUAL, 'motores', 'motor_calculadora.py')

        # Passo 1: Unificador
        if modo in ['completo', 'apenas_unificar']:
            if len([f for f in os.listdir(DIR_INPUTS_ORCAMENTO) if arquivo_permitido(f)]) == 0:
                return jsonify({"status": "erro", "mensagem": "Nenhuma planilha orçamentária encontrada."}), 400

            # Executa o motor unificador de orçamento em segundo plano
            resultado = subprocess.run([
                sys.executable, caminho_unificador
            ], capture_output=True, text=True)

            if resultado.returncode != 0:
            # 🌟 LOG DE DIAGNÓSTICO DO MOTOR ORÇAMENTÁRIO:
                print("\n" + "="*50 + "\n[ERRO CRÍTICO NO MOTOR ORÇAMENTÁRIO]:\n" + resultado.stderr + "="*50 + "\n")
                raise subprocess.CalledProcessError(resultado.returncode, 'motores', 'motor_unificador.py', resultado.stderr)
            
        # Passo 2: Deflator
        if modo in ['completo', 'gerar_fator']:
            caminho_config_ano = os.path.join(DIR_PARAMETROS, 'config_ano_base.txt')
            with open(caminho_config_ano, 'w', encoding='utf-8') as f:
                f.write(str(ano_base))

            subprocess.run([sys.executable, caminho_deflator], check=True)
            if os.path.exists(caminho_config_ano):
                os.remove(caminho_config_ano)

        # Passo 3: Calculadora Final
        if modo == 'completo':
            subprocess.run([sys.executable, caminho_calculadora], check=True)

        mensagens_sucesso = {
            "completo": f"Ajuste monetário e consolidação concluídos com sucesso para o ano-base {ano_base}. Os valores foram deflacionados conforme metodologia estatística oficial.",
            "apenas_unificar": "Alinhamento estrutural e consolidação das matrizes orçamentárias executados sob o gabarito padronizado.",
            "gerar_fator": f"Geração da série de fatores de correção monetária concluída para o ano-base {ano_base}."
        }
        return jsonify({"status": "sucesso", "mensagem": mensagens_sucesso.get(modo, "Concluído.")})

    except subprocess.CalledProcessError as e:
        return jsonify({"status": "erro", "mensagem": f"Falha no módulo orçamentário: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro inesperado: {str(e)}"}), 500

@app.route('/abrir_pasta', methods=['POST'])
def abrir_pasta():
    caminho_saida = os.path.abspath(DIR_OUTPUTS)
    try:
        sistema = platform.system()
        if sistema == "Windows":
            os.startfile(caminho_saida)
        elif sistema == "Darwin":
            subprocess.run(["open", caminho_saida])
        else:
            subprocess.run(["xdg-open", caminho_saida])
        return jsonify({"status": "sucesso", "mensagem": "Diretório de resultados aberto."})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Não foi possível acessar a pasta: {str(e)}"}), 500
    
@app.route('/upload/regional', methods=['POST'])
def upload_regional():
    if 'arquivo' not in request.files:
        return jsonify({"status": "erro", "mensagem": "Arquivo ausente."}), 400
    arquivo = request.files['arquivo']
    if arquivo and arquivo_permitido(arquivo.filename):
        nome_seguro = secure_filename(arquivo.filename)
        arquivo.save(os.path.join(DIR_INPUTS_REGIONAL, nome_seguro))
        return jsonify({"status": "sucesso"})
    return jsonify({"status": "erro", "mensagem": "Extensão inválida."}), 400

@app.route('/limpar/regional/<filename>', methods=['POST'])
def remover_arquivo_regional(filename):
    try:
        nome_seguro = secure_filename(filename)
        caminho_arquivo = os.path.join(DIR_INPUTS_REGIONAL, nome_seguro)
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
            return jsonify({"status": "sucesso", "mensagem": f"Arquivo '{nome_seguro}' removido com sucesso."})
        return jsonify({"status": "erro", "mensagem": "Arquivo não encontrado."}), 404
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro ao deletar arquivo: {str(e)}"}), 500

@app.route('/processar_regional', methods=['POST'])
def processar_regional():
    try:
        dados = request.get_json() or {}
        indicador = dados.get('indicador', 'ql_tradicional')
        exportar_matrizes = dados.get('exportar_matrizes', False)
        
        # Converte o booleano para uma string interpretável pelo terminal
        exportar_str = 'sim' if exportar_matrizes else 'nao'

        print(f"[LOG] Módulo Regional. Indicador: {indicador.upper()} | Exportar Matrizes: {exportar_str.upper()}")

        caminho_motor_regional = os.path.join(PASTA_ATUAL, 'motores', 'motor_regional.py')
        
        if len([f for f in os.listdir(DIR_INPUTS_REGIONAL) if arquivo_permitido(f)]) == 0:
            return jsonify({"status": "erro", "mensagem": "Nenhum arquivo encontrado em inputs_regional."}), 400

        # Dispara o processo enviando apenas o indicador de cálculo por argumento
        resultado = subprocess.run([
            sys.executable, caminho_motor_regional, indicador, exportar_str
        ], capture_output=True, text=True)

        if resultado.returncode != 0:
            # 🌟 ISSO AQUI VAI TRAZER O ERRO REAL PARA O SEU POWERSHELL:
            print("\n" + "="*50 + "\n[ERRO CRÍTICO NO MOTOR REGIONAL]:\n" + resultado.stderr + "="*50 + "\n")
            raise subprocess.CalledProcessError(resultado.returncode, caminho_motor_regional, resultado.stderr)

        return jsonify({
            "status": "sucesso",
            "mensagem": f"Processamento concluído com sucesso."
        })

    except subprocess.CalledProcessError as e:
        return jsonify({"status": "erro", "mensagem": f"Falha na execução do motor regional: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro inesperado: {str(e)}"}), 500
if __name__ == '__main__':
    print("Hub do Economista iniciado em http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)