CREATE TABLE IF NOT EXISTS ideas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(300) NOT NULL,
    description TEXT,
    submitted_by UUID REFERENCES users(id),
    votes_up INTEGER DEFAULT 0,
    votes_down INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS idea_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idea_id UUID REFERENCES ideas(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    vote_type SMALLINT CHECK (vote_type IN (-1, 1)),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(idea_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_ideas_votes ON ideas((votes_up - votes_down) DESC);
