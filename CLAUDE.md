# AGENTS.md - Neuroml-ai Project

This file contains common guidelines for all coding agents working on the neuroml-ai project.

## Project Structure

The project contains multiple Python packages:

- [code_ai_pkg/AGENTS.md](code_ai_pkg/AGENTS.md) - AI assisted coding for NeuroML
- [mcp_pkg/AGENTS.md](mcp_pkg/AGENTS.md) - MCP server for NeuroML
- [rag_pkg/AGENTS.md](rag_pkg/AGENTS.md) - Generic RAG implementation
- [utils_pkg/AGENTS.md](utils_pkg/AGENTS.md) - Shared utilities

Consult the relevant package's AGENTS.md for package-specific commands and architecture guidelines.

## Development Workflow

### Session Logging

At the start of each session, check the `.agents/` folder for previous session logs (named `YYYY-MM-DD.md`) to understand where work left off. Use the template in `.agents/README.md`.

### Pre-commit Requirements
- All code must pass ruff linting and formatting
- Import sorting is mandatory
- No trailing whitespace or large files
- Line endings must be Unix format

### Git Conventions
- Never stage or commit without explicit user approval
- When creating new files, use `git add --intent-to-add <file>` so they appear in `git diff`
- Flag large changes and suggest breaking them into smaller, focused commits for provenance and clarity
- Use conventional commit messages when possible
- Include relevant issue numbers in commit messages
- Keep commits focused and atomic
- Ensure all tests pass before pushing

## Security Considerations

### Code Safety
- Avoid eval() and exec() with user input
- Sanitize all file paths and inputs
- Implement proper access controls
- Use HTTPS for all external communications
- Never log sensitive information or credentials

### Comments
- Never remove TODO, FIXME, NOTE, or other comments from the codebase
- Preserve all existing comments during refactoring unless explicitly asked to remove them

This file should be updated as the project evolves. All agents should familiarize themselves with these guidelines before making changes to the codebase.
