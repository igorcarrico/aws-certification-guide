"""
Lógica de RAG: busca documentos relevantes e gera resposta com Claude.
"""

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from anthropic import Anthropic

import config

SYSTEM_PROMPT = """Você é um assistente especializado em preparação para a certificação AWS Cloud Practitioner (CLF-C02).

Seu papel é:
- Responder perguntas sobre os tópicos da certificação usando APENAS o contexto fornecido
- Explicar conceitos AWS de forma clara e didática
- Quando relevante, mencionar qual domínio da prova o tópico pertence
- Se a resposta não estiver no contexto fornecido, diga claramente que não encontrou essa informação nos documentos disponíveis

Domínios da prova CLF-C02:
1. Conceitos de nuvem (24%)
2. Segurança e conformidade (30%)
3. Tecnologia e serviços de nuvem (34%)
4. Cobrança, preços e suporte (12%)

Responda sempre em português brasileiro."""


def get_vector_store():
    """Carrega o vector store existente."""
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return Chroma(persist_directory=config.CHROMA_DIR, embedding_function=embeddings)


def retrieve_context(vector_store, question: str) -> str:
    """Busca os chunks mais relevantes para a pergunta."""
    results = vector_store.similarity_search(question, k=config.TOP_K)

    if not results:
        return "Nenhum documento relevante encontrado."

    context_parts = []
    for i, doc in enumerate(results, 1):
        source = doc.metadata.get("source", "desconhecido")
        page = doc.metadata.get("page", "?")
        context_parts.append(
            f"[Documento {i} - {source} (p.{page})]\n{doc.page_content}"
        )

    return "\n\n---\n\n".join(context_parts)


def generate_answer(question: str, context: str) -> str:
    """Gera resposta usando Claude com o contexto recuperado."""
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    user_message = f"""Contexto dos documentos de estudo:

{context}

---

Pergunta do estudante: {question}"""

    response = client.messages.create(
        model=config.MODEL_NAME,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text


def ask(question: str) -> str:
    """Pipeline completo: busca contexto e gera resposta."""
    vector_store = get_vector_store()
    context = retrieve_context(vector_store, question)
    answer = generate_answer(question, context)
    return answer
