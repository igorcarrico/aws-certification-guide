"""
Interface Streamlit para o assistente de certificação AWS.
"""

import os
import re
import streamlit as st
from query import ask, get_vector_store, generate_quiz
from ingest import run as run_ingest
import config


def parse_quiz(quiz_text: str) -> list[dict]:
    """Parseia o texto do quiz em lista de questões estruturadas."""
    questions = []
    blocks = re.split(r"\n---\n", quiz_text.strip())

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        q = {}

        match = re.search(r"QUESTÃO \d+:\s*(.+?)(?=\nA\))", block, re.DOTALL)
        if match:
            q["question"] = match.group(1).strip()

        for letter in ["A", "B", "C", "D"]:
            match = re.search(rf"{letter}\)\s*(.+?)(?=\n[BCD]\)|\nRESPOSTA|$)", block, re.DOTALL)
            if match:
                q[letter] = match.group(1).strip()

        match = re.search(r"RESPOSTA:\s*([A-D])", block)
        if match:
            q["answer"] = match.group(1).strip()

        match = re.search(r"EXPLICAÇÃO:\s*(.+?)$", block, re.DOTALL)
        if match:
            q["explanation"] = match.group(1).strip()

        if "question" in q and "answer" in q:
            questions.append(q)

    return questions


st.set_page_config(
    page_title="AWS Certification Guide",
    page_icon="☁️",
    layout="centered",
)

st.title("☁️ AWS Certification Guide")
st.caption("Assistente de estudo para AWS Cloud Practitioner (CLF-C02) — Powered by RAG + Claude AI")

# Sidebar
with st.sidebar:
    st.header("Configuração")
    api_key_input = st.text_input(
        "🔑 API Key (Anthropic)",
        type="password",
        placeholder="sk-ant-...",
        help="Obtenha sua key em console.anthropic.com",
    )
    if api_key_input:
        config.ANTHROPIC_API_KEY = api_key_input

    if not config.ANTHROPIC_API_KEY:
        st.warning("⚠️ Insira sua API key para começar")

    st.divider()

    st.header("Sobre")
    st.markdown(
        """
        Este assistente usa **RAG** (Retrieval-Augmented Generation)
        para responder suas perguntas sobre a certificação
        **AWS Cloud Practitioner** com base em documentos oficiais da AWS.

        **Documentação incluída:**
        - AWS Cloud Practitioner Exam Guide
        - AWS Overview Whitepaper
        - AWS Well-Architected Framework
        - FAQs: EC2, S3, IAM, Lambda, RDS

        **Quer adicionar mais material?**
        1. Coloque novos PDFs em `data/docs/`
        2. Clique em "Indexar documentos"
        """
    )

    st.divider()

    if st.button("📄 Indexar documentos", use_container_width=True):
        pdf_files = [
            f for f in os.listdir(config.DATA_DIR) if f.endswith(".pdf")
        ] if os.path.exists(config.DATA_DIR) else []

        if not pdf_files:
            st.error("Nenhum PDF encontrado em data/docs/")
        else:
            with st.spinner("Indexando documentos..."):
                run_ingest()
            st.success(f"{len(pdf_files)} arquivo(s) indexado(s)!")

    st.divider()

    if os.path.exists(config.CHROMA_DIR):
        st.success("✅ Base de conhecimento pronta")
    else:
        st.warning("⚠️ Nenhum documento indexado ainda")

    st.divider()

    st.markdown(
        """
        **Domínios da prova CLF-C02:**
        - Conceitos de nuvem (24%)
        - Segurança e conformidade (30%)
        - Tecnologia e serviços (34%)
        - Cobrança e suporte (12%)
        """
    )

# Abas
tab_chat, tab_quiz = st.tabs(["💬 Chat", "📝 Quiz"])

# Aba Chat
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "suggested_prompt" not in st.session_state:
        st.session_state.suggested_prompt = None

    if st.session_state.get("messages"):
        if st.button("🗑️ Limpar conversa", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Mensagem de boas-vindas + perguntas sugeridas
    if not st.session_state.messages:
        st.markdown(
            """
            <div style="text-align: center; padding: 2rem 0 1rem 0;">
                <h3>Olá! Sou seu assistente de estudos para a certificação AWS Cloud Practitioner.</h3>
                <p style="color: gray;">Faça uma pergunta ou escolha um dos tópicos abaixo para começar.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        suggested = [
            "O que é Amazon S3 e para que serve?",
            "Quais são os domínios da prova CLF-C02?",
            "Explique o modelo de responsabilidade compartilhada da AWS",
            "Qual a diferença entre EC2 e Lambda?",
            "O que é IAM e como funciona?",
            "Quais são os modelos de preços da AWS?",
        ]

        cols = st.columns(2)
        for i, suggestion in enumerate(suggested):
            if cols[i % 2].button(suggestion, use_container_width=True):
                st.session_state.suggested_prompt = suggestion
                st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander("📄 Fontes consultadas"):
                    for source in message["sources"]:
                        st.markdown(f"- **{source['filename']}** (p. {source['page']})")

    prompt = st.chat_input("Faça uma pergunta sobre AWS Cloud Practitioner...")
    if st.session_state.suggested_prompt:
        prompt = st.session_state.suggested_prompt
        st.session_state.suggested_prompt = None

    if prompt:
        if not config.ANTHROPIC_API_KEY:
            st.error("⚠️ Insira sua API key na sidebar para começar.")
        elif not os.path.exists(config.CHROMA_DIR):
            st.error(
                "⚠️ Nenhum documento indexado. "
                "Adicione PDFs em data/docs/ e clique em 'Indexar documentos'."
            )
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Buscando nos documentos..."):
                    response, sources = ask(prompt)
                st.markdown(response)
                if sources:
                    with st.expander("📄 Fontes consultadas"):
                        for source in sources:
                            st.markdown(f"- **{source['filename']}** (p. {source['page']})")

            st.session_state.messages.append(
                {"role": "assistant", "content": response, "sources": sources}
            )
            st.rerun()

# Aba Quiz
with tab_quiz:
    st.subheader("Gerar simulado")
    st.markdown("Escolha um tópico e a quantidade de questões para gerar um simulado.")

    topic = st.selectbox(
        "Tópico",
        [
            "Conceitos gerais de Cloud Computing",
            "Amazon EC2 (Elastic Compute Cloud)",
            "Amazon S3 (Simple Storage Service)",
            "AWS IAM (Identity and Access Management)",
            "AWS Lambda e Serverless",
            "Amazon RDS (Relational Database Service)",
            "Segurança e conformidade na AWS",
            "Modelos de preços e cobrança da AWS",
            "AWS Well-Architected Framework",
        ],
    )

    num_questions = st.slider("Quantidade de questões", min_value=3, max_value=10, value=5)

    if st.button("🎯 Gerar simulado", use_container_width=True):
        if not config.ANTHROPIC_API_KEY:
            st.error("⚠️ Insira sua API key na sidebar para começar.")
        elif not os.path.exists(config.CHROMA_DIR):
            st.error("⚠️ Nenhum documento indexado ainda.")
        else:
            with st.spinner("Gerando questões..."):
                quiz = generate_quiz(topic, num_questions)
            questions = parse_quiz(quiz)
            if questions:
                st.session_state.quiz_questions = questions
                st.session_state.quiz_answers = {}

    if st.session_state.get("quiz_questions"):
        questions = st.session_state.quiz_questions
        total = len(questions)

        for i, q in enumerate(questions, 1):
            st.markdown("---")
            st.markdown(f"**Questão {i}:** {q.get('question', '')}")
            st.markdown("")
            for letter in ["A", "B", "C", "D"]:
                if letter in q:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;**{letter})** {q[letter]}")
            st.markdown("")

            col1, col2 = st.columns([1, 3])
            with col1:
                selected = st.selectbox(
                    "Sua resposta:",
                    ["—", "A", "B", "C", "D"],
                    key=f"q_{i}",
                )
                if selected != "—":
                    st.session_state.quiz_answers[i] = selected

            with st.expander("Ver resposta"):
                answer = q.get("answer", "?")
                explanation = q.get("explanation", "")
                st.success(f"**Resposta correta: {answer}) {q.get(answer, '')}**")
                if explanation:
                    st.markdown(f"**Explicação:** {explanation}")

        st.markdown("---")
        if st.button("✅ Ver minha pontuação", use_container_width=True):
            answers = st.session_state.quiz_answers
            correct = sum(
                1 for i, q in enumerate(questions, 1)
                if answers.get(i) == q.get("answer")
            )
            pct = int(correct / total * 100)
            if pct >= 70:
                st.success(f"**Você acertou {correct} de {total} questões ({pct}%)** — Aprovado!")
            else:
                st.error(f"**Você acertou {correct} de {total} questões ({pct}%)** — Continue estudando!")
