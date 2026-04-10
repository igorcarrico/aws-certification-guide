"""
Interface Streamlit para o assistente de certificação AWS.
"""

import os
import streamlit as st
from query import ask
from ingest import run as run_ingest
import config


st.set_page_config(
    page_title="AWS Certification Guide",
    page_icon="☁️",
    layout="centered",
)

st.title("☁️ AWS Certification Guide")
st.caption("Assistente de estudo para AWS Cloud Practitioner (CLF-C02) — Powered by RAG + Claude AI")

# Sidebar
with st.sidebar:
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

# Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Faça uma pergunta sobre AWS Cloud Practitioner..."):
    if not os.path.exists(config.CHROMA_DIR):
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
                response = ask(prompt)
            st.markdown(response)

        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )
