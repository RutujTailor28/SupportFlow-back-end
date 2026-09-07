-- SupportFlow Phase 7: Routing rules schema

CREATE TABLE IF NOT EXISTS routing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    rule_order INT NOT NULL DEFAULT 1,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    match_type TEXT NOT NULL DEFAULT 'ALL'
        CHECK (match_type IN ('ALL', 'ANY')),
    conditions JSONB NOT NULL DEFAULT '[]'::jsonb,
    actions JSONB NOT NULL DEFAULT '{}'::jsonb,
    matches_last_30_days INT NOT NULL DEFAULT 0,
    last_triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS routing_rules_set_updated_at ON routing_rules;
CREATE TRIGGER routing_rules_set_updated_at
    BEFORE UPDATE ON routing_rules
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_routing_rules_order ON routing_rules(rule_order);
CREATE INDEX IF NOT EXISTS idx_routing_rules_enabled ON routing_rules(enabled);

GRANT ALL ON TABLE routing_rules TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE routing_rules TO authenticated;

ALTER TABLE routing_rules ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE routing_rules IS 'Deterministic ticket routing rules evaluated in order; first match wins';
