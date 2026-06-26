## 🛑 Estado Atual do Desenvolvimento (Parado para proteger minha sanidade mental)

Se você veio aqui esperando um app rodando 100% de forma mágica, sinto informar que a vida não é um morango...

* **O Motor Matemático (`core/`):** Até calcula as matrizes regionais (QL e CE), mas só se a base for perfeitamente estruturada e não tiver um único acento errado. Passei horas junto com a IA passando tentando entender o porque dos erros e do código não está respondendo ao que eu estava querendo, deixar o código blindado para qualquer tipo de formatação que o usuário upasse no app, mas não deu certo em algumas das poucas funções que tem.
* **A Guerra do Excel:** Depois de muita tortura psicológica, o Pandas finalmente aprendeu a salvar os arquivos sem transformar os acentos em hieróglifos no Excel em inglês, e para quem usa o Excel em português... bom, não testei então não sei se ta funcionando, pois é gerado arquivos .csv porque é mais leve e facil para o python escrever.
* **O Bug Invicto:** O principal motivo que eu perdi a paciência com esse código foi justamente na parte de criar um filtro de regiões, o que era para ser algo simples mas se tornou quase uma tarefa impossivel... o código até faz o filtro mas quando testei para a região nordeste que era justamente o que uma atividade minha da faculdade pedia, dentre as 42 mesorregiões do Nordeste, o código apenas filtrava 25 mesorregiões passei horas tentando resolver e entender o porque disso junto com a IA, mas como não sou de programação e comecei por puro hobby e tentantiva de aprender sozinho, desiste depois de horas sem resolver esse problema e decidir fazer o que precisava não mão mesmo dentro do próprio excel.

**Conclusão:** após horas de tentativa e erro, obtive mais erros do que sucessos, então decidi dar uma pausa no meu estudo em programação e voltar para o que eu ja tenho uma noção maior que é o mundo do suíte adobe, edição de video e design gráfico. 

O código está parado por puro ódio. Desisti momentaneamente da programação, e voltei para o Photoshop, Premiere e After Effects, que é onde a vida faz sentido, o resultado é visual e não tem nenhuma string maldita ou erro 500 tirando minha paz, isso que eu quis fazer algo simples e com uma das linguagens mais simples... se fosse algo realmente grande e complexo acho que nem iniciar o app eu conseguiria kkkkk, enfim essa vai ser a ultima att desse projeto e ta tudo quase que incompleto, talvez um dia eu retorne a ele, um dia... quem sabe...

---
---
---

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
