
import os
import logging
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class RAGPipeline:
    def __init__(self, index_path: str = "rag/faiss_index"):
        self.index_path = index_path
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vector_store = None
        self._load_vector_store()
        
        # Initialize LLM (same config as ChatAgent)
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-flash-latest",
                google_api_key=google_api_key,
                temperature=0.3, # Lower temperature for factual Q&A
                max_retries=2,
                convert_system_message_to_human=True
            )
        else:
            logger.warning("GOOGLE_API_KEY not found. RAG generation will fail.")
            self.llm = None

    def _load_vector_store(self):
        """Loads existing FAISS index if available."""
        if os.path.exists(self.index_path):
            try:
                self.vector_store = FAISS.load_local(
                    self.index_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True # Local file, safe
                )
                logger.info(f"Loaded existing vector store from {self.index_path}")
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")
        else:
            logger.info("No existing vector store found. A new one will be created upon ingestion.")

    def ingest_documents(self, file_paths: List[str]):
        """
        Loads documents, splits them, and updates the vector store.
        Supported formats: .pdf, .txt, .docx
        """
        all_docs = []
        for path in file_paths:
            if not os.path.exists(path):
                logger.warning(f"File not found: {path}")
                continue
            
            try:
                if path.lower().endswith(".pdf"):
                    loader = PyPDFLoader(path)
                elif path.lower().endswith(".docx"):
                    loader = Docx2txtLoader(path)
                elif path.lower().endswith(".txt"):
                    loader = TextLoader(path, encoding='utf-8')
                else:
                    logger.warning(f"Unsupported file type: {path}")
                    continue
                
                docs = loader.load()
                all_docs.extend(docs)
                logger.info(f"Loaded {len(docs)} pages/chunks from {path}")
            except Exception as e:
                logger.error(f"Error loading {path}: {e}")

        if not all_docs:
            logger.warning("No documents loaded.")
            return

        # Split text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        splits = text_splitter.split_documents(all_docs)
        logger.info(f"Created {len(splits)} chunks from loaded documents.")

        # Create or Update Vector Store
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(splits, self.embeddings)
        else:
            self.vector_store.add_documents(splits)

        # Save index
        try:
            self.vector_store.save_local(self.index_path)
            logger.info(f"Vector store saved to {self.index_path}")
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")

    def answer_from_docs(self, query: str) -> str:
        """
        Retrieves relevant context and uses LLM to answer the query.
        """
        if self.vector_store is None:
            return "Knowledge base is empty. Please upload documents first."
        
        if self.llm is None:
            return "LLM not configured. Cannot generate answer."

        try:
            # 1. Retrieve relevat documents
            # k=4 is a good default
            docs = self.vector_store.similarity_search(query, k=4)
            
            # 2. Construct context string
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # 3. Construct Prompt
            prompt_template = """Answer the question based only on the following context:
{context}

Question: {question}
"""
            prompt = ChatPromptTemplate.from_template(prompt_template)
            
            # 4. Generate Answer
            chain = prompt | self.llm | StrOutputParser()
            response = chain.invoke({"context": context, "question": query})
            
            return response
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            return f"Error answering query: {e}"

# Singleton instance
rag_pipeline = RAGPipeline()
