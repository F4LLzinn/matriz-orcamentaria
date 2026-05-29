======================================================================
🚀 MAESTRO ORÇAMENTÁRIO - MANUAL DE EXECUÇÃO LOCAL
======================================================================

Este sistema foi desenvolvido para automação do pipeline de dados públicos,
sendo responsável pela consolidação estrutural de matrizes orçamentárias
e aplicação de deflacionamento dinâmico baseado na série histórica do IPCA.

📋 PRÉ-REQUISITOS DO SISTEMA:
Certifique-se de possuir o ambiente Python instalado juntamente com as
bibliotecas de manipulação de dados. Para instalar as dependências:
👉 pip install -r requirements.txt

▶️ COMO INICIALIZAR O ECOSSISTEMA:
1. Execute o arquivo 'Inicar_sistema.bat' com dois cliques.
2. O servidor local Flask será iniciado em background e a interface
   operacional neumórfica abrirá automaticamente no seu navegador.

📂 ARQUITETURA DE DIRETÓRIOS:
- /inputs_orcamento: Repositório para armazenamento das matrizes brutas.
- /parametros: Diretório de persistência do indexador inflacionário (IPCA).
- /outputs_processados: Local de descarregamento das bases tratadas.

======================================================================