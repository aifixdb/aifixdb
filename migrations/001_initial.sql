CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    api_key_hash VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS problems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(300) NOT NULL,
    error_message TEXT,
    stack TEXT[] NOT NULL DEFAULT '{}',
    context TEXT,
    solution TEXT NOT NULL,
    environment JSONB,
    submitted_by UUID REFERENCES users(id),
    votes_up INTEGER DEFAULT 0,
    votes_down INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(error_message, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(solution, '')), 'C') ||
        setweight(to_tsvector('english', coalesce(context, '')), 'D')
    ) STORED
);

CREATE TABLE IF NOT EXISTS votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    problem_id UUID REFERENCES problems(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    vote_type SMALLINT CHECK (vote_type IN (-1, 1)),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(problem_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_problems_search ON problems USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_problems_stack ON problems USING GIN(stack);
CREATE INDEX IF NOT EXISTS idx_problems_error_trgm ON problems USING GIN(error_message gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_problems_created ON problems(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_problems_votes ON problems((votes_up - votes_down) DESC);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
