"""opus55-kit hooks. Stdlib only. Fail-safe: any error exits 0 silently - never break a session.

  prompt  (UserPromptSubmit) - Opus 5.5 only: add rules.md once per session and again after each
          compaction; add a one-line nudge when the prompt has a habit the sources advise against.
  stop    (Stop) - Opus 5.5 and unattended runs only: if TASKS.md was used this session and still has
          unticked "- [ ]" items, send the model back once to finish them.

Model: last main-chain assistant turn in the transcript, else the --model flag of the claude
process (first prompt), else unknown. Unknown counts as Opus 5.5; rules.md says to ignore it otherwise.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MARKER = "OPUS55-RULES"
TAIL = 1048576  # read at most the last 1 MB of a transcript

# First match wins. Messages quote the blog and the guide.
NUDGES = [
    (r"\b(show|write out|reproduce|print|include) (me )?(your|the) (full |internal |complete )?"
     r"(reasoning|chain[- ]of[- ]thought|thinking|thought process)\b",
     "Opus 5.5: this phrasing can trigger the reasoning_extraction safety flag. "
     "Ask instead: 'Explain why you chose this approach in three sentences.'"),
    (r"\b(think (step[- ]by[- ]step|carefully|hard(er)?|deeply)|ultrathink)\b",
     "Opus 5.5: Opus 5.5 always thinks and decides how much. Delete 'think carefully'. "
     "For a fast reply, write 'Answer directly'. For more depth, raise effort."),
    (r"(?s)^(?=.{120,})(?!.*\b(done|until|pass(es)?|stop|finished)\b).*"
     r"\b(migrate|refactor|build|implement|audit|port|rewrite)\b",
     "Opus 5.5: a big task with no finish line. Next time, say what 'done' means "
     "(for example 'the tests pass') and when to stop and ask."),
]


def read_tail(path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        f.seek(max(0, size - TAIL))
        return f.read().decode("utf-8", errors="replace").splitlines()


def transcript_model(transcript):
    """Model of the last main-chain assistant turn. Attachment lines carry other model ids."""
    try:
        for line in reversed(read_tail(transcript)):
            if '"assistant"' not in line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("type") == "assistant" and not d.get("isSidechain"):
                return (d.get("message") or {}).get("model") or ""
    except Exception:
        pass
    return ""


def cli_model():
    """--model flag of the claude process (CLAUDE_PID). Only used before the first reply."""
    pid = os.environ.get("CLAUDE_PID", "")
    if not pid.isdigit():
        return ""
    try:
        if os.name == "nt":
            cmd = ["powershell.exe", "-NoProfile", "-Command",
                   "(Get-CimInstance Win32_Process -Filter 'ProcessId=%s').CommandLine" % pid]
        else:
            cmd = ["ps", "-o", "args=", "-p", pid]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return ""
    m = re.search(r"--model[= ]\"?([\w.\[\]-]+)", out)
    return m.group(1) if m else ""


def is_opus55(transcript):
    model = transcript_model(transcript) or cli_model()
    return not model or "opus-5-5" in model


def rules_added(transcript):
    """True if rules.md was added since the last compaction (attachment lines only)."""
    added = False
    try:
        with open(transcript, encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"compact_boundary"' in line:
                    added = False
                elif MARKER in line and '"type":"attachment"' in line:
                    added = True
    except Exception:
        pass
    return added


def on_prompt(data):
    transcript = data.get("transcript_path") or ""
    if not is_opus55(transcript):
        return
    out = []
    if not rules_added(transcript):
        with open(os.path.join(HERE, "rules.md"), encoding="utf-8") as f:
            out.append(f.read())
    prompt = (data.get("prompt") or "").strip()
    for pattern, message in NUDGES:
        if re.search(pattern, prompt, re.IGNORECASE):
            out.append("<opus55-nudge>%s Surface this note verbatim to the user at the top of your "
                       "reply, then answer their prompt.</opus55-nudge>" % message)
            break
    if out:
        print("\n".join(out))


def on_stop(data):
    # ponytail: one automatic continue per stop (stop_hook_active); the guide allows 2-3, add a counter if one is too few
    if data.get("stop_hook_active") or data.get("background_tasks"):
        return
    # unattended runs only: claude -p and the SDK set CLAUDE_CODE_SESSION_ATTENDED=0, an interactive session sets 1
    if os.environ.get("CLAUDE_CODE_SESSION_ATTENDED") != "0":
        return
    path = os.path.join(data.get("cwd") or ".", "TASKS.md")
    transcript = data.get("transcript_path") or ""
    if not os.path.isfile(path) or "opus-5-5" not in transcript_model(transcript):
        return
    # an old TASKS.md this session never touched is left alone (tool-use lines only)
    with open(transcript, encoding="utf-8", errors="replace") as f:
        if not any('"tool_use"' in line and "TASKS.md" in line for line in f):
            return
    with open(path, encoding="utf-8", errors="replace") as f:
        items = [m.strip() for m in re.findall(r"^\s*[-*] \[ \] (.+)$", f.read(), re.M)]
    if not items:
        return
    shown = "; ".join(items[:5]) + (" (+%d more)" % (len(items) - 5) if len(items) > 5 else "")
    print(json.dumps({"decision": "block", "reason":
        "Your task list in TASKS.md still has open items: %s. Continue with them. "
        "If one is blocked, say what is blocking it. If you need the user's answer to continue, "
        "say so in one line and end the turn." % shown}))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        data = json.load(sys.stdin)
        {"prompt": on_prompt, "stop": on_stop}[sys.argv[1]](data)
    except Exception:
        pass
    sys.exit(0)
