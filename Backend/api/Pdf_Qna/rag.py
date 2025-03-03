import os
from typing import List, Dict, Any, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_mistralai import ChatMistralAI
from langchain_chroma import Chroma
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
import shutil
from pathlib import Path
import uuid

class DocumentProcessor:
    """
    Handles document loading and text splitting
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the document processor
        
        Args:
            chunk_size: Maximum size of each text chunk
            chunk_overlap: Overlap between consecutive chunks
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap
        )
    
    def load_pdf(self, file_path: str) -> List[Document]:
        """
        Load documents from a PDF file
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of document objects
        """
        loader = PyPDFLoader(file_path)
        return loader.load()
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of split document chunks
        """
        return self.text_splitter.split_documents(documents)


class EmbeddingEngine:
    """
    Handles document embedding and vector store operations
    """
    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """
        Initialize the embedding engine
        
        Args:
            model_name: Name of the HuggingFace embedding model to use
        """
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        self.vectorstore = None
        self.model_name = model_name
        self.documents = []  # Store the original documents
    
    def create_vectorstore(self, documents: List[Document]) -> None:
        """
        Create a vector store from documents
        
        Args:
            documents: List of documents to embed
        """
        self.documents = documents  # Store the original documents
        self.vectorstore = Chroma.from_documents(documents=documents, embedding=self.embeddings)
    
    def save_vectorstore(self, directory: str) -> None:
        """
        Save the vector store to a local directory
        
        Args:
            directory: Directory path to save the vector store
        """
        if self.vectorstore is None or not self.documents:
            raise ValueError("Vector store not created yet or no documents available. Call create_vectorstore first.")
            
        # Create directory if it doesn't exist
        directory_path = Path(directory)
        directory_path.mkdir(parents=True, exist_ok=True)
        
        # If directory already has data, we'll clean it to prevent conflicts
        if directory_path.exists():
            for item in directory_path.glob("*"):
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        
        # Create a new persistent Chroma instance with the same documents
        # The persist_directory parameter will make this automatically persistent
        persistent_vectorstore = Chroma.from_documents(
            documents=self.documents,
            embedding=self.embeddings,
            persist_directory=str(directory_path)
        )
        
        # Update our reference to the persistent store
        self.vectorstore = persistent_vectorstore
        
        print(f"Vector store saved to {directory_path}")
    
    def load_vectorstore(self, directory: str) -> None:
        """
        Load a vector store from a local directory
        
        Args:
            directory: Directory path where the vector store is saved
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            raise ValueError(f"Directory {directory_path} does not exist")
        
        # Load the Chroma vector store from the directory
        self.vectorstore = Chroma(
            persist_directory=str(directory_path),
            embedding_function=self.embeddings
        )
        print(f"Vector store loaded from {directory_path}")
    
    def get_retriever(self):
        """
        Get a retriever from the vector store
        
        Returns:
            Document retriever
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not created yet. Call create_vectorstore or load_vectorstore first.")
        return self.vectorstore.as_retriever()


class LLMEngine:
    """
    Handles LLM interactions and chain creation
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-large-latest"):
        """
        Initialize the LLM engine
        
        Args:
            api_key: Mistral API key (if not provided, will use environment variable)
            model: Name of the Mistral model to use
        """
        if api_key:
            os.environ["MISTRAL_API_KEY"] = api_key
        
        self.llm = ChatMistralAI(model=model)
    
    def create_qa_chain(self, system_prompt: str):
        """
        Create a question answering chain
        
        Args:
            system_prompt: System prompt template
            
        Returns:
            Question answering chain
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )
        return create_stuff_documents_chain(self.llm, prompt)


class RAGSystem:
    """
    Main RAG system that coordinates document processing, embedding, and LLM components
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "mistral-large-latest",
        embedding_model: str = "sentence-transformers/all-mpnet-base-v2",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize the RAG system
        
        Args:
            api_key: Mistral API key
            model: Name of the Mistral model
            embedding_model: Name of the embedding model
            chunk_size: Maximum size of each text chunk
            chunk_overlap: Overlap between consecutive chunks
        """
        self.document_processor = DocumentProcessor(chunk_size, chunk_overlap)
        self.embedding_engine = EmbeddingEngine(embedding_model)
        self.llm_engine = LLMEngine(api_key, model)
        
        self.default_system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "{context}"
        )
        
        self.rag_chain = None
    
    def ingest_pdf(self, file_path: str) -> None:
        """
        Ingest a PDF file into the RAG system
        
        Args:
            file_path: Path to the PDF file
        """
        documents = self.document_processor.load_pdf(file_path)
        splits = self.document_processor.split_documents(documents)
        self.embedding_engine.create_vectorstore(splits)
    
    def save_vectorstore(self, directory: str) -> None:
        """
        Save the vector store to a local directory
        
        Args:
            directory: Directory path to save the vector store
        """
        self.embedding_engine.save_vectorstore(directory)
    
    def load_vectorstore(self, directory: str) -> None:
        """
        Load a vector store from a local directory
        
        Args:
            directory: Directory path where the vector store is saved
        """
        self.embedding_engine.load_vectorstore(directory)
    
    def setup_chain(self, custom_system_prompt: Optional[str] = None) -> None:
        """
        Set up the RAG chain
        
        Args:
            custom_system_prompt: Custom system prompt template (optional)
        """
        system_prompt = custom_system_prompt or self.default_system_prompt
        qa_chain = self.llm_engine.create_qa_chain(system_prompt)
        retriever = self.embedding_engine.get_retriever()
        self.rag_chain = create_retrieval_chain(retriever, qa_chain)
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG system
        
        Args:
            question: Question to ask
            
        Returns:
            Result dictionary containing answer and related information
        """
        if self.rag_chain is None:
            self.setup_chain()
        
        return self.rag_chain.invoke({"input": question})
    
    def get_answer(self, question: str) -> str:
        """
        Get just the answer to a question
        
        Args:
            question: Question to ask
            
        Returns:
            Answer string
        """
        result = self.query(question)
        return result["answer"]
    
    def query_from_saved_vectorstore(self, directory: str, question: str) -> str:
        """
        Query using a previously saved vector store
        
        Args:
            directory: Directory path where the vector store is saved
            question: Question to ask
            
        Returns:
            Answer string
        """
        # Load the vectorstore
        self.load_vectorstore(directory)
        
        # Set up the chain and query
        if self.rag_chain is None:
            self.setup_chain()
        
        # Get the answer
        return self.get_answer(question)


def main():
    rag = RAGSystem(api_key="orjLf2qy6YnY5oOanmFFzS0u7Z15tUyF")
    
    print("Starting RAG system...")
    
    rag.ingest_pdf("constitution_of_India.pdf")
    
    print("PDF ingested successfully.")
    
    vector_store_dir = "vectorstore_constitution_of_India"
    rag.save_vectorstore(vector_store_dir)
    
    print("Vector store saved successfully.")
    
    answer = rag.get_answer("What is preamble of India?")
    print("Answer from original vectorstore:", answer)
    

    new_rag = RAGSystem(api_key="orjLf2qy6YnY5oOanmFFzS0u7Z15tUyF")
    
    answer = new_rag.query_from_saved_vectorstore(
        vector_store_dir,
        "What is preamble of India?"
    )
    print("Answer from saved vectorstore:", answer)


if __name__ == "__main__":
    main()