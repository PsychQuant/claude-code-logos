# Checklist Visibility

When starting any task with 3 or more steps, you MUST create a TaskCreate checklist before executing any step.

## Rules

1. **Every step = one task.** Do not combine multiple steps into a single task.
2. **Create all tasks first, then execute.** Do not start working before the full checklist exists.
3. **Creative steps get explicit names.** Name tasks by their actual output, not a vague label.
   - Bad: "Process content"
   - Good: "Read full transcript and add missing teaching points to lecture"
4. **Mark in_progress before starting, completed when done.** Do not skip status updates.
5. **Never mark a task completed if you skipped it or did it partially.**
6. **If a skill provides a task table, use it verbatim.** Do not rephrase or merge the provided tasks.

## Technical Notes

- `TaskCreate` is a Claude Code internal tool (registered via `buildTool`), NOT a shell command
- Skills' `!`command`` shell injection CANNOT call TaskCreate — it can only run shell commands
- Shell injection CAN scan for files (`ls`, `find`) to provide context for which tasks to create vs skip
- Best pattern in skills: shell injection scans materials → fixed task table with skip conditions → Claude creates tasks from table

## Why

Steps not on a visible checklist get skipped. Gawande (2009) documented that surgical checklists reduced mortality by 47%. Hales & Pronovost (2006) showed ICU infection rates dropped from 11% to 0% with a 5-item checklist. The mechanism: making steps visible prevents omission errors, especially when routine momentum carries past judgment-heavy steps.
