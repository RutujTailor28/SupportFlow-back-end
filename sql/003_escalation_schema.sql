-- SupportFlow Phase 6: Escalation schema
-- One ticket can have MULTIPLE escalation records (ticket_id is NOT unique)

CREATE TABLE IF NOT EXISTS ticket_escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    reason TEXT NOT NULL
        CHECK (reason IN (
            'Churn Risk Detected',
            'Legal Language',
            'SLA Risk',
            'Repeat Contact',
            'Executive Escalation',
            'Security Threat'
        )),
    trigger_phrases JSONB NOT NULL DEFAULT '[]'::jsonb,
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    source TEXT NOT NULL DEFAULT 'manual'
        CHECK (source IN ('manual', 'ai', 'rule', 'detection')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ticket_escalations_ticket_id ON ticket_escalations(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_escalations_reason ON ticket_escalations(reason);
CREATE INDEX IF NOT EXISTS idx_ticket_escalations_acknowledged ON ticket_escalations(acknowledged);
CREATE INDEX IF NOT EXISTS idx_ticket_escalations_created_at ON ticket_escalations(created_at DESC);

GRANT ALL ON TABLE ticket_escalations TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE ticket_escalations TO authenticated;

ALTER TABLE ticket_escalations ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE ticket_escalations IS 'Escalation triggers for a ticket — multiple rows allowed per ticket';
