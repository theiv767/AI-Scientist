# Plano de Execução: Setup do Experimento no AI-Scientist

## Introdução
Este plano de execução detalha a nova etapa de geração de um código inicial dentro do framework AI-Scientist. Com essa melhoria, o framework passa a não depender de um código preexistente, podendo criá-lo com base em prompts definidos pelo usuário.

## Legenda
- `<x>` → Recurso já existente no framework.
- `<<x>>` → Recurso que precisa ser inserido pelo usuário antes da execução.
- `<<<x>>>` → Resultado gerado durante a execução do `setup_experiment.py`.

## Variáveis Iniciais
```python
lista_experiment_falhas = []
lista_plot_falhas = []
```

## Etapas do Plano de Execução

### 1️⃣ Verificação da Existência de um Experimento
**Parâmetros:** `<code>`  
**Objetivos:**
- Identificar se `experiment.py` já possui uma implementação.
- Se existir, encerrar `setup_experiment` e iniciar `generate_ideas`.
- Caso contrário, prosseguir com a criação do experimento.

**Resultados:**
- `return Boolean`

---

### 2️⃣ Obtenção de Métricas Relevantes
**Parâmetros:** `<idea_system_prompt>`, `<task_description>`, `<<dados_disponíveis>>`  
**Objetivos:**
- Listar métricas relevantes para os objetivos da tarefa.

**Resultados:**
- `return <<<lista_metricas>>>`

---

### 3️⃣ Filtragem de Métricas Viáveis
**Parâmetros:** `<msg_history>`, `<<<lista_metricas>>>`, `<<dados_disponíveis>>`  
**Objetivos:**
- Selecionar apenas as métricas que podem ser utilizadas de forma realista.

**Resultados:**
- `return <<<lista_metricas>>>` (após filtragem)

---

### 4️⃣ Geração do `experiment.py` Base
**Parâmetros:** `<code>`, `<msg_history>`, `<idea_system_prompt>`, `<task_description>`, `<<dados_disponíveis>>`, `<<<lista_metricas>>>`, `<lista_experiment_falhas>`  
**Objetivos:**
- Criar um código inicial para `experiment.py`, seguindo as métricas definidas.
- Garantir que o código seja diferente dos listados em `<lista_experiment_falhas>`.

**Resultados:**
- `<code>` atualizado com a implementação inicial do experimento.

---

### 5️⃣ Execução do `experiment.py`
**Parâmetros:** Nenhum  
**Objetivos:**
- Rodar o experimento para obter resultados iniciais.

**Resultados:**
- Criação do arquivo `<final_info.json>`.

**Tratamento de Erros:**
1. Tentar corrigir falhas automaticamente.
2. Caso não seja possível, adicionar a tentativa falha em `<lista_experiment_falhas>` e repetir a etapa **4️⃣**.

---

### 6️⃣ Geração do `plot.py`
**Parâmetros:** `<final_info.json>`, `<idea_system_prompt>`, `<task_description>`  
**Objetivos:**
- Criar um script `plot.py` para visualização dos resultados.
- Implementar gráficos, tabelas e outras formas de análise.

**Resultados:**
- `<plot>` recebe um código base.

---

### 7️⃣ Execução do `plot.py`
**Parâmetros:** Nenhum  
**Objetivos:**
- Rodar `plot.py` para gerar visualizações dos resultados.

**Resultados:**
- Arquivos gerados para análise visual.

**Tratamento de Erros:**
1. Tentar corrigir falhas automaticamente.
2. Se a correção falhar, adicionar a tentativa a `<lista_plot_falhas>` e repetir a etapa **6️⃣**.

---

## 🔜 Próximo Passo: `generate_ideas`

