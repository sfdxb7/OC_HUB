"""
Supabase service for database operations.
Handles reports, conversations, messages, and user management.
"""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
import json

from supabase import create_client, Client
from postgrest.exceptions import APIError

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import DatabaseError

logger = get_logger(__name__)


class SupabaseService:
    """Service for Supabase database operations."""
    
    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None
    ):
        self.url = url or settings.supabase_url
        self.key = key or settings.supabase_service_key
        self._client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            self._client = create_client(self.url, self.key)
        return self._client
    
    # === Reports ===
    
    async def get_reports(
        self,
        search: Optional[str] = None,
        source: Optional[str] = None,
        year: Optional[int] = None,
        category: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[list[dict], int]:
        """
        Get reports with filtering and pagination.
        
        Returns:
            Tuple of (reports list, total count)
        """
        try:
            query = self.client.table("reports").select("*", count="exact")
            
            if search:
                query = query.or_(
                    f"title.ilike.%{search}%,"
                    f"executive_summary.ilike.%{search}%"
                )
            if source:
                query = query.eq("source", source)
            if year:
                query = query.eq("year", year)
            if category:
                query = query.eq("category", category)
            
            # Pagination
            offset = (page - 1) * limit
            query = query.range(offset, offset + limit - 1)
            query = query.order("created_at", desc=True)
            
            result = query.execute()
            total = result.count or 0
            
            return result.data, total
            
        except APIError as e:
            logger.error(f"Database error getting reports: {e}")
            raise DatabaseError(f"Failed to get reports: {e}")
    
    async def get_report(self, report_id: UUID) -> Optional[dict]:
        """Get a single report by ID."""
        try:
            result = self.client.table("reports")\
                .select("*")\
                .eq("id", str(report_id))\
                .single()\
                .execute()
            return result.data
        except APIError as e:
            if "PGRST116" in str(e):  # Not found
                return None
            logger.error(f"Database error getting report: {e}")
            raise DatabaseError(f"Failed to get report: {e}")
    
    async def create_report(self, report_data: dict) -> dict:
        """Create a new report."""
        try:
            result = self.client.table("reports")\
                .insert(report_data)\
                .execute()
            logger.info(f"Created report: {report_data.get('title')}")
            return result.data[0]
        except APIError as e:
            logger.error(f"Database error creating report: {e}")
            raise DatabaseError(f"Failed to create report: {e}")
    
    async def update_report(self, report_id: UUID, updates: dict) -> dict:
        """Update a report."""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            result = self.client.table("reports")\
                .update(updates)\
                .eq("id", str(report_id))\
                .execute()
            return result.data[0] if result.data else {}
        except APIError as e:
            logger.error(f"Database error updating report: {e}")
            raise DatabaseError(f"Failed to update report: {e}")
    
    async def delete_report(self, report_id: UUID) -> bool:
        """Delete a report."""
        try:
            self.client.table("reports")\
                .delete()\
                .eq("id", str(report_id))\
                .execute()
            logger.warning(f"Deleted report: {report_id}")
            return True
        except APIError as e:
            logger.error(f"Database error deleting report: {e}")
            raise DatabaseError(f"Failed to delete report: {e}")
    
    async def get_report_by_filename(self, filename: str) -> Optional[dict]:
        """Get a report by filename (folder name)."""
        try:
            result = self.client.table("reports")\
                .select("*")\
                .eq("filename", filename)\
                .limit(1)\
                .execute()
            return result.data[0] if result.data else None
        except APIError as e:
            logger.error(f"Database error getting report by filename: {e}")
            return None
    
    async def get_report_sources(self) -> list[str]:
        """Get distinct report sources."""
        try:
            result = self.client.table("reports")\
                .select("source")\
                .execute()
            sources = set(r["source"] for r in result.data if r.get("source"))
            return sorted(list(sources))
        except APIError as e:
            logger.error(f"Database error getting sources: {e}")
            raise DatabaseError(f"Failed to get sources: {e}")
    
    async def get_report_years(self) -> list[int]:
        """Get distinct report years."""
        try:
            result = self.client.table("reports")\
                .select("year")\
                .execute()
            years = set(r["year"] for r in result.data if r.get("year"))
            return sorted(list(years), reverse=True)
        except APIError as e:
            logger.error(f"Database error getting years: {e}")
            raise DatabaseError(f"Failed to get years: {e}")
    
    # === Conversations ===
    
    async def create_conversation(
        self,
        user_id: UUID,
        mode: str,
        report_id: Optional[UUID] = None,
        title: Optional[str] = None
    ) -> dict:
        """Create a new conversation."""
        try:
            data = {
                "user_id": str(user_id),
                "mode": mode,
                "title": title
            }
            if report_id:
                data["report_id"] = str(report_id)
            
            result = self.client.table("conversations")\
                .insert(data)\
                .execute()
            return result.data[0]
        except APIError as e:
            logger.error(f"Database error creating conversation: {e}")
            raise DatabaseError(f"Failed to create conversation: {e}")
    
    async def get_conversations(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> list[dict]:
        """Get user's conversations."""
        try:
            # Try with reports join first, fallback to without
            try:
                result = self.client.table("conversations")\
                    .select("*, reports(title)")\
                    .eq("user_id", str(user_id))\
                    .order("updated_at", desc=True)\
                    .range(offset, offset + limit - 1)\
                    .execute()
                return result.data
            except APIError:
                # Fallback without reports join
                result = self.client.table("conversations")\
                    .select("*")\
                    .eq("user_id", str(user_id))\
                    .order("updated_at", desc=True)\
                    .range(offset, offset + limit - 1)\
                    .execute()
                return result.data
        except APIError as e:
            logger.error(f"Database error getting conversations: {e}")
            raise DatabaseError(f"Failed to get conversations: {e}")
    
    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[dict]:
        """Get a conversation with messages."""
        try:
            query = self.client.table("conversations")\
                .select("*, messages(*), reports(title)")\
                .eq("id", str(conversation_id))
            
            if user_id:
                query = query.eq("user_id", str(user_id))
            
            result = query.single().execute()
            return result.data
        except APIError as e:
            if "PGRST116" in str(e):
                return None
            logger.error(f"Database error getting conversation: {e}")
            raise DatabaseError(f"Failed to get conversation: {e}")
    
    async def delete_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a conversation (cascades to messages)."""
        try:
            self.client.table("conversations")\
                .delete()\
                .eq("id", str(conversation_id))\
                .eq("user_id", str(user_id))\
                .execute()
            return True
        except APIError as e:
            logger.error(f"Database error deleting conversation: {e}")
            raise DatabaseError(f"Failed to delete conversation: {e}")
    
    # === Messages ===
    
    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        citations: Optional[list[dict]] = None,
        model_used: Optional[str] = None
    ) -> dict:
        """Add a message to a conversation."""
        try:
            data = {
                "conversation_id": str(conversation_id),
                "role": role,
                "content": content,
                "model_used": model_used
            }
            if citations:
                data["citations"] = json.dumps(citations)
            
            result = self.client.table("messages")\
                .insert(data)\
                .execute()
            
            # Update conversation timestamp
            self.client.table("conversations")\
                .update({"updated_at": datetime.utcnow().isoformat()})\
                .eq("id", str(conversation_id))\
                .execute()
            
            return result.data[0]
        except APIError as e:
            logger.error(f"Database error adding message: {e}")
            raise DatabaseError(f"Failed to add message: {e}")
    
    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 50
    ) -> list[dict]:
        """Get messages for a conversation."""
        try:
            result = self.client.table("messages")\
                .select("*")\
                .eq("conversation_id", str(conversation_id))\
                .order("created_at", desc=False)\
                .limit(limit)\
                .execute()
            return result.data
        except APIError as e:
            logger.error(f"Database error getting messages: {e}")
            raise DatabaseError(f"Failed to get messages: {e}")
    
    # === Data Bank ===
    
    async def get_databank_items(
        self,
        item_type: Optional[str] = None,
        report_id: Optional[UUID] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> tuple[list[dict], int]:
        """Get data bank items with filtering."""
        try:
            query = self.client.table("data_bank")\
                .select("*, reports(title, source)", count="exact")
            
            if item_type:
                query = query.eq("type", item_type)
            if report_id:
                query = query.eq("report_id", str(report_id))
            if search:
                query = query.or_(
                    f"content.ilike.%{search}%,"
                    f"context.ilike.%{search}%"
                )
            
            offset = (page - 1) * limit
            query = query.range(offset, offset + limit - 1)
            query = query.order("created_at", desc=True)
            
            result = query.execute()
            total = result.count or 0
            
            return result.data, total
        except APIError as e:
            logger.error(f"Database error getting databank: {e}")
            raise DatabaseError(f"Failed to get databank: {e}")
    
    async def add_databank_item(
        self,
        report_id: UUID,
        item_type: str,
        content: str,
        context: Optional[str] = None,
        source_page: Optional[int] = None,
        tags: Optional[list[str]] = None
    ) -> dict:
        """Add an item to the data bank."""
        try:
            data = {
                "report_id": str(report_id),
                "type": item_type,
                "content": content,
                "context": context,
                "source_page": source_page,
                "tags": tags or []
            }
            result = self.client.table("data_bank")\
                .insert(data)\
                .execute()
            return result.data[0]
        except APIError as e:
            logger.error(f"Database error adding databank item: {e}")
            raise DatabaseError(f"Failed to add databank item: {e}")
    
    # === News ===
    
    async def get_news_items(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> list[dict]:
        """Get news items."""
        try:
            result = self.client.table("news_items")\
                .select("*")\
                .order("published_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            return result.data
        except APIError as e:
            logger.error(f"Database error getting news: {e}")
            raise DatabaseError(f"Failed to get news: {e}")
    
    async def add_news_item(
        self,
        url: str,
        title: str,
        source: str,
        content: str,
        so_what_analysis: Optional[dict] = None,
        published_at: Optional[datetime] = None
    ) -> dict:
        """Add a news item."""
        try:
            data = {
                "url": url,
                "title": title,
                "source": source,
                "raw_content": content,
                "published_at": (published_at or datetime.utcnow()).isoformat()
            }
            if so_what_analysis:
                data["so_what_analysis"] = json.dumps(so_what_analysis)
            
            result = self.client.table("news_items")\
                .upsert(data, on_conflict="url")\
                .execute()
            return result.data[0]
        except APIError as e:
            logger.error(f"Database error adding news: {e}")
            raise DatabaseError(f"Failed to add news: {e}")
    
    # === Users ===
    
    async def get_user(self, user_id: UUID) -> Optional[dict]:
        """Get user by ID."""
        try:
            result = self.client.auth.admin.get_user_by_id(str(user_id))
            return result.user.__dict__ if result.user else None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    async def create_admin_user(
        self,
        email: str,
        password: str
    ) -> dict:
        """Create an admin user."""
        try:
            result = self.client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"role": "admin"}
            })
            logger.info(f"Created admin user: {email}")
            return result.user.__dict__
        except Exception as e:
            logger.error(f"Error creating admin: {e}")
            raise DatabaseError(f"Failed to create admin: {e}")
    
    # === Stats ===
    
    async def get_stats(self) -> dict:
        """Get platform statistics."""
        try:
            reports = self.client.table("reports").select("id", count="exact").execute()
            conversations = self.client.table("conversations").select("id", count="exact").execute()
            databank = self.client.table("data_bank").select("id", count="exact").execute()
            
            return {
                "total_reports": reports.count or 0,
                "total_conversations": conversations.count or 0,
                "total_databank_items": databank.count or 0
            }
        except APIError as e:
            logger.error(f"Database error getting stats: {e}")
            return {"total_reports": 0, "total_conversations": 0, "total_databank_items": 0}


# Singleton instance
_supabase_service: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    """Get the singleton Supabase service."""
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service
