"""Manage Pinecone index lifecycle, document chunking, retrieval, and deletion."""

import asyncio
import concurrent.futures
import functools
import os
import time
from collections.abc import Awaitable
from types import TracebackType
from typing import Any, Protocol, TypeAlias, TypeVar, cast

from pinecone import PineconeAsyncio, SearchQuery, SearchRerank, IndexEmbed  # pyright: ignore[reportMissingTypeStubs]
from pinecone.openapi_support.exceptions import NotFoundException
from src.config.settings import (
    PINECONE_API_KEY,
    DEFAULT_CHUNK_WORKERS,
    PINECONE_BATCH_SIZE,
    PINECONE_CHUNK_SIZE,
    PINECONE_CHUNK_OVERLAP,
    PINECONE_QUERY_TOP_K,
    PINECONE_QUERY_TOP_N,
    PINECONE_INDEX_TIMEOUT,
    PINECONE_NAMESPACE_CACHE_TTL,
)
from src.config.log_config import setup_logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.models.schemas import Content
from typing import Callable

T = TypeVar("T")
ChunkRecord: TypeAlias = dict[str, str]
DEFAULT_NAMESPACE = ""


class PineconeIndexStats(Protocol):
    """Index metadata required after creation or lookup."""

    host: str


class PineconeIndexAsyncContext(Protocol):
    """Async context manager returned for a Pinecone index connection."""

    async def __aenter__(self) -> "PineconeIndex": ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None: ...


class PineconeIndex(Protocol):
    """Subset of asynchronous index operations used by the service."""

    async def upsert_records(self, namespace: str, records: list[ChunkRecord]) -> None: ...
    async def delete(
        self,
        ids: list[str] | None = None,
        delete_all: bool | None = None,
        namespace: str | None = None,
        filter: dict[str, Any] | None = None,
    ) -> Any: ...
    async def search(
        self,
        namespace: str,
        query: SearchQuery,
        rerank: SearchRerank | None = None,
    ) -> Any: ...
    async def describe_index_stats(self, filter: dict[str, Any] | None = None) -> Any: ...
    def list(self, **kwargs: Any) -> Any: ...


class PineconeClient(Protocol):
    """Subset of Pinecone client operations used by the service."""

    inference: Any
    async def has_index(self, index_name: str) -> bool: ...
    async def create_index_for_model(
        self,
        *,
        name: str,
        cloud: str,
        region: str,
        embed: IndexEmbed,
        timeout: int,
    ) -> PineconeIndexStats: ...
    async def describe_index(self, index_name: str) -> PineconeIndexStats: ...
    async def delete_index(self, index_name: str) -> None: ...
    async def list_indexes(self) -> Any: ...
    def IndexAsyncio(self, host: str, **kwargs: Any) -> PineconeIndexAsyncContext: ...
    async def close(self) -> None: ...

# Determine a reasonable number of workers for chunking
# Default to DEFAULT_CHUNK_WORKERS if cpu_count is not available or fails
try:
    max_chunk_workers = os.cpu_count() or DEFAULT_CHUNK_WORKERS
except NotImplementedError:
    max_chunk_workers = DEFAULT_CHUNK_WORKERS

logger = setup_logging(filename='pinecone_service')

def ensure_initialized(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """
    Decorator to ensure PineconeService is initialized before method execution.
    """
    @functools.wraps(func)
    async def wrapper(self: "PineconeService", *args: Any, **kwargs: Any) -> T:
        if not self.is_initialized:
            logger.info(f"Auto-initializing PineconeService before calling {func.__name__}")
            await self.initialize()
        return await func(self, *args, **kwargs)
    return wrapper

class PineconeService:
    """Provide one shared asynchronous Pinecone client and chunking executor."""

    _instance: "PineconeService | None" = None
    _lock = asyncio.Lock()
    _initialized: bool
    pc: PineconeClient | None
    chunking_executor: concurrent.futures.ThreadPoolExecutor | None
    _host_cache: dict[str, str]
    _namespace_cache: dict[str, tuple[list[str], float]]
    
    def __new__(cls) -> "PineconeService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pc = None
            cls._instance.chunking_executor = None
            cls._instance._initialized = False
            cls._instance._host_cache = {}
            cls._instance._namespace_cache = {}
        return cls._instance

    async def initialize(self) -> 'PineconeService':
        """Initialize the shared client and executor once, returning this service."""
        async with self._lock:
            if not self._initialized:
                logger.info("Initializing PineconeService...")
                try:
                    self.pc = cast(PineconeClient, PineconeAsyncio(api_key=PINECONE_API_KEY))
                    self.chunking_executor = concurrent.futures.ThreadPoolExecutor(
                        max_workers=max_chunk_workers,
                        thread_name_prefix='ChunkerThread'
                    )
                    logger.info(f"Created chunking executor with max_workers={max_chunk_workers}")
                    self._initialized = True
                    logger.info("PineconeService initialized.")
                except Exception as e:
                    logger.error(f"Failed to initialize PineconeService: {e}")
                    raise
        return self

    @property
    def is_initialized(self) -> bool:
        """Return whether client resources are ready for use."""
        return self._initialized

    @property
    def _client(self) -> PineconeClient:
        """Return the initialized client or fail fast when lifecycle setup was skipped."""
        if self.pc is None:
            raise RuntimeError("PineconeService is not initialized.")
        return self.pc

    @ensure_initialized
    async def get_or_create_index(self, index_name: str) -> str:
        """Return the host URL for a Pinecone index, creating it if absent. Result is cached in memory."""
        if index_name in self._host_cache:
            return self._host_cache[index_name]

        client = self._client
        if not await client.has_index(index_name):
            logger.info(f"Index '{index_name}' not found. Creating...")
            index_stats = await client.create_index_for_model(
                name=index_name,
                cloud="aws",
                region="us-east-1",
                embed=IndexEmbed(model="multilingual-e5-large", field_map={"text": "text"}, metric="cosine"),
                timeout=PINECONE_INDEX_TIMEOUT,
            )
            host = index_stats.host
            logger.info(f"Pinecone index {index_name} created at {host}")
        else:
            logger.info(f"Index '{index_name}' found. Describing...")
            index_description = await client.describe_index(index_name)
            host = index_description.host
            logger.info(f"Pinecone index {index_name} host is {host}")

        self._host_cache[index_name] = host
        return host

    @ensure_initialized
    async def delete_index(self, index_name: str) -> bool:
        """Delete a Pinecone index"""
        client = self._client
        if await client.has_index(index_name):
            logger.info(f"Deleting index '{index_name}'...")
            await client.delete_index(index_name)
            logger.info(f"Index '{index_name}' deleted.")
            return True
        logger.info(f"Index '{index_name}' not found for deletion.")
        return False

    @ensure_initialized
    async def list_all_indexes(self) -> Any:
        """List all available Pinecone indexes"""
        return await self._client.list_indexes()

    @ensure_initialized
    async def upsert_documents(
        self,
        index_name: str,
        documents: list[Content],
        namespace: str = DEFAULT_NAMESPACE,
        batch_size: int = PINECONE_BATCH_SIZE,
    ) -> None:
        """Chunks documents and upserts them to Pinecone index in batches."""
        if not documents:
            logger.warning("No documents provided for upserting.")
            return

        host = await self.get_or_create_index(index_name)
        
        # Step 1: Chunk all documents using the shared executor
        client = self._client
        all_chunks = await self.chunk_documents(documents)
        if not all_chunks:
            logger.warning("No chunks were generated from the provided documents.")
            return
            
        total_chunks = len(all_chunks)
        logger.info(f"Generated {total_chunks} chunks from {len(documents)} documents.")

        # Step 2: Upsert chunks in batches
        async with client.IndexAsyncio(host=host) as index:
            logger.info(
                f"Starting upsert to index '{index_name}' namespace '{namespace}' at host {host} "
                f"in batches of {batch_size}..."
            )
            upserted_count = 0
            failed_batches = 0
            for i in range(0, total_chunks, batch_size):
                batch = all_chunks[i:i + batch_size]
                batch_ids = [chunk['id'] for chunk in batch]
                logger.debug(f"Upserting batch {i // batch_size + 1}/{(total_chunks + batch_size - 1) // batch_size} with {len(batch)} chunks (IDs: {batch_ids[:5]}...)")
                try:
                    await index.upsert_records(namespace=namespace, records=batch)
                    upserted_count += len(batch)
                    logger.debug(f"Successfully upserted batch {i // batch_size + 1}")
                except Exception as e:
                    failed_batches += 1
                    logger.error(f"Error upserting batch {i // batch_size + 1} (IDs: {batch_ids[:5]}...): {e}")
                    continue
            
            logger.info(f"Upsert complete. Successfully upserted {upserted_count}/{total_chunks} chunks.")
            if failed_batches or upserted_count != total_chunks:
                raise RuntimeError(
                    f"Upsert incomplete for index '{index_name}' namespace '{namespace}': "
                    f"{upserted_count}/{total_chunks} chunks upserted."
                )
        self._invalidate_namespace_cache(index_name)

    @ensure_initialized
    async def query_similar(
        self,
        index_name: str,
        query: str,
        namespace: str = DEFAULT_NAMESPACE,
        top_k: int = PINECONE_QUERY_TOP_K,
        top_n: int = PINECONE_QUERY_TOP_N,
        use_rerank: bool = True,
    ) -> Any:
        """Query similar vectors from Pinecone"""
        host = await self.get_or_create_index(index_name)
        async with self._client.IndexAsyncio(host=host) as index:
            logger.info(f"Querying index '{index_name}' namespace '{namespace}' at host {host}...")
            search_kwargs: dict[str, Any] = {
                "namespace": namespace,
                "query": SearchQuery(inputs={"text": query}, top_k=top_k),
            }
            if use_rerank:
                search_kwargs["rerank"] = SearchRerank(
                    model="pinecone-rerank-v0",
                    rank_fields=["text"],
                    top_n=top_n,
                    query=query,
                    parameters={"truncate": "END"},
                )
            results = await index.search(**search_kwargs)
            logger.info("Query complete.")
            return results

    @ensure_initialized
    async def query_similar_namespaces(
        self,
        index_name: str,
        query: str,
        namespaces: list[str] | None = None,
        top_k: int = PINECONE_QUERY_TOP_K,
        top_n: int = PINECONE_QUERY_TOP_N,
    ) -> dict[str, Any]:
        """Query all namespaces in parallel (vector-only), then rerank the merged pool once."""
        target_namespaces = namespaces or await self.list_namespaces(index_name)

        async def _query_one(namespace: str) -> tuple[str, Any]:
            try:
                result = await self.query_similar(
                    index_name, query, namespace=namespace, top_k=top_k, top_n=top_n, use_rerank=False,
                )
                return namespace, result
            except Exception as e:
                logger.error(
                    "Error querying index '%s' namespace '%s': %s",
                    index_name, namespace, e, exc_info=True,
                )
                return namespace, None

        pairs = await asyncio.gather(*(_query_one(ns) for ns in target_namespaces))

        candidates: list[dict[str, Any]] = []
        for namespace, result in pairs:
            if result is None:
                continue
            hits = getattr(getattr(result, "result", None), "hits", None) or []
            for hit in hits:
                text = (getattr(hit, "fields", None) or {}).get("text", "")
                if not text:
                    continue
                candidates.append({
                    "_id": getattr(hit, "_id", ""),
                    "text": text,
                    "namespace": namespace,
                    "_score": getattr(hit, "_score", 0.0),
                })

        if not candidates:
            logger.warning("No candidates found across namespaces for index '%s'", index_name)
            return {}

        try:
            reranked = await self._client.inference.rerank(
                model="pinecone-rerank-v0",
                query=query,
                documents=candidates,
                rank_fields=["text"],
                top_n=min(top_n, len(candidates)),
                parameters={"truncate": "END"},
            )
            top_hits = [
                {
                    "_id": candidates[item.index]["_id"],
                    "text": candidates[item.index]["text"],
                    "namespace": candidates[item.index]["namespace"],
                    "_score": item.score,
                }
                for item in (getattr(reranked, "data", None) or [])
            ]
            logger.info(
                "Reranked %d candidates to top %d hits across %d namespaces",
                len(candidates), len(top_hits), len(target_namespaces),
            )
        except Exception as e:
            logger.error("Reranking failed, falling back to vector score order: %s", e, exc_info=True)
            top_hits = sorted(candidates, key=lambda c: c["_score"], reverse=True)[:top_n]

        return {"reranked": top_hits}

    @ensure_initialized
    async def list_namespaces(self, index_name: str) -> list[str]:
        """List namespaces present in an index, cached for PINECONE_NAMESPACE_CACHE_TTL seconds."""
        cached = self._namespace_cache.get(index_name)
        if cached is not None:
            namespaces, ts = cached
            if time.monotonic() - ts < PINECONE_NAMESPACE_CACHE_TTL:
                return namespaces

        host = await self.get_or_create_index(index_name)
        async with self._client.IndexAsyncio(host=host) as index:
            stats = await index.describe_index_stats()

        raw_namespaces = getattr(stats, "namespaces", None)
        if raw_namespaces is None and isinstance(stats, dict):
            raw_namespaces = stats.get("namespaces")
        namespaces = list(raw_namespaces.keys()) if isinstance(raw_namespaces, dict) else [DEFAULT_NAMESPACE]
        self._namespace_cache[index_name] = (namespaces, time.monotonic())
        return namespaces

    def _invalidate_namespace_cache(self, index_name: str) -> None:
        """Drop the namespace cache for an index after a write that may add or remove namespaces."""
        self._namespace_cache.pop(index_name, None)

    @ensure_initialized
    async def upsert_single_record(
        self,
        index_name: str,
        namespace: str,
        text: str,
        record_id: str | None = None,
    ) -> str:
        """Upsert a single text record (no chunking). Returns the record ID."""
        import uuid
        rid = record_id or uuid.uuid4().hex
        host = await self.get_or_create_index(index_name)
        async with self._client.IndexAsyncio(host=host) as index:
            await index.upsert_records(namespace=namespace, records=[{"id": rid, "text": text}])
        logger.info("Upserted single record '%s' to index '%s' ns '%s'", rid, index_name, namespace)
        self._invalidate_namespace_cache(index_name)
        return rid

    @ensure_initialized
    async def delete_records_by_ids(
        self,
        index_name: str,
        namespace: str,
        ids: list[str],
    ) -> None:
        """Delete specific records by their IDs."""
        host = await self.get_or_create_index(index_name)
        async with self._client.IndexAsyncio(host=host) as index:
            await index.delete(ids=ids, namespace=namespace)
        logger.info("Deleted %d records from index '%s' ns '%s'", len(ids), index_name, namespace)

    @ensure_initialized
    async def delete_namespace(self, index_name: str, namespace: str) -> None:
        """Delete all records from a namespace without deleting the index."""
        host = await self.get_or_create_index(index_name)
        async with self._client.IndexAsyncio(host=host) as index:
            logger.info("Deleting namespace '%s' from index '%s'", namespace, index_name)
            try:
                await index.delete(delete_all=True, namespace=namespace)
            except NotFoundException:
                logger.info(
                    "Namespace '%s' was not found in index '%s'; nothing to delete.",
                    namespace,
                    index_name,
                )
        self._invalidate_namespace_cache(index_name)

    @ensure_initialized
    async def delete_records_by_prefix(
        self,
        index_name: str,
        namespace: str,
        prefix: str,
    ) -> int:
        """Delete records in a namespace whose IDs start with a prefix."""
        host = await self.get_or_create_index(index_name)
        deleted_count = 0

        async with self._client.IndexAsyncio(host=host) as index:
            try:
                async for id_batch in index.list(prefix=prefix, namespace=namespace):
                    if not id_batch:
                        continue
                    await index.delete(ids=id_batch, namespace=namespace)
                    deleted_count += len(id_batch)
            except NotFoundException:
                logger.info(
                    "Namespace '%s' was not found in index '%s'; no prefixed records to delete.",
                    namespace,
                    index_name,
                )

        logger.info(
            "Deleted %s records from index '%s' namespace '%s' with prefix '%s'",
            deleted_count,
            index_name,
            namespace,
            prefix,
        )
        return deleted_count

    @ensure_initialized
    async def chunk_documents(
        self,
        documents: list[Content],
        chunk_size: int = PINECONE_CHUNK_SIZE,
        chunk_overlap: int = PINECONE_CHUNK_OVERLAP,
    ) -> list[ChunkRecord]:
        """Chunk text content from multiple documents into smaller pieces using a shared thread pool executor."""
        logger.info(f"Starting chunking for {len(documents)} documents with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
        loop = asyncio.get_running_loop()
        all_chunks: list[ChunkRecord] = []
        tasks: list[tuple[Content, Awaitable[list[str]]]] = []

        def run_split(text_to_split: str) -> list[str]:
            """Split one document inside the shared thread pool."""
            logger.debug(f"Running split_text in executor for text length: {len(text_to_split)}")
            chunks = splitter.split_text(text_to_split)
            logger.debug(f"split_text returned {len(chunks)} chunks")
            return chunks

        for doc in documents:
            if not doc.text or not doc.text.strip():
                logger.warning(f"Skipping document ID {doc.id} due to empty or invalid text content.")
                continue
            if self.chunking_executor is None:
                raise RuntimeError("Chunking executor is not initialized.")
            task = loop.run_in_executor(self.chunking_executor, run_split, doc.text)
            tasks.append((doc, task))
            
        results = await asyncio.gather(*(task for _, task in tasks), return_exceptions=True)

        for (doc, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.error(f"Error chunking document ID {doc.id}: {result}")
                continue
            if not isinstance(result, list):
                logger.error(f"Unexpected chunking result for document ID {doc.id}: {result}")
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

    async def close(self) -> None:
        """Close the Pinecone client connection and shutdown the executor."""
        if self._initialized:
            logger.info("Closing Pinecone client connection...")
            await self._client.close()
            logger.info("Pinecone client connection closed.")
            
            if self.chunking_executor:
                logger.info(f"Shutting down chunking executor ({self.chunking_executor._max_workers} workers)...")
                self.chunking_executor.shutdown(wait=True)
                self.chunking_executor = None
                logger.info("Chunking executor shut down.")
                
            self._initialized = False
