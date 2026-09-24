# opus55-kit

A Claude Code plugin that applies the Opus 5.5 best practices so that you do not have to remember them.
Sources: Anthropic's blog "Getting the most out of Opus 5.5 in Claude and Claude Code", the guide
"Prompting Claude Opus 5.5", and the "Effort" docs page.

## What it does

| Part | When it acts | What it does |
|---|---|---|
| Standing rules (`hooks/rules.md`) | On your first prompt, and again after each compaction. Only when the model is Opus 5.5. | Adds rules to the context: when to stop, state a finish line, keep `TASKS.md`, end with "Blocked on me / Changed / Found", subagent evidence, review format, "mark what you couldn't confirm", document checks, the frontend avoid list, explore connected apps first, how to explain a choice, and what to do after a safety flag. |
| Prompt nudges | When a prompt has one of 3 habits. Only on Opus 5.5. | Shows one line: for "think carefully", for "show your reasoning", or for a long build/migrate/refactor prompt with no finish line. |
| TASKS.md continuation | When a turn ends. Only on Opus 5.5 and only in unattended runs (`claude -p`, SDK). | If this session used `TASKS.md` and it still has `- [ ]` items, it sends the model back once to finish them. |
| `opus55-audit` skill | When you ask "audit my setup for Opus 5.5". | Finds think lines and reasoning requests in your saved instructions, and checks effort and permission settings. It changes files only after you approve. |

Requires Python 3 on PATH (`python3` or `python`). Standard library only.

## Install

For one session:

```
claude --plugin-dir /path/to/opus55-kit
```

To keep it, add the folder to a plugin marketplace and run `claude plugin install opus55-kit@<marketplace>`.

## Model detection

A hook's input does not include the model. The plugin reads the model of the last reply in the
transcript. Before the first reply, it reads the `--model` flag of the `claude` process. If it still
cannot tell, it treats the model as Opus 5.5, and the rules text tells any other model to ignore it.

## Not in this plugin

- **Claude apps.** Plugins do not run there. Paste this into a project's instructions instead:

  ```
  When a step doesn't need my input, keep going. Mark anything you couldn't confirm, and say where you looked.
  When I ask you to check a document, find anything that contradicts itself: numbers, dates and names. Quote each problem and say where it is.
  When I give no design direction, don't use a cream or off-white background, italic accent words in headings, numbered "01 / 02 / 03" section labels, monospace labels, or pill-shaped buttons.
  ```

  For long chats that do not need earlier answers checked again, add: "Once you have answered something,
  treat that answer as done. Focus on what I'm asking now, and don't go back over an earlier answer unless
  I ask about it or point out a problem with it."
- **API programs.** Your program sets `max_tokens`, `thinking.display`, per-message effort and the agent
  loop. See the guide "Prompting Claude Opus 5.5".
- **Habits no hook can see:** attach the image instead of retyping it, `/fast` for back-and-forth work,
  and typing a follow-up while Claude works.
