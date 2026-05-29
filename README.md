# 📊 Plataforma de Métodos Quantitativos Aplicados (PMQA)

A **PMQA** é um ecossistema integrado e modular desenvolvido para a automação de pipelines de dados públicos, análise econométrica regional e consolidação orçamentária. O sistema unifica ferramentas analíticas sob uma arquitetura Flask estável e uma interface neumórfica minimalista.

---

### 🚧 Status do Projeto: Em Desenvolvimento Ativo
> **Aviso Importante:** Este sistema encontra-se em estágio de desenvolvimento (Alpha). Algumas funcionalidades de cálculo avançado estão sendo implementadas e calibradas de forma progressiva.

---

## ⚙️ Módulos Operacionais

### 1. Orçamento Público (Consolidação & Deflacionamento)
* **Unificação Estrutural:** Agregação e higienização automática de matrizes históricas brutas extraídas do Siga Brasil.
* **Correção Monetária Dinâmica:** Extração e aplicação do índice de deflacionamento baseado na série histórica oficial do IPCA (Ipeadata).
* **Outputs customizados:** Geração de visões analíticas paralelas (lado a lado para ferramentas de BI e dados deflacionados puros).

### 2. Análise Econômica Regional (Mercado de Trabalho)
* **Quociente Locacional (QL Tradicional):** Identificação de especializações produtivas locais através de duplo fechamento.
* **QL Leave-One-Out (LOO):** Ajuste com correção de escala para eliminação de distorções em regiões de forte peso econômico.
* **Coeficiente de Especialização (CE):** Mensuração sintética do desvio estrutural de emprego das localidades em relação ao comportamento macro nacional.

---

## 🛑 Limitações Atuais & Erros Conhecidos

* ⚠️ **Módulo Shift-Share (Análise Estrutural-Diferencial):** A opção está visível no painel regional, mas **ainda não está funcional**. O algoritmo completo exige o processamento de microdados emparelhados de dois períodos temporais distintos e está em fase de modelagem lógica. Selecionar esta opção resultará em uma interrupção intencional do motor traseiro.

---

## 🗺️ Próximos Passos & Roadmap de Atualizações

- [ ] **Implementação do Shift-Share:** Desenvolvimento do pipeline de dados bifásico para cálculo dos efeitos nacional, estrutural e locacional.
- [ ] **Repaginada Completa da UI/UX:** Atualização estrutural dos componentes neumórficos, otimização do fluxo de navegação entre módulos e refinamento do feedback visual de processamento para melhorar drasticamente a experiência do usuário.
- [ ] **Expansão de Indicadores:** Inclusão de rotinas automáticas para o Coeficiente de Reestruturação (Cr) e Coeficiente de Diversificação (Cd).

---

## 📂 Arquitetura de Diretórios Estrutural

O ecossistema organiza de forma autônoma as seguintes dependências físicas no disco:
* `/inputs_orcamento`: Destinado ao armazenamento das matrizes brutas de despesas e receitas.
* `/inputs_regional`: Repositório para recepção das planilhas de emprego territorial (MTE/CAGED).
* `/motores`: Centralização dos scripts puros de cálculo em Python (`motor_unificador.py`, `motor_deflator.py`, `motor_calculadora.py` e `motor_regional.py`).
* `/parametros`: Diretório de persistência para indexadores e arquivos de configuração temporários (IPCA/Ipeadata).
* `/outputs_processados`: Local unificado para o descarregamento das bases tratadas e matrizes geradas.

---

## 🚀 Como Inicializar Localmente

1. **Instalar Dependências:** Garanta que possui o ambiente Python instalado e execute a instalação dos pacotes necessários:
   ```bash
   pip install -r requirements.txt