"""
Pipeline de ingestão de documentos.
Carrega PDFs da pasta data/docs, divide em chunks e armazena no ChromaDB.
"""

import os
import sys

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

import config


def load_documents():
    """Carrega todos os PDFs da pasta data/docs."""
    if not os.path.exists(config.DATA_DIR):
        print(f"Pasta {config.DATA_DIR} não encontrada.")
        sys.exit(1)

    pdf_files = [f for f in os.listdir(config.DATA_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"Nenhum PDF encontrado em {config.DATA_DIR}")
        print("Adicione seus PDFs de estudo nessa pasta e rode novamente.")
        sys.exit(1)

    loader = DirectoryLoader(
        config.DATA_DIR,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True,
    )
    documents = loader.load()
    print(f"{len(documents)} páginas carregadas de {len(pdf_files)} arquivo(s).")
    return documents


def split_documents(documents):
    """Divide documentos em chunks menores."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"{len(chunks)} chunks criados.")
    return chunks


def create_vector_store(chunks):
    """Cria o vector store no ChromaDB com os chunks."""
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
    )

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=config.CHROMA_DIR,
    )
    print(f"Vector store criado em {config.CHROMA_DIR}")
    return vector_store


def run():
    """Executa o pipeline completo de ingestão."""
    print("=" * 50)
    print("Iniciando ingestão de documentos...")
    print("=" * 50)

    documents = load_documents()
    chunks = split_documents(documents)
    create_vector_store(chunks)

    print("=" * 50)
    print("Ingestão concluída com sucesso!")
    print("=" * 50)


if __name__ == "__main__":
    run()
