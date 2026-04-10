# AWS Certification Guide

Assistente de estudo para a certificação **AWS Cloud Practitioner (CLF-C02)** utilizando **RAG** (Retrieval-Augmented Generation) + **Claude AI**.

O sistema carrega documentos de estudo (PDFs, whitepapers, guias), indexa em um vector store e responde perguntas com base no conteúdo real dos documentos.

## Como funciona

```
Documentos (PDF) → Chunking → Embeddings → Vector Store (ChromaDB)
                                                    ↓
Pergunta do usuário → Busca por similaridade → Contexto relevante
                                                    ↓
                                        Claude AI gera a resposta
```

## Tech Stack

- **Python** — linguagem principal
- **LangChain** — pipeline de RAG
- **ChromaDB** — vector store local
- **Claude AI (Anthropic)** — geração de respostas
- **Streamlit** — interface web
- **Sentence Transformers** — embeddings (all-MiniLM-L6-v2)

## Pré-requisitos

- Python 3.10+
- API Key da [Anthropic](https://console.anthropic.com)

## Instalação

```bash
git clone https://github.com/igorcarrico/aws-certification-guide.git
cd aws-certification-guide

python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

pip install -r requirements.txt

cp .env.example .env
# Edite o arquivo .env com sua API key
```

## Uso

### 1. Adicione seus documentos de estudo

Coloque seus PDFs na pasta `data/docs/`.

### 2. Indexe os documentos

```bash
python ingest.py
```

### 3. Inicie a aplicação

```bash
streamlit run app.py
```

Acesse `http://localhost:8501` no navegador.

## Estrutura do Projeto

```
aws-certification-guide/
├── app.py              # Interface Streamlit
├── config.py           # Configurações
├── ingest.py           # Pipeline de ingestão de dados
├── query.py            # Lógica RAG (busca + geração)
├── requirements.txt    # Dependências
├── .env.example        # Exemplo de variáveis de ambiente
└── data/
    └── docs/           # PDFs de estudo (não versionados)
```

## Domínios da Prova CLF-C02

| Domínio | Peso |
|---------|------|
| Conceitos de nuvem | 24% |
| Segurança e conformidade | 30% |
| Tecnologia e serviços de nuvem | 34% |
| Cobrança, preços e suporte | 12% |

## Roadmap

- [x] Pipeline RAG básico com PDFs
- [x] Interface Streamlit
- [ ] Suporte a múltiplas certificações (Solutions Architect, Azure, GCP)
- [ ] Modo quiz (geração de perguntas de simulado)
- [ ] Histórico de conversas persistente
- [ ] Deploy com Docker

## Licença

MIT
