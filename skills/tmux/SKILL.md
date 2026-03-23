---
name: tmux
description: "Trigger: /tmux <action>. Deterministically manage a private tmux server (isolated socket) for TTY-required workflows: create session, run command, capture output, and clean up safely."
---

# tmux

## Trigger contract

Trigger when the user sends:
- `/tmux <action> [args...]`

Supported actions:
- `start` — create (or ensure) a tmux session on an isolated socket
- `run` — send a single shell command to a target pane
- `capture` — capture recent output from a target pane
- `stop` — kill a session
- `status` — list sessions/panes for the isolated socket

If the action is missing or not one of the supported actions, return the exact error in **Failure modes**.

## Use

Use this skill when you need a real TTY (interactive programs, REPLs, terminal UIs) and you want deterministic control and reproducible capture of output. It uses an isolated tmux socket so it does not interfere with any other tmux server.

## Inputs

A single line command.

Parameters (by action):

### start
- `session=<name>` (optional, default: `openclaw`)
- `shell=<command>` (optional, default: `$SHELL -l`)

Example:
- `/tmux start session=repl`

### run
- `session=<name>` (required)
- `target=<session:window.pane>` (optional, default: `<session>:0.0`)
- `cmd=<shell command>` (required)

Example:
- `/tmux run session=repl cmd=python3 -q`

### capture
- `target=<session:window.pane>` (required)
- `lines=<n>` (optional, default: 200, max: 2000)

Example:
- `/tmux capture target=repl:0.0 lines=200`

### stop
- `session=<name>` (required)

Example:
- `/tmux stop session=repl`

### status
(no args)

## Outputs

Plain text.

### Output A — Success
TMUX_STATUS: OK
SOCKET: <path>
SESSION: <name or empty>
DETAILS:
- <one line per action result>

### Output B — Error
Output exactly one line starting with `ERROR:` (see Failure modes).

## Deterministic workflow (must follow)

### Tooling
- `exec`

### Global caps (hard limits)
- Max sessions managed per run: **1**
- Max capture lines: **2000**
- Max command length for `run`: **500** characters
- Exec timeout per tmux command: **20 seconds**

### Boundary rules (privacy + safety)

- Use an isolated socket only.
- Never attach interactively (no `tmux attach`), only create/send/capture/list/kill.
- Never run destructive shell commands via `run` if they contain (case-insensitive substring match):
  - `rm -rf`, `mkfs`, `:(){`, `dd if=`
- Never run commands that attempt privilege escalation: `sudo`.

### Step 1 — Compute socket path
Set:
- `SOCKET_DIR=${CLAWDBOT_TMUX_SOCKET_DIR:-${TMPDIR:-/tmp}/clawdbot-tmux-sockets}`
- `SOCKET=$SOCKET_DIR/clawdbot.sock`

### Step 2 — Implement each action

#### start
Run (single exec command):
```bash
SOCKET_DIR="${CLAWDBOT_TMUX_SOCKET_DIR:-${TMPDIR:-/tmp}/clawdbot-tmux-sockets}" && mkdir -p "$SOCKET_DIR" && SOCKET="$SOCKET_DIR/clawdbot.sock" && tmux -S "$SOCKET" has-session -t "SESSION" 2>/dev/null || tmux -S "$SOCKET" new-session -d -s "SESSION" -n shell
```

#### status
Run:
```bash
SOCKET_DIR="${CLAWDBOT_TMUX_SOCKET_DIR:-${TMPDIR:-/tmp}/clawdbot-tmux-sockets}" && SOCKET="$SOCKET_DIR/clawdbot.sock" && tmux -S "$SOCKET" list-sessions -F '#{session_name}'
```

#### run
Before executing, enforce command caps/denylist.

Run:
```bash
SOCKET_DIR="${CLAWDBOT_TMUX_SOCKET_DIR:-${TMPDIR:-/tmp}/clawdbot-tmux-sockets}" && SOCKET="$SOCKET_DIR/clawdbot.sock" && tmux -S "$SOCKET" send-keys -t "TARGET" -l -- "CMD" && tmux -S "$SOCKET" send-keys -t "TARGET" Enter
```

#### capture
Run:
```bash
SOCKET_DIR="${CLAWDBOT_TMUX_SOCKET_DIR:-${TMPDIR:-/tmp}/clawdbot-tmux-sockets}" && SOCKET="$SOCKET_DIR/clawdbot.sock" && tmux -S "$SOCKET" capture-pane -p -J -t "TARGET" -S -LINES
```

#### stop
Run:
```bash
SOCKET_DIR="${CLAWDBOT_TMUX_SOCKET_DIR:-${TMPDIR:-/tmp}/clawdbot-tmux-sockets}" && SOCKET="$SOCKET_DIR/clawdbot.sock" && tmux -S "$SOCKET" kill-session -t "SESSION"
```

## Failure modes

Return exactly one of these lines and nothing else:

- Missing/invalid action:
  - `ERROR: invalid_action. Use: /tmux start|run|capture|stop|status`

- tmux not installed:
  - `ERROR: tmux_missing. Install tmux and retry.`

- Session/target missing:
  - `ERROR: missing_required_args. Provide required session/target/cmd fields.`

- Command denied:
  - `ERROR: command_denied. Refusing to run destructive or privileged commands.`

- tmux command failed:
  - `ERROR: tmux_failed. tmux returned non-zero.`

## Toolset

- `exec`

## Acceptance tests

1. **Behavioral (negative): invalid action**
   - Run: `/tmux`
   - Expected output (exact): `ERROR: invalid_action. Use: /tmux start|run|capture|stop|status`

2. **Behavioral: start creates session deterministically**
   - Run: `/tmux start session=test-sess`
   - Expected: output contains `TMUX_STATUS: OK` and `SESSION: test-sess`.

3. **Behavioral: run sends keys and capture returns output**
   - Run: `/tmux run session=test-sess target=test-sess:0.0 cmd=echo hello`
   - Then: `/tmux capture target=test-sess:0.0 lines=50`
   - Expected: capture output contains `hello`.

4. **Behavioral (negative): deny rm -rf**
   - Run: `/tmux run session=test-sess cmd=rm -rf /`
   - Expected output (exact): `ERROR: command_denied. Refusing to run destructive or privileged commands.`

5. **Behavioral: stop kills session**
   - Run: `/tmux stop session=test-sess`
   - Expected: output contains `TMUX_STATUS: OK`.

6. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/tmux/SKILL.md
```
Expected: `PASS`.

7. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/tmux/SKILL.md
```
Expected: `PASS`.
