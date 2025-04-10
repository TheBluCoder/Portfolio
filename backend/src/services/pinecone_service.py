import asyncio
import concurrent.futures
import os
import functools
from pinecone import PineconeAsyncio, SearchQuery, SearchRerank, IndexEmbed
from src.config.settings import (
    PINECONE_API_KEY, 
    DEFAULT_CHUNK_WORKERS,
    PINECONE_BATCH_SIZE,
    PINECONE_CHUNK_SIZE,
    PINECONE_CHUNK_OVERLAP,
    PINECONE_QUERY_TOP_K,
    PINECONE_QUERY_TOP_N,
    PINECONE_INDEX_TIMEOUT
)
from src.config.log_config import setup_logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.models.schemas import Content
from typing import List, Dict, Callable, Any

# Determine a reasonable number of workers for chunking
# Default to DEFAULT_CHUNK_WORKERS if cpu_count is not available or fails
try:
    MAX_CHUNK_WORKERS = os.cpu_count() or DEFAULT_CHUNK_WORKERS
except NotImplementedError:
    MAX_CHUNK_WORKERS = DEFAULT_CHUNK_WORKERS

logger = setup_logging(filename='pinecone_service')

def ensure_initialized(func: Callable) -> Callable:
    """
    Decorator to ensure PineconeService is initialized before method execution.
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs) -> Any:
        if not self._initialized:
            logger.info(f"Auto-initializing PineconeService before calling {func.__name__}")
            await self.initialize()
        return await func(self, *args, **kwargs)
    return wrapper

class PineconeService:
    _instance = None
    _initialized = False
    _lock = asyncio.Lock()
    chunking_executor = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pc = None
            cls._instance.chunking_executor = None
            cls._instance._initialized = False
        return cls._instance

    async def initialize(self) -> 'PineconeService':
        async with self._lock:
            if not self._initialized:
                logger.info("Initializing PineconeService...")
                try:
                    self.pc = PineconeAsyncio(api_key=PINECONE_API_KEY)
                    self.chunking_executor = concurrent.futures.ThreadPoolExecutor(
                        max_workers=MAX_CHUNK_WORKERS,
                        thread_name_prefix='ChunkerThread'
                    )
                    logger.info(f"Created chunking executor with max_workers={MAX_CHUNK_WORKERS}")
                    self._initialized = True
                    logger.info("PineconeService initialized.")
                except Exception as e:
                    logger.error(f"Failed to initialize PineconeService: {e}")
                    raise
        return self

    @ensure_initialized
    async def get_or_create_index(self, index_name: str) -> str:
        """
        Get the host for a Pinecone index. Creates the index if it doesn't exist.
        Returns the index host URL.
        """
        if not await self.pc.has_index(index_name):
            logger.info(f"Index '{index_name}' not found. Creating...")
            index_stats = await self.pc.create_index_for_model(
                name=index_name,
                cloud="aws", 
                region="us-east-1", 
                embed=IndexEmbed(model="multilingual-e5-large", field_map={"text": "text"}, metric="cosine"),
                timeout=PINECONE_INDEX_TIMEOUT 
            )
            host = index_stats.host
            logger.info(f"Pinecone index {index_name} created at {host}")
            return host
        else:
            logger.info(f"Index '{index_name}' found. Describing...")
            index_description = await self.pc.describe_index(index_name)
            host = index_description.host
            logger.info(f"Pinecone index {index_name} host is {host}")
            return host

    @ensure_initialized
    async def delete_index(self, index_name: str) -> bool:
        """Delete a Pinecone index"""
        if await self.pc.has_index(index_name):
            logger.info(f"Deleting index '{index_name}'...")
            await self.pc.delete_index(index_name)
            logger.info(f"Index '{index_name}' deleted.")
            return True
        logger.info(f"Index '{index_name}' not found for deletion.")
        return False

    @ensure_initialized
    async def list_all_indexes(self):
        """List all available Pinecone indexes"""
        return await self.pc.list_indexes()

    @ensure_initialized
    async def upsert_documents(self, index_name: str, documents: List[Content], batch_size: int = PINECONE_BATCH_SIZE):
        """Chunks documents and upserts them to Pinecone index in batches."""
        if not documents:
            logger.warning("No documents provided for upserting.")
            return

        host = await self.get_or_create_index(index_name)
        
        # Step 1: Chunk all documents using the shared executor
        all_chunks = await self.chunk_documents(documents)
        if not all_chunks:
            logger.warning("No chunks were generated from the provided documents.")
            return
            
        total_chunks = len(all_chunks)
        logger.info(f"Generated {total_chunks} chunks from {len(documents)} documents.")

        # Step 2: Upsert chunks in batches
        async with self.pc.IndexAsyncio(host=host) as index:
            logger.info(f"Starting upsert to index '{index_name}' at host {host} in batches of {batch_size}...")
            upserted_count = 0
            for i in range(0, total_chunks, batch_size):
                batch = all_chunks[i:i + batch_size]
                logger.info(f"batch {batch} ")
                batch_ids = [chunk['id'] for chunk in batch]
                logger.debug(f"Upserting batch {i // batch_size + 1}/{(total_chunks + batch_size - 1) // batch_size} with {len(batch)} chunks (IDs: {batch_ids[:5]}...)")
                try:
                    await index.upsert_records(namespace="default", records=batch)
                    upserted_count += len(batch)
                    logger.debug(f"Successfully upserted batch {i // batch_size + 1}")
                except Exception as e:
                    logger.error(f"Error upserting batch {i // batch_size + 1} (IDs: {batch_ids[:5]}...): {e}")
                    continue
            
            logger.info(f"Upsert complete. Successfully upserted {upserted_count}/{total_chunks} chunks.")

    @ensure_initialized
    async def query_similar(self, index_name: str, query: str, top_k: int = PINECONE_QUERY_TOP_K, top_n: int = PINECONE_QUERY_TOP_N):
        """Query similar vectors from Pinecone"""
        host = await self.get_or_create_index(index_name)
        async with self.pc.IndexAsyncio(host=host) as index:
            logger.info(f"Querying index '{index_name}' at host {host}...")
            results = await index.search(
                namespace="default", 
                query=SearchQuery(inputs={"text": query}, top_k=top_k), 
                rerank=SearchRerank(model="pinecone-rerank-v0", rank_fields=["text"], top_n=top_n, query=query)
            )
            logger.info("Query complete.")
            return results

    @ensure_initialized
    async def chunk_documents(self, documents: List[Content], chunk_size: int = PINECONE_CHUNK_SIZE, chunk_overlap: int = PINECONE_CHUNK_OVERLAP) -> List[Dict]:
        """Chunk text content from multiple documents into smaller pieces using a shared thread pool executor."""
        logger.info(f"Starting chunking for {len(documents)} documents with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
        loop = asyncio.get_running_loop()
        all_chunks = []
        tasks = []

        def run_split(text_to_split: str):
            logger.debug(f"Running split_text in executor for text length: {len(text_to_split)}")
            chunks = splitter.split_text(text_to_split)
            logger.debug(f"split_text returned {len(chunks)} chunks")
            return chunks

        for doc in documents:
            if not doc.text or not isinstance(doc.text, str) or not doc.text.strip():
                logger.warning(f"Skipping document ID {doc.id} due to empty or invalid text content.")
                continue
            task = loop.run_in_executor(self.chunking_executor, run_split, doc.text)
            tasks.append((doc, task))
            
        results = await asyncio.gather(*(task for _, task in tasks), return_exceptions=True)

        for (doc, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.error(f"Error chunking document ID {doc.id}: {result}")
                continue
            
            text_chunks = result
            logger.debug(f"Processing {len(text_chunks)} chunks for doc ID {doc.id} from executor result.")
            for i, text_chunk in enumerate(text_chunks):
                if text_chunk.strip():
                    chunk_id = f"{doc.id}_chunk_{i}"
                    all_chunks.append({
                        "id": chunk_id,
                        "text": text_chunk.strip()
                    })
                
        logger.info(f"Total valid chunks generated: {len(all_chunks)}")
        return all_chunks

    async def close(self):
        """Close the Pinecone client connection and shutdown the executor."""
        if self._initialized:
            logger.info("Closing Pinecone client connection...")
            await self.pc.close()
            logger.info("Pinecone client connection closed.")
            
            if self.chunking_executor:
                logger.info(f"Shutting down chunking executor ({self.chunking_executor._max_workers} workers)...")
                self.chunking_executor.shutdown(wait=True)
                self.chunking_executor = None
                logger.info("Chunking executor shut down.")
                
            self._initialized = False