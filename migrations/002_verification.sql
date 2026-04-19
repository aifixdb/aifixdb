-- Add verification token column
ALTER TABLE users ADD COLUMN IF NOT EXISTS verify_token VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_users_verify_token ON users(verify_token) WHERE verify_token IS NOT NULL;
