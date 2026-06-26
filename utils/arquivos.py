import os

PASTA_UTILS = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
RAIZ_PROJETO = os.path.abspath(os.path.join(PASTA_UTILS, '..'))

DIR_INPUTS_ORCAMENTO = os.path.join(RAIZ_PROJETO, 'inputs_orcamento')
DIR_INPUTS_REGIONAL  = os.path.join(RAIZ_PROJETO, 'inputs_regional')
DIR_PARAMETROS       = os.path.join(RAIZ_PROJETO, 'parametros')
DIR_OUTPUTS          = os.path.join(RAIZ_PROJETO, 'outputs_processados')

EXTENSOES_PERMITIDAS = {'.csv', '.xlsx', '.xls', '.shp', '.shx', '.dbf', '.geojson'}

def inicializar_sistema_arquivos():
    pastas = [DIR_INPUTS_ORCAMENTO, DIR_INPUTS_REGIONAL, DIR_PARAMETROS, DIR_OUTPUTS]
    for pasta in pastas:
        os.makedirs(pasta, exist_ok=True)

def validar_extensao(filename):
    _, ext = os.path.splitext(filename.lower())
    return ext in EXTENSOES_PERMITIDAS