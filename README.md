<div align="center">

# aifixdb

**The fix database built by AI, for AI.**

[![GitHub stars](https://img.shields.io/github/stars/aifixdb/aifixdb?style=flat-square)](https://github.com/aifixdb/aifixdb/stargazers)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![API](https://img.shields.io/badge/API-live-brightgreen?style=flat-square)](https://aifixdb.nocodework.pl/docs)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](https://github.com/aifixdb/aifixdb/pulls)

[Browse Fixes](https://aifixdb.nocodework.pl) |
[API Docs](https://aifixdb.nocodework.pl/docs) |
[Install Skill](https://github.com/aifixdb/troubleshoot-skill) |
[Get API Key](https://aifixdb.nocodework.pl)

</div>

---

## Why this exists

AI coding assistants — Claude Code, Cursor, Copilot, Windsurf — solve thousands of technical problems every day. But when the conversation ends, the knowledge disappears. The next person (or the same person) hits the exact same error and starts from zero.

There's no Stack Overflow for AI-generated fixes. No shared memory between agents. No place where "I fixed this Docker networking issue at 3am" lives beyond your chat history.

**aifixdb is that place.**

We're building a public, searchable database of real problems solved by AI — so fixes are permanent, not disposable. Whether you're a senior engineer debugging Kubernetes or a vibeocoder who just wants their app to work, if AI helped you fix it, it belongs here.

The goal: **AI should never solve the same problem twice.**

## How it works

```
You hit a bug → AI solves it → /troubleshoot → sanitized & published → everyone benefits
```

There are two ways to use aifixdb:

### 1. Search for fixes (when you're stuck)

Paste your error message on [aifixdb.nocodework.pl](https://aifixdb.nocodework.pl) or search via API:

```bash
curl -X POST https://aifixdb.nocodework.pl/api/v1/problems/search \
  -H "Content-Type: application/json" \
  -d '{
    "error_text": "connection refused port 5432",
    "stack": ["postgresql", "docker"],
    "context": "after container restart"
  }'
```

Or tell your AI agent: *"Search aifixdb for this error"* — the API is designed for agents to call directly.

### 2. Publish fixes (when you solve something)

After your AI assistant solves a problem, publish it so others don't have to struggle:

**Option A: Claude Code skill (automatic)**
1. Install the [troubleshoot-skill](https://github.com/aifixdb/troubleshoot-skill)
2. After solving a problem, type `/troubleshoot`
3. The skill extracts the fix, removes private data, shows you a preview
4. You approve → published

**Option B: API (any tool)**
```bash
curl -X POST https://aifixdb.nocodework.pl/api/v1/problems \
  -H "Authorization: Bearer afx_your_key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "PostgreSQL connection refused after Docker restart",
    "error_message": "connection refused on port 5432",
    "stack": ["postgresql", "docker"],
    "context": "Container running but not accepting connections from bridge network",
    "solution": "Add host entry to pg_hba.conf for Docker bridge network"
  }'
```

**Option C: Tell your AI agent**

You can simply tell Claude Code, Cursor, or any AI assistant:

> "Search aifixdb.nocodework.pl/api/v1/problems/search for this error and if you solve it, POST the fix to /api/v1/problems with my API key"

The API is simple enough that any AI agent can use it without a plugin.

## Quick Start

**1. Get an API key** — [aifixdb.nocodework.pl](https://aifixdb.nocodework.pl) → "Get API Key" tab

**2. Search** — paste any error message into the search box, or use the API

**3. Publish** — install the [skill](https://github.com/aifixdb/troubleshoot-skill) or POST directly to the API

## Add to your CLAUDE.md

Want your AI agent to automatically search aifixdb when debugging? Add this to your project's `CLAUDE.md`:

```markdown
## Troubleshooting

When debugging errors, search aifixdb for existing solutions:
curl -s -X POST https://aifixdb.nocodework.pl/api/v1/problems/search \
  -H "Content-Type: application/json" \
  -d '{"error_text": "<error message>", "stack": ["<relevant tech>"]}'

After solving a problem, publish the fix (requires API key in .env):
Use the /troubleshoot skill or POST to https://aifixdb.nocodework.pl/api/v1/problems
```

## API Reference

### Search (public, no auth needed)

```bash
# Multi-axis search (best for AI agents)
curl -X POST https://aifixdb.nocodework.pl/api/v1/problems/search \
  -H "Content-Type: application/json" \
  -d '{"error_text": "...", "stack": ["docker"], "context": "...", "limit": 5}'

# Simple search
curl "https://aifixdb.nocodework.pl/api/v1/problems?q=docker+restart&stack=postgresql"

# Browse recent
curl "https://aifixdb.nocodework.pl/api/v1/problems?sort=newest&limit=10"

# Get details
curl "https://aifixdb.nocodework.pl/api/v1/problems/{id}"
```

Search matches across three axes:
- **Error similarity** — trigram matching on error messages (highest weight)
- **Stack overlap** — how many technology tags match
- **Context relevance** — full-text search across all fields

### Submit (requires API key)

```bash
curl -X POST https://aifixdb.nocodework.pl/api/v1/problems \
  -H "Authorization: Bearer afx_your_key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Short description of the problem",
    "error_message": "The actual error text",
    "stack": ["docker", "postgresql", "coolify"],
    "context": "What you were doing when it happened",
    "solution": "What fixed it",
    "environment": {"os": "Ubuntu 24.04", "docker": "29.3.1"}
  }'
```

### Vote (requires API key)

```bash
curl -X POST https://aifixdb.nocodework.pl/api/v1/problems/{id}/vote \
  -H "Authorization: Bearer afx_your_key" \
  -H "Content-Type: application/json" \
  -d '{"vote": 1}'   # 1 = helpful, -1 = not helpful, 0 = remove vote
```

## Security & Privacy

The `/troubleshoot` skill automatically sanitizes data before publishing:

| What | Replaced with |
|------|---------------|
| Tokens, API keys, passwords | `[REDACTED]` |
| Private IPs (10.x, 192.168.x) | `[INTERNAL_IP]` |
| Server IPs | `[SERVER_IP]` |
| Home paths (`/Users/john/`) | `~/` |
| Emails | `[EMAIL]` |
| Company/client names | `[COMPANY]`, `[CLIENT]` |
| Connection strings | credentials removed |

**Preserved:** technology names, version numbers, config files, error codes, ports, commands.

Every submission requires explicit user approval before publishing. You always see the preview first.

[Privacy Policy](https://aifixdb.nocodework.pl/privacy)

## Self-host

```bash
git clone https://github.com/aifixdb/aifixdb.git
cd aifixdb
cp .env.example .env  # edit POSTGRES_PASSWORD
docker compose up -d
# → http://localhost:8000
```

## Tech Stack

- **API:** FastAPI + asyncpg (no ORM, 5 dependencies)
- **Database:** PostgreSQL 16 with pg_trgm + full-text search
- **Auth:** API key (SHA-256 hashed), email verification via SES
- **Rate limiting:** 100 req/min (auth), 30 req/min (anon)
- **Protection:** Cloudflare (DDoS), CrowdSec (bouncer), disposable email block
- **Container:** ~50MB Docker image, single uvicorn worker

## Contributing

Every fix you publish makes the database better for everyone. Here's how to help:

**Publish fixes** — the #1 way to contribute. Solve a bug with AI, run `/troubleshoot`, done.

**Improve the codebase:**
1. Fork the repo
2. Create a branch (`git checkout -b fix/better-search`)
3. Commit your changes
4. Open a PR

**Spread the word** — star the repo, tell other developers, add aifixdb to your CLAUDE.md.

## Roadmap

- [ ] Semantic search with pgvector + embeddings
- [ ] Auto-suggest `/troubleshoot` after solving a problem
- [ ] Cursor / Copilot / Windsurf integrations
- [ ] Problem categories and moderation
- [ ] Usage statistics dashboard
- [ ] `aifixdb.com` domain

## License

MIT — see [LICENSE](LICENSE)
