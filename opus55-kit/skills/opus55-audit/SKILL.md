---
name: opus55-audit
description: One-time check of a Claude Code setup against the Opus 5.5 best practices. Finds "think carefully" lines and requests to show reasoning in saved instructions, checks the effort setting, and checks that permission prompts stay on for destructive commands. Use when the user says "audit my setup for Opus 5.5", "Opus 5.5 setup check", "am I ready for Opus 5.5", or asks what in their instructions conflicts with Opus 5.5.
---

# Opus 5.5 setup audit

Report first. Change a file only after the user approves the change.

## 1. Find the saved instructions

Use Glob, then Grep. Do not guess paths. Search these places when they exist:

- `~/.claude/CLAUDE.md`, `./CLAUDE.md`, `./.claude/CLAUDE.md`, `./CLAUDE.local.md`
- `~/.claude/skills/*/SKILL.md`, `./.claude/skills/*/SKILL.md`
- `~/.claude/agents/*.md`, `./.claude/agents/*.md`
- `~/.claude/output-styles/*.md`

## 2. Search for lines the sources advise against

Grep with case-insensitive matching:

| Finding | Pattern | Why (source) |
|---|---|---|
| Think instruction | `think (step[- ]by[- ]step\|carefully\|hard\|harder\|deeply)\|ultrathink` | Opus 5.5 always thinks and decides how much. Removing such a line made replies start sooner with no clear drop in quality (blog §1, guide). |
| Reasoning request | `(show\|write out\|reproduce\|print\|include) (me )?(your\|the) (full \|internal \|complete )?(reasoning\|chain[- ]of[- ]thought\|thinking\|thought process)` | Can be declined as `reasoning_extraction` (blog §5, guide). |
| Thinking off | `thinking.{0,20}disabled` | Returns a 400 error on Opus 5.5 at every effort level (effort docs). |

For each hit, propose a rewrite. A think instruction is usually deleted, or replaced with "Answer directly." for speed. A reasoning request becomes "Explain why you chose this approach in three sentences."

Do not propose edits to files under `~/.claude/plugins/` or to synced skills. An update overwrites them. List them as "cannot fix locally".

## 3. Check the settings

Read `~/.claude/settings.json` and `./.claude/settings.json`.

- **Effort.** Report `effortLevel` and `modelSettings["claude-opus-5-5"]`. The Opus 5.5 default is `medium`, and the guide says to start there, set it explicitly, and keep `xhigh` and `max` for measured gains. If neither key is set, propose `"modelSettings": {"claude-opus-5-5": {"effortLevel": "medium"}}`.
- **Permission prompts.** If `permissions.defaultMode` is `bypassPermissions`, or `skipDangerousModePermissionPrompt` is `true`, say so. The blog says: keep permission prompts on for destructive commands.

## 4. Check the stop rule

Search CLAUDE.md for a rule about when to stop and ask. If there is none, propose the blog's rule:

```
When a step doesn't need my input, keep going. Put status notes in the
same message as your next action.
Stop and ask only when you can't continue without me, or before anything
destructive: deleting data, force-pushing, or changing anything outside
this repository.
```

If the opus55-kit plugin is on, its rules already carry this for Opus 5.5 sessions. Say so, and propose the CLAUDE.md rule only if the user wants it for other models too.

## 5. Report

One table: file:line, finding, proposed change. Then the settings findings. Then ask which changes to apply. Apply only those.
