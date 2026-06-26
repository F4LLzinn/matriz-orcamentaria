import os
import platform
import subprocess
from flask import Flask, render_template, jsonify

from utils.arquivos import inicializar_sistema_arquivos, DIR_OUTPUTS
from rotas.rota_orcamento import blueprint_orcamento
from rotas.rota_regional import blueprint_regional

app = Flask(__name__)

# Garante a existência física de todas as pastas essenciais no HD
inicializar_sistema_arquivos()

# Registra os módulos isolados de rotas (Blueprints)
app.register_blueprint(blueprint_orcamento)
app.register_blueprint(blueprint_regional)

@app.route('/')
def menu_principal():
    return render_template('menu.html')

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
        return jsonify({"status": "erro", "mensagem": f"Não foi possível acessar a pasta: {str(e)}"})

if __name__ == '__main__':
    print("\n\033[1;35m[PMQA :: ENGINE V2]\033[0m Servidor unificado ativado com sucesso.")
    print("\033[35m[URL]\033[0m Acesse o Hub em: http://127.0.0.1:5000\n")
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)