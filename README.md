# ⏳ Kairós • Econometric Ecosystem (v2.0)

O **Kairós** é um ecossistema integrado e modular desenvolvido para a automação de pipelines de dados públicos, análise econométrica regional e consolidação orçamentária. O sistema unifica ferramentas analíticas sob uma arquitetura Flask estável e uma interface NeuMorphism.

---

### 🚧 Status do Projeto: Em Desenvolvimento Ativo (mas não sei se vou finalizar)
> **Aviso Importante:** Este sistema encontra-se em estágio de desenvolvimento (Pré-historicamente Alpha). Algumas funcionalidades de cálculo avançado estão sendo implementadas e calibradas de forma progressiva. Com base no meu ânimo...

---

## ⚙️ Módulos Operacionais

### 1. Orçamento Público (Consolidação & Deflacionamento)
* **Unificação Estrutural:** Agregação e higienização automática de matrizes históricas brutas extraídas do Siga Brasil.
* **Correção Monetária Dinâmica:** Extração e aplicação do índice de deflacionamento baseado na série histórica oficial do IPCA (Ipeadata).
* **Outputs customizados:** Geração de visões analíticas paralelas (lado a lado para ferramentas de BI e dados deflacionados puros).

### 2. Análise Econômica Regional & Urbana (Mercado de Trabalho)
* **Quociente Locacional (QL Tradicional):** Identificação de especializações produtivas locais através de duplo fechamento.
* **QL Leave-One-Out (LOO):** Ajuste com correção de escala para eliminação de distorções em regiões de forte peso econômico.
* **Coeficiente de Especialização (CE):** Mensuração sintética do desvio estrutural de emprego das localidades em relação ao comportamento macro nacional.
* **[Experimental] Análise de Dependência Espacial:** Motor configurado para acoplamento de Shapefiles do IBGE, calculando o Índice de Moran Global e Local (LISA) para a Indústria de Transformação.
### 2. Análise Econômica Regional (Mercado de Trabalho)
* **Quociente Locacional (QL Tradicional):** Identificação de especializações produtivas locais através de duplo fechamento.
* **QL Leave-One-Out (LOO):** Ajuste com correção de escala para eliminação de distorções em regiões de forte peso econômico.
* **Coeficiente de Especialização (CE):** Mensuração sintética do desvio estrutural de emprego das localidades em relação ao comportamento macro nacional.

---

## 🛑 Limitações Atuais & Erros Conhecidos

* ⚠️ **Módulo Shift-Share (Análise Estrutural-Diferencial):** A opção está foi removida temporariamente do painel regional, mas **ainda será implementada**. O algoritmo completo exige o processamento de microdados emparelhados de dois períodos temporais distintos e está em fase de modelagem lógica. Então aguardem novas atualizações um dia.

---

## 🗺️ Próximos Passos & Roadmap de Atualizações

- [ ] **Implementação do Shift-Share:** Desenvolvimento do pipeline de dados bifásico para cálculo dos efeitos nacional, estrutural e locacional.
- [ ] **Repaginada Completa da UI/UX:** Refinamento no estilo da interface, otimização do fluxo de navegação entre módulos e feedback de processamento no padrão que ainda irei definir, estou na duvida de um NeuMophirsm ou LiquidGlass ou algum outro estilo talvez mais simples... quem sabe uma interface retro? talvez.
- [ ] **Expansão de Indicadores:** Inclusão de rotinas automáticas para o Coeficiente de Reestruturação (Cr) e Coeficiente de Diversificação (Cd).
- [ ] **Adição de Opção de Visualização Dinâmica:** Incluir a opção de gerar gráficos interativos prontos para uma apresentação visual ou inclusão em um artigo.
- [ ] **Compilar em um único APP:** Ao final talvez eu compile o código em um app executável para não rodar em um terminal e uma aba de navegador, ou talvez upe o código em uma host e deixe ele acessível de forma online. Ainda vou pensar.

---

## 📂 Arquitetura de Diretórios Estrutural (v2.0 Core)

O ecossistema organiza de forma autônoma as seguintes dependências físicas no disco:
* `/core`: Motores analíticos isolados por escopo de negócio (Orçamento e Economia Regional).
* `/rotas`: Controladores desacoplados utilizando Flask Blueprints para garantir a escalabilidade.
* `/utils`: Utilitários globais de persistência e verificação de integridade de arquivos.
* `/templates` e `/static`: Estrutura semântica e visual da interface NeuMorphism.

---

## 🚀 Como Inicializar Localmente

1. **Instalar Dependências:** Garanta que possui o ambiente Python instalado e execute a instalação dos pacotes necessários:
   ```bash
   pip install flask pandas werkzeug openpyxl scikit-learn geopandas libpysal esda shapely scipy pyproj pyogrio
