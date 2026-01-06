"""
Application configuration loaded from environment variables.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # === Application ===
    app_name: str = "DCAI Intelligence Platform"
    debug: bool = False
    log_level: str = "INFO"
    
    # === API URLs ===
    api_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000,https://myintel.alfalasi.io"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # === OpenRouter (LLM) ===
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # LLM Models - All Gemini 3 Flash for consistency
    llm_model_chat: str = "google/gemini-3-flash-preview"
    llm_model_reasoning: str = "google/gemini-3-flash-preview"
    llm_model_fast: str = "google/gemini-3-flash-preview"
    llm_model_extraction: str = "google/gemini-3-flash-preview"
    llm_model_fallback: str = "google/gemini-2.5-flash"
    
    # LLM Timeouts (seconds)
    llm_timeout_chat: int = 60
    llm_timeout_reasoning: int = 180
    llm_timeout_extraction: int = 120
    
    # LLM Token Limits
    max_tokens_chat: int = 4096
    max_tokens_reasoning: int = 8192
    max_tokens_extraction: int = 8192
    
    # === RAGFlow ===
    ragflow_url: str = "http://localhost:9380"
    ragflow_api_key: str = "ragflow-BjzhB7GzV1Vi680U17VAJEgcrPLwq-5fBwVd4CZT0DM"
    ragflow_dataset_id: str = "eceb7b32e83111f080689a6078826a72"
    ragflow_enable_graph: bool = True
    ragflow_graph_method: str = "lightrag"
    ragflow_entity_types: str = "person,organization,policy,initiative,technology,country,statistic,recommendation,risk,opportunity"
    ragflow_chunk_size: int = 512
    ragflow_chunk_overlap: int = 50
    
    @property
    def ragflow_entity_types_list(self) -> List[str]:
        return [t.strip() for t in self.ragflow_entity_types.split(",")]
    
    # === Supabase ===
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    database_url: str = ""
    jwt_secret: str = ""
    
    # === Firecrawl & Tavily ===
    firecrawl_api_key: str = ""
    firecrawl_url: str = "https://myfirecrawl.alfalasi.io"
    tavily_api_key: str = ""
    
    # === News Sources ===
    news_sources: str = ""
    news_refresh_interval: int = 60  # minutes
    
    @property
    def news_sources_list(self) -> List[str]:
        if not self.news_sources:
            return []
        return [s.strip() for s in self.news_sources.split(",")]
    
    # === Admin ===
    admin_email: str = "s.falasi@gmail.com"
    admin_password: str = ""
    
    # === Processing ===
    max_concurrent_processing: int = 5
    mineru_reports_path: str = ""
    temp_processing_path: str = ""
    
    # === Rate Limiting ===
    rate_limit_chat: int = 30
    rate_limit_search: int = 60
    rate_limit_upload: int = 10
    
    # === Feature Flags ===
    enable_digital_minister: bool = True
    enable_news_analysis: bool = True
    enable_meeting_prep: bool = True
    enable_data_bank: bool = True
    enable_graph_visualization: bool = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
