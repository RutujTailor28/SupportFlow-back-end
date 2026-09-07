-- SupportFlow Phase 5: Classification schema
-- Tables: ticket_classifications, classification_corrections

CREATE TABLE IF NOT EXISTS ticket_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL UNIQUE REFERENCES tickets(id) ON DELETE CASCADE,
    category TEXT
        CHECK (category IN (
            'Billing', 'Technical', 'Account', 'Feature Request',
            'Shipping', 'Security', 'Other'
        )),
    subcategory TEXT,
    urgency TEXT
        CHECK (urgency IN ('critical', 'high', 'normal', 'low')),
    sentiment TEXT
        CHECK (sentiment IN ('positive', 'neutral', 'negative', 'very_negative')),
    language TEXT,
    intent_summary TEXT,
    entities JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence NUMERIC(5, 4),
    source TEXT NOT NULL DEFAULT 'ai'
        CHECK (source IN ('ai', 'manual')),
    human_corrected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS classification_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    classification_id UUID NOT NULL REFERENCES ticket_classifications(id) ON DELETE CASCADE,
    category TEXT
        CHECK (category IN (
            'Billing', 'Technical', 'Account', 'Feature Request',
            'Shipping', 'Security', 'Other'
        )),
    subcategory TEXT,
    urgency TEXT
        CHECK (urgency IN ('critical', 'high', 'normal', 'low')),
    sentiment TEXT
        CHECK (sentiment IN ('positive', 'neutral', 'negative', 'very_negative')),
    language TEXT,
    intent_summary TEXT,
    entities JSONB,
    confidence NUMERIC(5, 4),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS ticket_classifications_set_updated_at ON ticket_classifications;
CREATE TRIGGER ticket_classifications_set_updated_at
    BEFORE UPDATE ON ticket_classifications
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_ticket_classifications_ticket_id ON ticket_classifications(ticket_id);
CREATE INDEX IF NOT EXISTS idx_classification_corrections_ticket_id ON classification_corrections(ticket_id);
CREATE INDEX IF NOT EXISTS idx_classification_corrections_classification_id
    ON classification_corrections(classification_id);

GRANT ALL ON TABLE ticket_classifications TO service_role;
GRANT ALL ON TABLE classification_corrections TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE ticket_classifications TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE classification_corrections TO authenticated;

ALTER TABLE ticket_classifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE classification_corrections ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE ticket_classifications IS 'Original AI/manual classification for a ticket (immutable values after creation)';
COMMENT ON TABLE classification_corrections IS 'Human corrections applied to an AI classification';
