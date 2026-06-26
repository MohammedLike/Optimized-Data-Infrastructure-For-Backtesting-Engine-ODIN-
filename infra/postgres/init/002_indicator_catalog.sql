-- StrykeX indicator catalog and quant rule templates

CREATE TABLE IF NOT EXISTS odin.indicator_catalog (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(64) NOT NULL UNIQUE,
    display_name VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL,
    indicator_type VARCHAR(32) NOT NULL,
    default_params JSONB NOT NULL DEFAULT '{}',
    precompute BOOLEAN NOT NULL DEFAULT FALSE,
    implementation_status VARCHAR(32) NOT NULL DEFAULT 'planned',
    description TEXT,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_indicator_catalog_category
    ON odin.indicator_catalog (category);

CREATE INDEX IF NOT EXISTS idx_indicator_catalog_status
    ON odin.indicator_catalog (implementation_status);

CREATE TABLE IF NOT EXISTS odin.condition_rule_templates (
    id SERIAL PRIMARY KEY,
    indicator_slug VARCHAR(64) NOT NULL REFERENCES odin.indicator_catalog (slug) ON DELETE CASCADE,
    rule_purpose VARCHAR(32) NOT NULL,
    rule_name VARCHAR(128) NOT NULL,
    left_operand VARCHAR(128),
    operator VARCHAR(32),
    right_operand VARCHAR(128),
    right_value DOUBLE PRECISION,
    logic_notes TEXT,
    priority INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (indicator_slug, rule_purpose, rule_name)
);

CREATE INDEX IF NOT EXISTS idx_condition_rules_slug
    ON odin.condition_rule_templates (indicator_slug);

CREATE INDEX IF NOT EXISTS idx_condition_rules_purpose
    ON odin.condition_rule_templates (rule_purpose);

-- Trader-facing view: indicators with rule counts
CREATE OR REPLACE VIEW odin.indicator_catalog_summary AS
SELECT
    c.slug,
    c.display_name,
    c.category,
    c.indicator_type,
    c.implementation_status,
    c.precompute,
    COUNT(r.id) AS rule_count
FROM odin.indicator_catalog AS c
LEFT JOIN odin.condition_rule_templates AS r ON c.slug = r.indicator_slug
GROUP BY c.id, c.slug, c.display_name, c.category, c.indicator_type,
         c.implementation_status, c.precompute
ORDER BY c.sort_order, c.category, c.display_name;
