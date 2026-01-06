
-- Create data_bank table if not exists
CREATE TABLE IF NOT EXISTS public.data_bank (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES public.reports(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    context TEXT,
    source_page INTEGER,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_data_bank_report_id ON public.data_bank(report_id);
CREATE INDEX IF NOT EXISTS idx_data_bank_type ON public.data_bank(type);

-- Enable RLS
ALTER TABLE public.data_bank ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS data_bank_select_policy ON public.data_bank;
DROP POLICY IF EXISTS data_bank_all_policy ON public.data_bank;

-- Allow authenticated users to read
CREATE POLICY data_bank_select_policy ON public.data_bank 
    FOR SELECT TO authenticated USING (true);

-- Allow service role full access  
CREATE POLICY data_bank_all_policy ON public.data_bank 
    FOR ALL TO service_role USING (true);
