-- SupportFlow Phase 8: Knowledge base schema
-- Basic KB article CRUD only — no RAG/embeddings pipeline yet

CREATE TABLE IF NOT EXISTS kb_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL
        CHECK (category IN (
            'Billing', 'Technical', 'Account', 'Features',
            'Feature Request', 'Shipping', 'Security'
        )),
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    content TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('indexed', 'processing', 'failed', 'draft', 'archived')),
    chunks_count INT NOT NULL DEFAULT 0,
    embedding_model TEXT NOT NULL DEFAULT 'text-embedding-004',
    view_count INT NOT NULL DEFAULT 0,
    helpful_votes INT NOT NULL DEFAULT 0,
    ai_usage_count INT NOT NULL DEFAULT 0,
    last_indexed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS kb_articles_set_updated_at ON kb_articles;
CREATE TRIGGER kb_articles_set_updated_at
    BEFORE UPDATE ON kb_articles
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_kb_articles_slug ON kb_articles(slug);
CREATE INDEX IF NOT EXISTS idx_kb_articles_category ON kb_articles(category);
CREATE INDEX IF NOT EXISTS idx_kb_articles_status ON kb_articles(status);
CREATE INDEX IF NOT EXISTS idx_kb_articles_created_at ON kb_articles(created_at DESC);

GRANT ALL ON TABLE kb_articles TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE kb_articles TO authenticated;
GRANT SELECT ON TABLE kb_articles TO anon;

ALTER TABLE kb_articles ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE kb_articles IS 'Knowledge base articles for support replies (CRUD only in Phase 8; RAG later)';
