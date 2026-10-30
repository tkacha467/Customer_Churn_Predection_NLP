#!/bin/bash

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
FRONTEND_DIR="$ROOT_DIR/Digital_Card/frontend"
PYTHON="$ROOT_DIR/.venv/bin/python"

fail() {
    printf '\n[ERROR] %s\n' "$*" >&2
    printf 'Press Return to close this window... '
    read -r _ || true
    exit 1
}

# Set Terminal window title
printf '\033]0;VRAJA AI Digital Card Launcher\007'

printf '\n======================================================\n'
printf ' VRAJA AI - Digital Business Card (Product B)\n'
printf ' Port 5174 (Frontend) + Port 8000 (Backend API)\n'
printf '======================================================\n\n'
printf '[1/3] Checking environment dependencies...\n'

[ -x "$PYTHON" ] || fail "Project Python environment not found at $PYTHON."
"$PYTHON" --version || fail "The project virtualenv Python could not be run."
"$PYTHON" -m uvicorn --version >/dev/null 2>&1 || fail "Uvicorn is missing from the project virtualenv."
command -v node >/dev/null 2>&1 || fail "Node.js was not found in PATH."
command -v npm >/dev/null 2>&1 || fail "npm was not found in PATH."
NODE="$(command -v node)"
NODE_BIN="$(dirname "$NODE")"

[ -d "$FRONTEND_DIR" ] || fail "Digital Card frontend directory not found at $FRONTEND_DIR."
[ -d "$FRONTEND_DIR/node_modules" ] || fail "Frontend dependencies are missing. Run npm install from Digital_Card/frontend."

port_listeners() {
    /usr/sbin/lsof -nP -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null || true
}

quote_shell() {
    "$PYTHON" -c 'import shlex,sys; print(shlex.quote(sys.argv[1]))' "$1"
}

create_runner() {
    local label="$1"
    runner_dir="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/digital-card-launch.XXXXXX")" || fail "Could not create temporary runner."
    runner_file="$runner_dir/$label.sh"
    runner_ready="$runner_file.started"
}

write_runner_header() {
    printf '#!/bin/bash\n'
    printf 'trap '\''rm -f "$0" "$0.started"; rmdir "$(dirname "$0")" 2>/dev/null || true'\'' EXIT\n'
    printf 'touch %s\n' "$(quote_shell "$runner_ready")"
}

launch_terminal_runner() {
    local label="$1" file="$2"
    chmod 700 "$file" || fail "Could not make runner executable."
    /usr/bin/osascript - "$file" <<'APPLESCRIPT'
on run argv
    set runnerPath to item 1 of argv
    tell application "Terminal"
        activate
        do script "/bin/bash " & quoted form of runnerPath
    end tell
end run
APPLESCRIPT
    local attempt
    for attempt in {1..20}; do
        if [ -f "$file.started" ]; then
            rm -f "$file.started"
            printf 'Terminal started the %s runner.\n' "$label"
            return 0
        fi
        sleep 0.25
    done
}

ROOT_Q="$(quote_shell "$ROOT_DIR")"
FRONTEND_Q="$(quote_shell "$FRONTEND_DIR")"
PYTHON_Q="$(quote_shell "$PYTHON")"
NODE_BIN_Q="$(quote_shell "$NODE_BIN")"

# 1. Backend on 8000
BACKEND_PID="$(port_listeners 8000 | head -n 1)"
if [ -n "$BACKEND_PID" ]; then
    printf 'Backend already running (PID %s) on port 8000.\n' "$BACKEND_PID"
else
    printf '[2/3] Opening Terminal for FastAPI backend...\n'
    create_runner backend
    {
        write_runner_header
        printf 'printf "\\033]0;VRAJA AI Shared Backend\\007"\n'
        printf 'cd %s || exit 1\n' "$ROOT_Q"
        printf 'export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1\n'
        printf 'printf "\\nStarting backend on http://127.0.0.1:8000...\\n\\n"\n'
        printf '%s -m uvicorn Backend.app.main:app --host 127.0.0.1 --port 8000 --reload\n' "$PYTHON_Q"
        printf 'result=$?\nprintf "\\nBackend exited with %%s\\n" "$result"\n/bin/bash -i\n'
    } > "$runner_file"
    launch_terminal_runner backend "$runner_file"
fi

# 2. Digital Card Frontend on 5174
CARD_PID="$(port_listeners 5174 | head -n 1)"
if [ -n "$CARD_PID" ]; then
    printf 'Digital Card frontend already running (PID %s) on port 5174.\n' "$CARD_PID"
else
    printf '[3/3] Opening Terminal for Digital Card frontend...\n'
    create_runner digital_card
    {
        write_runner_header
        printf 'printf "\\033]0;VRAJA AI Digital Card Frontend\\007"\n'
        printf 'cd %s || exit 1\n' "$FRONTEND_Q"
        printf 'export PATH=%s:"$PATH"\n' "$NODE_BIN_Q"
        printf 'printf "\\nStarting Digital Card on http://127.0.0.1:5174...\\n\\n"\n'
        printf 'npm run dev\n'
        printf 'result=$?\nprintf "\\nFrontend exited with %%s\\n" "$result"\n/bin/bash -i\n'
    } > "$runner_file"
    launch_terminal_runner digital_card "$runner_file"
fi

printf '\n======================================================\n'
printf ' Digital Business Card is ready!\n'
printf ' Public Card:  http://127.0.0.1:5174/b/default_business/card\n'
printf ' Owner Studio: http://127.0.0.1:5174/owner\n'
printf ' Backend API:  http://127.0.0.1:8000/docs\n'
printf '======================================================\n\n'

sleep 1
open "http://127.0.0.1:5174/b/default_business/card" 2>/dev/null || true
