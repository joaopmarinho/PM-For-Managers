# ⛏️ Process Mining Dashboard

Dashboard interativo de **Mineração Multidimensional de Regras de Associação**, construído com Python e Streamlit. Aplica o algoritmo **Apriori** sobre logs de processo e prioriza anomalias usando a **Definição 18** da escala Likert.

---

## 📋 Sumário

- [O que o projeto faz](#-o-que-o-projeto-faz)
- [Arquitetura](#-arquitetura)
- [Estrutura de pastas](#-estrutura-de-pastas)
- [Pré-requisitos](#-pré-requisitos)
- [Como rodar](#-como-rodar)
  - [Opção 1 — Docker (recomendado)](#opção-1--docker-recomendado)
  - [Opção 2 — Local com Python](#opção-2--local-com-python)
- [Como usar o dashboard](#-como-usar-o-dashboard)
- [A lógica de mineração](#-a-lógica-de-mineração)
- [Exportação de relatórios](#-exportação-de-relatórios)
- [Variáveis de ambiente](#️-variáveis-de-ambiente)

---

## 🎯 O que o projeto faz

O dashboard recebe um arquivo CSV contendo **logs de eventos de processo** (atividades, recursos, objetos de dados, operações e categorias de anomalia) e:

1. **Armazena** os datasets em um banco SQLite — os dados persistem entre reinicializações.
2. **Explora** os dados em uma tabela interativa com paginação, ordenação e busca global.
3. **Minera** regras de associação na forma `{Antecedentes} → {Categoria de Anomalia}` usando o algoritmo Apriori (via `mlxtend`).
4. **Prioriza** as regras com a função de relevância da **Definição 18**, baseada exclusivamente na escala Likert de severidade.
5. **Exporta** um relatório do estado atual da análise nos formatos **JSON** e **CSV**.

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                    Streamlit UI                     │
│            Layout 70% esquerda / 30% direita        │
│                                                     │
│  ┌─────────────────────┐  ┌────────────────────┐   │
│  │  Gestão & Exploração│  │  Motor de Mineração│   │
│  │  ─ Upload CSV       │  │  ─ Seletor N-D     │   │
│  │  ─ Seletor contexto │  │  ─ Sliders Apriori │   │
│  │  ─ Data Explorer    │  │  ─ Resultados      │   │
│  │    (paginado)       │  │    Likert Def. 18  │   │
│  └─────────────────────┘  │  ─ Export JSON/CSV │   │
│                            └────────────────────┘   │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────▼───────────┐
        │   engine/miner.py     │  Apriori + Definição 18
        │   engine/data_utils.py│  One-Hot Encoding dinâmico
        │   engine/persistence.py│  SQLite via SQLAlchemy
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐
        │   database/storage.db │  Volume Docker persistente
        └───────────────────────┘
```

---

## 📁 Estrutura de pastas

```
mvp/
├── app.py                   # Aplicação Streamlit (UI + layout)
├── engine/
│   ├── __init__.py
│   ├── miner.py             # Algoritmo Apriori + scoring Likert
│   ├── persistence.py       # Camada de persistência SQLite/SQLAlchemy
│   └── data_utils.py        # Transformação One-Hot Encoding dinâmica
├── database/                # Diretório do banco (criado automaticamente)
│   └── storage.db           # Banco SQLite gerado na primeira execução
├── default_dataset.csv      # Dataset de exemplo (carregado automaticamente)
├── Dockerfile               # Imagem python:3.11-slim
├── docker-compose.yml       # Orquestração com volume persistente
└── requirements.txt         # Dependências Python
```

---

## 🔧 Pré-requisitos

### Para rodar com Docker
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ou Docker Engine + Compose Plugin

### Para rodar localmente
- Python **3.11+**
- `pip`

---

## 🚀 Como rodar

### Opção 1 — Docker (recomendado)

É a forma mais simples: uma linha, sem instalar nada além do Docker.

```bash
# 1. Clone ou entre na pasta do projeto
cd mvp/

# 2. Suba o container em background
docker compose up -d --build

# 3. Acesse no navegador
# http://localhost:8501
```

> **Persistência garantida:** o diretório `./database` é mapeado como volume Docker.  
> Os datasets carregados **não são perdidos** ao reiniciar o container.

Para parar:
```bash
docker compose down
```

Para ver os logs em tempo real:
```bash
docker compose logs -f
```

---

### Opção 2 — Local com Python

```bash
# 1. Entre na pasta do projeto
cd mvp/

# 2. (Opcional, mas recomendado) Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Crie o diretório do banco (se ainda não existir)
mkdir -p database

# 5. Rode a aplicação
streamlit run app.py
```

> O banco será criado automaticamente em `database/storage.db`.  
> O dataset padrão (`default_dataset.csv`) é carregado automaticamente na primeira execução.

Acesse em: **http://localhost:8501**

---

## 🖥️ Como usar o dashboard

A tela é dividida em dois painéis:

### ⬅️ Painel Esquerdo (70%) — Gestão e Exploração

| Seção | O que faz |
|---|---|
| **Ingestão de Dados** | Arraste um CSV ou clique para fazer upload. O arquivo é salvo no SQLite. |
| **Contexto Ativo** | Dropdown para alternar entre datasets já armazenados. O botão 🗑️ remove o dataset selecionado. |
| **Data Explorer** | Tabela interativa com todas as linhas do dataset ativo. |
| **Filtro global** | Busca em tempo real em qualquer coluna. |
| **Paginação** | Navega pelas páginas com os botões ◀ ▶. |

#### Formato esperado do CSV

O arquivo deve conter ao menos a coluna `Category` (consequente fixo). Exemplo:

```
Activity,Resource,Data Object,Operation,Category
Publicar solucao,re6,Gestao,read,Illegal data access
Executar teste,re7,Codigo,read,Illegal data access
Contagem de ponto de funcao,re7,,,Prohibited activity
```

Colunas com valores vazios são preenchidas automaticamente com `"None"`.

---

### ➡️ Painel Direito (30%) — Motor de Mineração

**1. Colunas Antecedentes (N-D)**  
Selecione uma ou mais colunas para compor os antecedentes das regras.  
A coluna `Category` é sempre o consequente (fixo).  

Exemplo com 2 dimensões:  
`{Activity, Data Object}` → `{Category}`

**2. Parâmetros de Mineração**
- **Suporte Mínimo** — frequência mínima do itemset no dataset (default: `0.05` = 5%)
- **Confiança Mínima** — força preditiva mínima da regra (default: `0.80` = 80%)

**3. Executar Mineração**  
Clique em **▶ Executar Mineração** para rodar o Apriori e ver os resultados.

**4. Painel de Relevância**  
As regras são exibidas ordenadas por score de relevância (`rel`), com badges coloridos por severidade:

| Badge | Categoria | Peso Likert |
|---|---|---|
| 🔴 Vermelho | Illegal / Prohibited | 5 |
| 🟡 Amarelo | Ignored | 3 |
| 🔵 Azul | Unexpected | 2 |

---

## 🧮 A lógica de mineração

### Algoritmo Apriori

Cada linha do CSV é tratada como uma **transação única**. O processo é:

```
CSV → fillna("None") → One-Hot Encoding → Apriori → Filtro de regras → Scoring
```

O **One-Hot Encoding** transforma cada coluna em colunas binárias no formato `Coluna=Valor`:

```
Activity=Publicar solucao | Data Object=Gestao → Category=Illegal data access
```

O filtro garante que:
- Os **antecedentes** contêm itens das colunas selecionadas.
- O **consequente** é sempre um valor da coluna `Category`.

### Priorização — Definição 18 (Likert)

A relevância de cada regra é calculada como:

$$rel(raf) = \sum_{x \in X}(w_{att}(x) + w_{val}(x)) + (w_{att}(y) + w_{val}(y))$$

Onde:
- $w_{att}$ = peso do **atributo** (ex: `Category = 5`, `Data Object = 3`, demais = `1`)
- $w_{val}$ = peso do **valor** específico (ex: `Illegal data access = 5`, `Ignored = 3`, `Unexpected = 2`)

| Atributo | $w_{att}$ |
|---|---|
| Activity | 1 |
| Resource | 1 |
| Data Object | 3 |
| Operation | 1 |
| Category | 5 |

| Valor | $w_{val}$ |
|---|---|
| Illegal activity / Illegal data access | 5 |
| Prohibited activity / Prohibited data access | 5 |
| Ignored mandatory activity / data access | 3 |
| Unexpected activity / data access | 2 |
| Codigo, Requisito (Data Object) | 4 |
| PF (Data Object) | 2 |
| qualquer outro | 1 |

---

## 📥 Exportação de relatórios

Após executar a mineração, dois botões de download ficam disponíveis:

- **⬇️ JSON** — snapshot completo com metadados, configuração e regras
- **⬇️ CSV** — tabela de regras para importação em Excel/BI

Estrutura do JSON exportado:

```json
{
  "metadata": {
    "dataset": "report_default.csv",
    "generated_at": "2026-05-15T15:30:00"
  },
  "config": {
    "antecedent_columns": ["Activity", "Data Object"],
    "min_support": 0.05,
    "min_confidence": 0.80
  },
  "stats": {
    "itemsets_count": 38,
    "rules_total": 30,
    "rules_filtered": 5
  },
  "rules": [
    {
      "Antecedentes": "Activity: Publicar solucao | Data Object: Gestao",
      "Categoria da Anomalia": "Illegal data access",
      "Suporte": 0.1212,
      "Confiança": 1.0,
      "Relevância (rel)": 16
    }
  ]
}
```

---

## ⚙️ Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `DB_PATH` | `/app/database/storage.db` | Caminho do banco SQLite |
| `STREAMLIT_SERVER_PORT` | `8501` | Porta do servidor |
| `STREAMLIT_SERVER_ADDRESS` | `0.0.0.0` | Endereço de bind |

Para alterar a porta no Docker, edite `docker-compose.yml`:

```yaml
ports:
  - "9000:8501"   # acesso em localhost:9000
```

---

## 🛠️ Stack

| Tecnologia | Uso |
|---|---|
| [Python 3.11](https://python.org) | Linguagem base |
| [Streamlit](https://streamlit.io) | Interface web |
| [mlxtend](http://rasbt.github.io/mlxtend/) | Algoritmo Apriori |
| [pandas](https://pandas.pydata.org) | Manipulação de dados |
| [SQLAlchemy](https://sqlalchemy.org) | ORM / SQLite |
| [Docker](https://docker.com) | Containerização |
# PM-For-Managers
