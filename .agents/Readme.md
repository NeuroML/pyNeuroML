# Agent Session Summaries

Directory for storing summaries from chats with coding agents for future context.

## Session File Format

Based on Claude Code's session memory structure.

```markdown
# Session: YYYY-MM-DD

**Authoring agent:** <agent-name>

## Objective
Brief 1-2 sentence overview of what was discussed/accomplished.

## Completed
- Completed item 1
- Completed item 2

## Errors and Lessons
- Lesson learned (from error)

## Open Questions
- Question 1

## Notes
Any other relevant context for future agents

## References
- [Title](URL) - brief description
```

## Naming Convention

Session files should be named with the date:
```
YYYY-MM-DD.md
```

## Guidelines

- **Be concise**: Logs are added to agent context. Aim for 5-10 lines total. Focus on decisions and outcomes, not task-by-task details.
- **Focus on continuity**: Capture what's needed to continue work in future sessions.
- **Omit routine work**: Don't log every lint fix or commit unless noteworthy.
- **Preserve information**: When updating a session log, do not remove existing content. Merge new information with what's already there.
