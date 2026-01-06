"""
RAGFlow client service for vector search and document management.
Supports RAGFlow v0.23+ API.
"""
import httpx
from typing import Optional, Any
from uuid import UUID

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import RAGFlowError

logger = get_logger(__name__)


class RAGFlowClient:
    """Client for RAGFlow API operations."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 60.0
    ):
        self.base_url = (base_url or settings.ragflow_url).rstrip("/")
        self.api_key = api_key or settings.ragflow_api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def headers(self) -> dict:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=self.timeout
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> dict:
        """Make an API request to RAGFlow."""
        client = await self._get_client()
        
        try:
            response = await client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            data = response.json()
            
            # RAGFlow returns {"code": 0, "data": ...} on success
            if isinstance(data, dict) and "code" in data:
                if data["code"] != 0:
                    error_msg = data.get("message", "Unknown RAGFlow error")
                    logger.error(f"RAGFlow error: {error_msg}", endpoint=endpoint)
                    raise RAGFlowError(error_msg)
                return data.get("data", data)
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"RAGFlow HTTP error: {e.response.status_code}",
                endpoint=endpoint,
                response=e.response.text[:500]
            )
            raise RAGFlowError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
        except httpx.RequestError as e:
            logger.error(f"RAGFlow request error: {e}", endpoint=endpoint)
            raise RAGFlowError(f"Request failed: {str(e)}")
    
    # === Dataset (Knowledge Base) Operations ===
    
    async def list_datasets(self) -> list[dict]:
        """List all datasets (knowledge bases)."""
        return await self._request("GET", "/api/v1/datasets")
    
    async def create_dataset(
        self,
        name: str,
        description: str = "",
        language: str = "English",
        embedding_model: str = "",
        chunk_method: str = "naive",
        parser_config: Optional[dict] = None
    ) -> dict:
        """Create a new dataset (knowledge base)."""
        payload = {
            "name": name,
            "description": description,
            "language": language,
            "embedding_model": embedding_model,
            "chunk_method": chunk_method,
        }
        if parser_config:
            payload["parser_config"] = parser_config
        
        logger.info(f"Creating dataset: {name}")
        return await self._request("POST", "/api/v1/datasets", json=payload)
    
    async def get_dataset(self, dataset_id: str) -> dict:
        """Get dataset details by ID."""
        return await self._request("GET", f"/api/v1/datasets/{dataset_id}")
    
    async def delete_dataset(self, dataset_id: str) -> dict:
        """Delete a dataset."""
        logger.warning(f"Deleting dataset: {dataset_id}")
        return await self._request("DELETE", f"/api/v1/datasets/{dataset_id}")
    
    # === Document Operations ===
    
    async def list_documents(
        self,
        dataset_id: str,
        page: int = 1,
        page_size: int = 100,
        keywords: str = ""
    ) -> dict:
        """List documents in a dataset."""
        params = {
            "page": page,
            "page_size": page_size
        }
        if keywords:
            params["keywords"] = keywords
        
        return await self._request(
            "GET",
            f"/api/v1/datasets/{dataset_id}/documents",
            params=params
        )
    
    async def upload_document(
        self,
        dataset_id: str,
        file_path: str,
        file_name: str,
        chunk_method: Optional[str] = None
    ) -> dict:
        """Upload a document to a dataset."""
        import aiofiles
        
        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()
        
        files = {"file": (file_name, content)}
        data = {}
        if chunk_method:
            data["chunk_method"] = chunk_method
        
        # Need to use different headers for file upload
        client = await self._get_client()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            response = await client.post(
                f"/api/v1/datasets/{dataset_id}/documents",
                files=files,
                data=data,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise RAGFlowError(result.get("message", "Upload failed"))
            
            logger.info(f"Uploaded document: {file_name} to dataset {dataset_id}")
            return result.get("data", result)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Upload failed: {e.response.text[:500]}")
            raise RAGFlowError(f"Upload failed: {e.response.status_code}")
    
    async def upload_document_text(
        self,
        dataset_id: str,
        name: str,
        text: str,
        chunk_method: Optional[str] = None
    ) -> dict:
        """
        Upload text content as a document.
        
        RAGFlow requires multipart/form-data with a 'file' field.
        We send the text content as a file with the specified name.
        
        IMPORTANT: We use a fresh client without Content-Type header,
        as httpx needs to set it for multipart/form-data.
        """
        # Ensure name has an extension for RAGFlow to recognize
        if not name.endswith(('.txt', '.md')):
            name = f"{name}.md"
        
        # Encode text as bytes
        text_bytes = text.encode('utf-8')
        
        # Prepare multipart form data - use tuple format (filename, content, content_type)
        files = {"file": (name, text_bytes, "text/markdown")}
        data = {}
        if chunk_method:
            data["chunk_method"] = chunk_method
        
        # Create a fresh client WITHOUT Content-Type header for multipart upload
        # The pre-configured client has Content-Type: application/json which breaks multipart
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        ) as upload_client:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            try:
                logger.info(f"Uploading text document: {name}")
                response = await upload_client.post(
                    f"/api/v1/datasets/{dataset_id}/documents",
                    files=files,
                    data=data if data else None,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("code") != 0:
                    error_msg = result.get("message", "Upload failed")
                    logger.error(f"RAGFlow upload error: {error_msg}")
                    raise RAGFlowError(error_msg)
                
                # Return the first document from the array
                data_result = result.get("data", [])
                if isinstance(data_result, list) and len(data_result) > 0:
                    logger.info(f"Successfully uploaded: {name} (id: {data_result[0].get('id')})")
                    return data_result[0]
                return data_result
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Upload HTTP error: {e.response.status_code} - {e.response.text[:500]}")
                raise RAGFlowError(f"Upload failed: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Upload request error: {e}")
                raise RAGFlowError(f"Upload request failed: {str(e)}")
    
    async def get_document(self, dataset_id: str, document_id: str) -> dict:
        """Get document details."""
        return await self._request(
            "GET",
            f"/api/v1/datasets/{dataset_id}/documents/{document_id}"
        )
    
    async def delete_document(self, dataset_id: str, document_id: str) -> dict:
        """Delete a document."""
        logger.warning(f"Deleting document: {document_id}")
        return await self._request(
            "DELETE",
            f"/api/v1/datasets/{dataset_id}/documents/{document_id}"
        )
    
    async def parse_documents(
        self,
        dataset_id: str,
        document_ids: list[str]
    ) -> dict:
        """Trigger parsing/chunking for documents."""
        # RAGFlow uses /documents/run endpoint, not /documents/parse
        payload = {"document_ids": document_ids}
        logger.info(f"Parsing {len(document_ids)} documents")
        return await self._request(
            "POST",
            f"/api/v1/datasets/{dataset_id}/documents/run",
            json=payload
        )
    
    async def get_document_chunks(
        self,
        dataset_id: str,
        document_id: str,
        page: int = 1,
        page_size: int = 100
    ) -> dict:
        """Get chunks for a document."""
        params = {"page": page, "page_size": page_size}
        return await self._request(
            "GET",
            f"/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks",
            params=params
        )
    
    # === Retrieval Operations ===
    
    async def retrieve(
        self,
        dataset_ids: list[str],
        question: str,
        top_k: int = 10,
        similarity_threshold: float = 0.2,
        keyword_similarity_weight: float = 0.3,
        document_ids: Optional[list[str]] = None,
        rerank_model: Optional[str] = None
    ) -> list[dict]:
        """
        Retrieve relevant chunks from datasets.
        
        Args:
            dataset_ids: List of dataset IDs to search
            question: Query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            keyword_similarity_weight: Weight for keyword vs semantic search
            document_ids: Optional filter to specific documents
            rerank_model: Optional reranker model name
        
        Returns:
            List of chunk dictionaries with content, score, metadata
        """
        payload = {
            "dataset_ids": dataset_ids,
            "question": question,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "keyword_similarity_weight": keyword_similarity_weight,
        }
        
        if document_ids:
            payload["document_ids"] = document_ids
        if rerank_model:
            payload["rerank_model"] = rerank_model
        
        logger.debug(f"Retrieving for query: {question[:100]}...")
        result = await self._request("POST", "/api/v1/retrieval", json=payload)
        
        # Normalize the response format
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "chunks" in result:
            return result["chunks"]
        return []
    
    # === Chat Operations (RAGFlow native chat) ===
    
    async def create_chat(
        self,
        name: str,
        dataset_ids: list[str],
        llm_model: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> dict:
        """Create a chat assistant."""
        payload = {
            "name": name,
            "dataset_ids": dataset_ids
        }
        if llm_model:
            payload["llm"] = {"model_name": llm_model}
        if prompt:
            payload["prompt"] = {"system": prompt}
        
        return await self._request("POST", "/api/v1/chats", json=payload)
    
    async def chat_completion(
        self,
        chat_id: str,
        question: str,
        session_id: Optional[str] = None,
        stream: bool = False
    ) -> dict:
        """Send a message to a chat assistant."""
        payload = {
            "question": question,
            "stream": stream
        }
        if session_id:
            payload["session_id"] = session_id
        
        return await self._request(
            "POST",
            f"/api/v1/chats/{chat_id}/completions",
            json=payload
        )
    
    # === Graph Operations (if enabled) ===
    
    async def get_graph(self, dataset_id: str) -> dict:
        """Get knowledge graph for a dataset."""
        try:
            return await self._request(
                "GET",
                f"/api/v1/datasets/{dataset_id}/graph"
            )
        except RAGFlowError as e:
            logger.warning(f"Graph not available: {e}")
            return {"nodes": [], "edges": []}
    
    async def query_graph(
        self,
        dataset_id: str,
        query: str,
        depth: int = 2
    ) -> dict:
        """Query the knowledge graph."""
        payload = {
            "query": query,
            "depth": depth
        }
        return await self._request(
            "POST",
            f"/api/v1/datasets/{dataset_id}/graph/query",
            json=payload
        )
    
    # === Health Check ===
    
    async def health_check(self) -> bool:
        """Check if RAGFlow is healthy."""
        try:
            client = await self._get_client()
            response = await client.get("/api/v1/system/status")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"RAGFlow health check failed: {e}")
            return False


# Singleton instance
_ragflow_client: Optional[RAGFlowClient] = None


def get_ragflow_client() -> RAGFlowClient:
    """Get the singleton RAGFlow client."""
    global _ragflow_client
    if _ragflow_client is None:
        _ragflow_client = RAGFlowClient()
    return _ragflow_client


async def close_ragflow_client():
    """Close the RAGFlow client connection."""
    global _ragflow_client
    if _ragflow_client:
        await _ragflow_client.close()
        _ragflow_client = None
