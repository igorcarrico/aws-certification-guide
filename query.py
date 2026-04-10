"""
Lógica de RAG: busca documentos relevantes e gera resposta com Claude.
"""

import os
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


def translate_query(question: str) -> str:
    """Traduz a pergunta para inglês para melhorar a busca nos docs."""
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=config.MODEL_NAME,
        max_tokens=256,
        system="Translate the following question to English. Return ONLY the translated text, nothing else.",
        messages=[{"role": "user", "content": question}],
    )
    return response.content[0].text


def retrieve_context(vector_store, question: str) -> tuple[str, list[dict]]:
    """Busca os chunks mais relevantes para a pergunta."""
    english_query = translate_query(question)
    results = vector_store.similarity_search(english_query, k=config.TOP_K)

    if not results:
        return "Nenhum documento relevante encontrado.", []

    context_parts = []
    sources = []
    seen = set()

    for i, doc in enumerate(results, 1):
        source = doc.metadata.get("source", "desconhecido")
        page = doc.metadata.get("page", "?")
        context_parts.append(
            f"[Documento {i} - {source} (p.{page})]\n{doc.page_content}"
        )
        filename = os.path.basename(source)
        if filename not in seen:
            seen.add(filename)
            sources.append({"filename": filename, "page": page})

    return "\n\n---\n\n".join(context_parts), sources


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


def ask(question: str) -> tuple[str, list[dict]]:
    """Pipeline completo: busca contexto e gera resposta com fontes."""
    vector_store = get_vector_store()
    context, sources = retrieve_context(vector_store, question)
    answer = generate_answer(question, context)
    return answer, sources


QUIZ_PROMPT = """Você é um gerador de questões de simulado para a certificação AWS Cloud Practitioner (CLF-C02).

Com base no contexto fornecido, gere exatamente {num_questions} questões de múltipla escolha.

Regras:
- Cada questão deve ter 4 alternativas (A, B, C, D)
- Apenas uma alternativa correta por questão
- As questões devem ser baseadas APENAS no contexto fornecido
- Nível de dificuldade similar à prova real
- Responda em português brasileiro

Use EXATAMENTE este formato para cada questão:

QUESTÃO 1: [texto da pergunta]
A) [alternativa A]
B) [alternativa B]
C) [alternativa C]
D) [alternativa D]
RESPOSTA: [letra correta]
EXPLICAÇÃO: [breve explicação de por que a resposta está correta]

---"""


def generate_quiz(topic: str, num_questions: int = 5) -> str:
    """Gera questões de simulado sobre um tópico."""
    vector_store = get_vector_store()
    context, _ = retrieve_context(vector_store, topic)

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    user_message = f"""Contexto dos documentos de estudo:

{context}

---

Gere {num_questions} questões de simulado sobre: {topic}"""

    response = client.messages.create(
        model=config.MODEL_NAME,
        max_tokens=4096,
        system=QUIZ_PROMPT.format(num_questions=num_questions),
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text
