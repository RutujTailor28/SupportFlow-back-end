-- SupportFlow Phase 2: Core schema
-- Tables: profiles, customers, tickets, ticket_messages
-- Run once in Supabase SQL Editor or via: python scripts/apply_core_schema.py

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------------
-- profiles — application users (support agents / admins)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id UUID UNIQUE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    avatar_url TEXT,
    role TEXT NOT NULL DEFAULT 'agent'
        CHECK (role IN ('admin', 'agent', 'viewer')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- customers — support customers who submit tickets
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    avatar_url TEXT,
    company TEXT,
    plan TEXT NOT NULL DEFAULT 'Free'
        CHECK (plan IN ('Free', 'Pro', 'Enterprise')),
    is_vip BOOLEAN NOT NULL DEFAULT FALSE,
    joined_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- ticket number sequence (matches frontend format #TK-48291)
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS ticket_number_seq START WITH 48291;

CREATE OR REPLACE FUNCTION generate_ticket_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ticket_number IS NULL OR BTRIM(NEW.ticket_number) = '' THEN
        NEW.ticket_number := '#TK-' || LPAD(nextval('ticket_number_seq')::TEXT, 5, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- tickets — core support tickets
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number TEXT NOT NULL UNIQUE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'web'
        CHECK (channel IN ('web', 'email', 'chat', 'phone', 'api')),
    status TEXT NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'open', 'pending', 'resolved', 'closed')),
    priority TEXT NOT NULL DEFAULT 'normal'
        CHECK (priority IN ('critical', 'high', 'normal', 'low')),
    category TEXT
        CHECK (category IN (
            'Billing', 'Technical', 'Account', 'Feature Request',
            'Shipping', 'Security', 'Other'
        )),
    sentiment TEXT
        CHECK (sentiment IN ('positive', 'neutral', 'negative', 'very_negative')),
    assigned_team TEXT,
    assigned_agent_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    first_response_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    sla_due_at TIMESTAMPTZ
);

DROP TRIGGER IF EXISTS tickets_set_ticket_number ON tickets;
CREATE TRIGGER tickets_set_ticket_number
    BEFORE INSERT ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION generate_ticket_number();

DROP TRIGGER IF EXISTS profiles_set_updated_at ON profiles;
CREATE TRIGGER profiles_set_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS customers_set_updated_at ON customers;
CREATE TRIGGER customers_set_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS tickets_set_updated_at ON tickets;
CREATE TRIGGER tickets_set_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- ticket_messages — conversation on a ticket
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ticket_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    sender_type TEXT NOT NULL
        CHECK (sender_type IN ('customer', 'agent', 'system', 'ai')),
    sender_name TEXT NOT NULL,
    sender_avatar TEXT,
    body TEXT NOT NULL,
    direction TEXT NOT NULL
        CHECK (direction IN ('in', 'out')),
    attachments JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
    ai_confidence NUMERIC(5, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_tickets_customer_id ON tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned_team ON tickets(assigned_team);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket_id ON ticket_messages(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_messages_created_at ON ticket_messages(created_at);

-- ---------------------------------------------------------------------------
-- grants for Supabase PostgREST (service role bypasses RLS)
-- ---------------------------------------------------------------------------
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role, authenticated;

GRANT ALL ON TABLE profiles TO service_role;
GRANT ALL ON TABLE customers TO service_role;
GRANT ALL ON TABLE tickets TO service_role;
GRANT ALL ON TABLE ticket_messages TO service_role;
GRANT USAGE, SELECT ON SEQUENCE ticket_number_seq TO service_role, authenticated;

-- ---------------------------------------------------------------------------
-- row level security (enabled; service role bypasses)
-- ---------------------------------------------------------------------------
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_messages ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE profiles IS 'Application users (support agents and admins)';
COMMENT ON TABLE customers IS 'Support customers who submit tickets';
COMMENT ON TABLE tickets IS 'Core support tickets';
COMMENT ON TABLE ticket_messages IS 'Messages on support tickets';
