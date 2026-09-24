# Opus 5.5 playbook

This repository holds two things:

1. **`opus55-kit`** — a Claude Code plugin. It applies the Anthropic best practices for Claude Opus 5.5
   in your sessions, so you do not have to remember them.
2. **`opus-5-5-playbook.html`** — a one-page reference. It lists 30 practices from the sources, with the
   source prompts copied word for word, and says for each one where it applies: Claude Code, the Claude
   apps, or the API.

The repository is also a plugin marketplace (`.claude-plugin/marketplace.json`, name `opus55-local`).

## Sources

All rules and prompts come from three Anthropic pages (also listed in `README.txt`):

| Source | URL |
|---|---|
| Blog: "Getting the most out of Opus 5.5 in Claude and Claude Code" (2026-09-22) | https://claude.dev/blog/getting-the-most-out-of-opus-5-5/ |
| Guide: "Prompting Claude Opus 5.5" | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5 |
| Docs: "Effort" (includes "Change effort mid-conversation", beta) | https://platform.claude.com/docs/en/build-with-claude/effort#change-effort-mid-conversation-beta |

The plugin does not add advice of its own. Each rule restates a practice from these pages.

## Install

Requires Claude Code and Python 3 on PATH (`python3` or `python`). The hooks use the standard library only.

```
claude plugin marketplace add az9713/opus-5.5-playbook
claude plugin install opus55-kit@opus55-local
```

To try it for one session without installing:

```
claude --plugin-dir /path/to/opus55-kit
```

To see the playbook page, open `opus-5-5-playbook.html` in a browser.

## What the plugin does

| Part | When it acts | What it does |
|---|---|---|
| Standing rules (`hooks/rules.md`) | On the first prompt of a session, and again after each compaction. Only when the model is Opus 5.5. | Adds 12 rules to the context: when to stop and ask, state a finish line, end with "Blocked on me / Changed / Found", keep a `TASKS.md` checklist, check subagent evidence, the merge-blocker review format, mark what you could not confirm, find contradictions in documents, the frontend avoid list, explore connected apps first, explain a choice in a few sentences, and what to do after a safety flag. |
| Prompt nudges (`hooks/opus55.py prompt`) | When a prompt has one of 3 habits. Only on Opus 5.5. | Shows one line for: "think carefully" / "think step by step", "show your reasoning" (can trigger the `reasoning_extraction` safety flag), or a long build/migrate/refactor prompt with no finish line. |
| TASKS.md continuation (`hooks/opus55.py stop`) | When a turn ends. Only on Opus 5.5, and only in unattended runs (`CLAUDE_CODE_SESSION_ATTENDED=0`, which `claude -p` and the SDK set). | If the session used `TASKS.md` and the file still has unticked `- [ ]` items, it sends the model back once to finish them. |
| `opus55-audit` skill | When you ask "audit my setup for Opus 5.5". | Finds think lines, reasoning requests and "thinking disabled" in your saved instructions. Checks the effort setting and the permission-prompt settings. Changes a file only after you approve. |

### How the plugin finds the model

A hook's input does not include the model. The plugin reads the model of the last reply in the
session transcript. Before the first reply, it reads the `--model` flag of the `claude` process. If it
still cannot tell, it treats the model as Opus 5.5. The first line of `rules.md` tells any other model
to ignore the rules, so a wrong guess costs context tokens but does not change behavior.

## How the plugin was made

The plugin came out of one Claude Code session on Opus 5.5 (2026-09-23 to 2026-09-24). The steps:

1. **Read the sources and sort the practices.** Claude read the 3 pages and listed 17 practices. For
   each one it proposed a place: a standing instruction, a hook, a skill, a setting, or a habit that
   only the user can keep.
2. **Build it into one personal setup.** The first version went into the author's own `~/.claude`:
   a section in `CLAUDE.md`, a Stop hook for `TASKS.md`, 3 prompt-check rules in a local "coach" hook,
   and `modelSettings["claude-opus-5-5"] = {"effortLevel": "medium"}` in `settings.json`.
3. **Condition on the model.** A `CLAUDE.md` section loads for every model and depends on the model
   obeying a label. So the rules moved to a file that a `UserPromptSubmit` hook adds only when the
   model is Opus 5.5.
4. **Limit the Stop hook to unattended runs.** The author runs interactive sessions in
   bypass-permissions mode, so the permission mode could not tell attended from unattended. The
   environment variable `CLAUDE_CODE_SESSION_ATTENDED` could: it was measured as `0` in `claude -p` and
   `1` in an interactive session.
5. **Write the playbook page.** A 30-card HTML page with the source prompts and a "where it applies"
   line on each card.
6. **Ask how a user adopts the practices without memorizing them.** The answer ranked 5 places for a
   practice: the model does it; set it once; remind at the moment of the mistake; load it when the task
   matches; show it when a rare event happens. Two user habits became model rules here: "state the
   finish line" and the "Blocked on me / Changed / Found" summary.
7. **Package it as a plugin.** The rules, the nudges, the Stop hook and a new audit skill went into
   `opus55-kit`, with one Python script for both hooks. `claude plugin validate` passed. The author then
   removed the personal copies (to prevent every rule and nudge from running twice) and installed the
   plugin from a local marketplace.

**Tests.** Real `claude -p` runs with only the plugin loaded:

| Test | Result |
|---|---|
| Opus 5.5 | The rules were in the context, and the "think step by step" nudge appeared. |
| Sonnet 5 | No rules and no nudge. The plugin found the model from the `--model` flag. |
| TASKS.md on Opus 5.5, unattended | The model ended with a report. The hook sent it back, and it did the open item and ticked it. |
| Old TASKS.md not used in the session | Ignored. |
| Installed copy (from the marketplace) | The rules were in the context. |

**Not tested:** the `opus55-audit` skill has not run on a real setup yet.

## What is in the plugin, and why

| Practice | Where it goes | Why there |
|---|---|---|
| Stop rules, finish line, run summary, task list, subagent evidence, review format, "mark what you couldn't confirm", document contradiction check, frontend avoid list, explore connected apps first, explain a choice briefly | Standing rules (`rules.md`) | These are the model's work, not the user's. Standing instructions let the user write them zero times. |
| Recovery after a safety flag (`/model`, Esc Esc, `/config`, `/feedback`) | Standing rules, marked "applies to any model" | The flag is rare, so the user will not remember the steps. After a flag, the new model reads the rule and can tell the user. |
| No "think carefully", no "show your reasoning", give a finish line | Prompt nudges | Only the user can change what they type. A one-line note at the moment of the habit is the only automatic reminder possible. |
| Continue open items when a run stops halfway | Stop hook | This must happen with no one watching, and the model cannot remind itself after its turn ends. |
| Delete think lines from saved instructions, set effort to `medium`, keep permission prompts for destructive commands | Audit skill | These are one-time fixes. After one audit, no one needs to remember them. |

## What is not in the plugin, and why

| Practice | Why not |
|---|---|
| "Treat an earlier answer as done" | The guide says it makes the model less likely to point out a mistake in an earlier answer. The plugin README gives it as an opt-in line for long chats. |
| The long system-prompt paragraph for unattended runs | The guide says to leave it out of work where a person is present. The 2-sentence stop rule from the blog is used instead. |
| 2–3 automatic continues | The Stop hook sends the model back once in a row (the built-in `stop_hook_active` flag). A counter would add state. Add it only if one continue is too few. |
| API settings: `max_tokens` 128,000, `thinking.display: "updates"`, per-message effort (beta header `mid-conversation-output-config-2026-07-01`), time budgets such as `elapsed 340s / 1200s`, a reminder after 5 silent steps, refusal fallback | Claude Code sets these itself. They matter only when you write your own agent loop. See the guide. |
| Marking pasted text, showing progress notes | Claude Code already does both (`<pasted_content>` tags, progress updates). |
| Claude apps (claude.ai, desktop, mobile) | Plugins do not run there. `opus55-kit/README.md` has a text to paste into a project's instructions. |
| Attach the image instead of retyping it, `/fast` for back-and-forth work, add details while the model works, ask for the finished file | A hook needs a word in the prompt or an event to react to. These habits have neither. The playbook page covers them. |
| Separate skills for review, document checks and subagent audits | A skill edit applies to every model. These rules had to apply to Opus 5.5 only, so they went into the gated rules file. The cost: about 600 tokens of context in each Opus 5.5 session. |

## Known limits

- On a first prompt without `--model`, the plugin assumes Opus 5.5.
- A `/model` switch during a session does not remove rules that were already added. The first line of
  `rules.md` tells the new model to ignore them, except the safety-flag rule.
- A `/loop` in an interactive session counts as attended, so the Stop hook does not run there.
- While a used `TASKS.md` has open items in an unattended run, the Stop hook acts on every turn, not
  once per session. Tick the items or delete the file to stop it.

## Layout

```
.claude-plugin/marketplace.json   marketplace "opus55-local"
opus55-kit/                       the plugin (see opus55-kit/README.md)
  .claude-plugin/plugin.json
  hooks/hooks.json                UserPromptSubmit + Stop
  hooks/opus55.py                 both hooks, stdlib only, exits 0 on any error
  hooks/rules.md                  the 12 standing rules
  skills/opus55-audit/SKILL.md    one-time setup audit
opus-5-5-playbook.html            30-practice reference page
README.txt                        the 3 source URLs
```

## License

MIT (see `opus55-kit/.claude-plugin/plugin.json`).
