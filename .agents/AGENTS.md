# agentic-ai-gateway Handbook

## Universal Rules
- **Git Push Approval Rule**: NEVER run `git push` automatically. Always present implemented changes and unit test verification results, and wait for explicit user confirmation before executing any `git push` command.
- **Python Virtualenv Path**: All unit tests must be executed using:
  `/Users/gnanesh_arva/Downloads/travel-planner-v2/travel-agent-service/.venv/bin/pytest`

## Repository Standards
- **Port**: `8007` (Default)
- **Role**: Reverse Proxy API Gateway managing request correlation, rate limiting, bulkhead concurrency, GZip compression, and downstream service forwarding.
