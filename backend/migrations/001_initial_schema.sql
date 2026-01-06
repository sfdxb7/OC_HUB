-- ============================================
-- DCAI Intelligence Platform - Initial Schema
-- Run this against your Supabase PostgreSQL
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================
-- REPORTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Basic metadata
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    year INTEGER,
    category TEXT,
    page_count INTEGER,
    
    -- File references
    original_filename TEXT,
    mineru_folder TEXT,
    ragflow_doc_id TEXT,
    pdf_storage_path TEXT,
    
    -- Extracted intelligence (JSONB for flexibility)
    executive_summary TEXT,
    key_findings JSONB DEFAULT '[]',
    statistics JSONB DEFAULT '[]',
    quotes JSONB DEFAULT '[]',
    aha_moments JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    methodology TEXT,
    limitations TEXT,
    
    -- Full text for search
    full_text TEXT,
    
    -- Processing status
    processing_status TEXT DEFAULT 'pending',
    processing_error TEXT,
    processed_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for reports
CREATE INDEX IF NOT EXISTS idx_reports_source ON reports(source);
CREATE INDEX IF NOT EXISTS idx_reports_year ON reports(year);
CREATE INDEX IF NOT EXISTS idx_reports_category ON reports(category);
CREATE INDEX IF NOT EXISTS idx_reports_ragflow ON reports(ragflow_doc_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(processing_status);
CREATE INDEX IF NOT EXISTS idx_reports_fulltext ON reports USING gin(to_tsvector('english', COALESCE(full_text, '')));
CREATE INDEX IF NOT EXISTS idx_reports_title_trgm ON reports USING gin(title gin_trgm_ops);

-- ============================================
-- CONVERSATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    mode TEXT NOT NULL CHECK (mode IN ('single', 'all', 'minister')),
    report_id UUID REFERENCES reports(id),
    title TEXT,
    
    settings JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_mode ON conversations(mode);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at DESC);

-- ============================================
-- MESSAGES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    
    citations JSONB DEFAULT '[]',
    model_used TEXT,
    tokens_used INTEGER,
    
    original_content TEXT,
    was_enhanced BOOLEAN DEFAULT FALSE,
    
    agent_contributions JSONB DEFAULT '[]',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);

-- ============================================
-- NEWS ITEMS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS news_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    source TEXT,
    author TEXT,
    published_at TIMESTAMPTZ,
    
    raw_content TEXT,
    
    so_what_analysis JSONB,
    analyzed_at TIMESTAMPTZ,
    analysis_model TEXT,
    
    submitted_by UUID REFERENCES auth.users(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_url ON news_items(url);
CREATE INDEX IF NOT EXISTS idx_news_published ON news_items(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_created ON news_items(created_at DESC);

-- ============================================
-- DATA BANK TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS data_bank (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    
    type TEXT NOT NULL CHECK (type IN ('statistic', 'quote', 'finding', 'aha_moment', 'recommendation')),
    content TEXT NOT NULL,
    context TEXT,
    source_page INTEGER,
    
    tags TEXT[] DEFAULT '{}',
    topic TEXT,
    
    speaker TEXT,
    value TEXT,
    unit TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_databank_report ON data_bank(report_id);
CREATE INDEX IF NOT EXISTS idx_databank_type ON data_bank(type);
CREATE INDEX IF NOT EXISTS idx_databank_tags ON data_bank USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_databank_content ON data_bank USING gin(to_tsvector('english', content));

-- ============================================
-- PROCESSING JOBS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    type TEXT NOT NULL CHECK (type IN ('bulk_upload', 'single_reprocess')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    
    total_items INTEGER,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    
    items JSONB DEFAULT '[]',
    error TEXT,
    
    created_by UUID REFERENCES auth.users(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON processing_jobs(created_at DESC);

-- ============================================
-- USER PREFERENCES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    
    theme TEXT DEFAULT 'dark',
    default_chat_mode TEXT DEFAULT 'all',
    
    auto_enhance_queries BOOLEAN DEFAULT FALSE,
    show_agent_contributions BOOLEAN DEFAULT TRUE,
    
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- AUDIT LOG TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    
    metadata JSONB DEFAULT '{}',
    ip_address TEXT,
    user_agent TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at DESC);

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_bank ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Reports: All authenticated users can read
CREATE POLICY "Reports are viewable by authenticated users"
    ON reports FOR SELECT
    TO authenticated
    USING (true);

-- Conversations: Users can only see their own
CREATE POLICY "Users can view own conversations"
    ON conversations FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own conversations"
    ON conversations FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own conversations"
    ON conversations FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own conversations"
    ON conversations FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- Messages: Based on conversation ownership
CREATE POLICY "Users can view messages in own conversations"
    ON messages FOR SELECT
    TO authenticated
    USING (
        conversation_id IN (
            SELECT id FROM conversations WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create messages in own conversations"
    ON messages FOR INSERT
    TO authenticated
    WITH CHECK (
        conversation_id IN (
            SELECT id FROM conversations WHERE user_id = auth.uid()
        )
    );

-- News items: All authenticated users can read
CREATE POLICY "News items are viewable by authenticated users"
    ON news_items FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Users can submit news items"
    ON news_items FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = submitted_by);

-- Data bank: All authenticated users can read
CREATE POLICY "Data bank is viewable by authenticated users"
    ON data_bank FOR SELECT
    TO authenticated
    USING (true);

-- User preferences: Users can only access their own
CREATE POLICY "Users can manage own preferences"
    ON user_preferences FOR ALL
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_reports_updated_at
    BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Auto-generate conversation title from first message
CREATE OR REPLACE FUNCTION set_conversation_title()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.role = 'user' THEN
        UPDATE conversations
        SET title = LEFT(NEW.content, 100)
        WHERE id = NEW.conversation_id AND title IS NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_conversation_title
    AFTER INSERT ON messages
    FOR EACH ROW EXECUTE FUNCTION set_conversation_title();

-- ============================================
-- GRANT PERMISSIONS (for service role)
-- ============================================
-- Note: Run these with service role if needed
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
