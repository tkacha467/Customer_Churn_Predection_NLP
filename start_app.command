#!/bin/bash

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
FRONTEND_DIR="$ROOT_DIR/frontend"
PYTHON="$ROOT_DIR/.venv/bin/python"

fail() {
    printf '\n[ERROR] %s\n' "$*" >&2
    printf 'Press Return to close this window... '
    read -r _ || true
    exit 1
}

# Set Terminal window title for diagnostics
printf '\033]0;Nasta Ghar Diagnostics\007'

printf '\n======================================================\n'
printf ' NASTA GHAR - Google Review Assistant (macOS Launcher)\n'
printf ' Trilingual Review AI: English, Hinglish, Gujlish\n'
printf '======================================================\n\n'
printf '[1/4] Checking local development dependencies...\n'

[ -x "$PYTHON" ] || fail "Project Python environment not found at $PYTHON."
"$PYTHON" --version || fail "The project virtualenv Python could not be run."
"$PYTHON" -m uvicorn --version >/dev/null 2>&1 || fail "Uvicorn is missing from the project virtualenv."
command -v node >/dev/null 2>&1 || fail "Node.js was not found in PATH."
command -v npm >/dev/null 2>&1 || fail "npm was not found in PATH."
NODE="$(command -v node)"
NODE_BIN="$(dirname "$NODE")"
TERMINAL_APP=""
for candidate in /System/Applications/Utilities/Terminal.app /Applications/Utilities/Terminal.app; do
    if [ -x "$candidate/Contents/MacOS/Terminal" ]; then
        TERMINAL_APP="$candidate"
        break
    fi
done
[ -n "$TERMINAL_APP" ] || fail "Terminal.app was not found in the standard macOS application locations."
[ -d "$FRONTEND_DIR" ] || fail "Frontend directory not found at $FRONTEND_DIR."
[ -d "$FRONTEND_DIR/node_modules" ] || fail "Frontend dependencies are missing. Run npm ci from the frontend directory first."
[ -x "$FRONTEND_DIR/node_modules/.bin/vite" ] || fail "Vite is missing from frontend/node_modules. Run npm ci from the frontend directory first."

port_listeners() {
    /usr/sbin/lsof -nP -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null || true
}

project_listener_state() {
    local port="$1" expected_cwd="$2" expected_exec="$3" pids pid actual_cwd actual_exec
    pids="$(port_listeners "$port")"
    [ -n "$pids" ] || { printf 'free'; return; }
    for pid in $pids; do
        actual_cwd="$(/usr/sbin/lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1)"
        actual_exec="$(/usr/sbin/lsof -a -p "$pid" -d txt -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1)"
        if [ "$actual_cwd" != "$expected_cwd" ] || [ "${actual_exec##*/}" != "$expected_exec" ]; then
            printf 'conflict:%s' "$pid"
            return
        fi
    done
    printf 'project:%s' "$(printf '%s ' $pids | sed 's/[[:space:]]*$//')"
}

probe_service() {
    local kind="$1" timeout="${2:-2}"
    "$PYTHON" - "$kind" "$timeout" <<'PY'
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

kind = sys.argv[1]
timeout = float(sys.argv[2])
url = ("http://127.0.0.1:8000/healthz" if kind == "backend"
       else "http://127.0.0.1:5173/@vite/client")
try:
    response = urlopen(url, timeout=timeout)
except HTTPError as exc:
    print(f"HTTP ERROR: {url} returned status {exc.code}.")
    sys.exit(3)
except (URLError, TimeoutError, OSError) as exc:
    reason = getattr(exc, "reason", exc)
    print(f"CONNECTION FAILED: could not reach {url}: {reason}")
    sys.exit(2)

if response.status != 200:
    print(f"HTTP ERROR: {url} returned status {response.status}.")
    sys.exit(3)
try:
    body = response.read(16384)
except OSError as exc:
    print(f"CONNECTION FAILED while reading {url}: {exc}")
    sys.exit(2)

if kind == "backend":
    try:
        healthy = json.loads(body).get("status") == "ok"
    except (ValueError, AttributeError):
        healthy = False
    if not healthy:
        print(f"APPLICATION CHECK FAILED: {url} returned HTTP 200 without status=ok JSON.")
        sys.exit(4)
else:
    if b"vite" not in body.lower():
        print(f"APPLICATION CHECK FAILED: {url} returned HTTP 200 without Vite client content.")
        sys.exit(4)
print(f"PASS: {url} returned expected HTTP 200 response.")
PY
}

BACKEND_STATE="$(project_listener_state 8000 "$ROOT_DIR" Python)"
FRONTEND_STATE="$(project_listener_state 5173 "$FRONTEND_DIR" node)"
case "$BACKEND_STATE" in conflict:*) fail "Port 8000 is occupied by PID ${BACKEND_STATE#conflict:}, outside the verified backend working directory. It was left untouched." ;; esac
case "$FRONTEND_STATE" in conflict:*) fail "Port 5173 is occupied by PID ${FRONTEND_STATE#conflict:}, outside the verified frontend working directory. It was left untouched." ;; esac

if [[ "$BACKEND_STATE" == project:* ]]; then
    printf '\nBackend listener found (PID(s) %s); checking /healthz...\n' "${BACKEND_STATE#project:}"
    if ! probe_service backend 2; then
        /usr/sbin/lsof -nP -iTCP:8000 -sTCP:LISTEN 2>/dev/null || true
        fail "Project PID(s) ${BACKEND_STATE#project:} already own port 8000 but /healthz failed. No duplicate was started. Inspect the owning terminal; press Ctrl-C there only if you intend to restart, then rerun after port 8000 is free."
    fi
    BACKEND_HEALTHY=1
else
    BACKEND_HEALTHY=0
fi
if [[ "$FRONTEND_STATE" == project:* ]]; then
    printf 'Frontend listener found (PID(s) %s); checking Vite...\n' "${FRONTEND_STATE#project:}"
    if ! probe_service frontend 2; then
        /usr/sbin/lsof -nP -iTCP:5173 -sTCP:LISTEN 2>/dev/null || true
        fail "Project PID(s) ${FRONTEND_STATE#project:} already own port 5173 but the health check at 127.0.0.1 failed. No duplicate was started. Inspect the listener address and owning terminal; if restarting, press Ctrl-C there and rerun after port 5173 is free."
    fi
    FRONTEND_HEALTHY=1
else
    FRONTEND_HEALTHY=0
fi

HF_HUB_CACHE="$("$PYTHON" -c 'from huggingface_hub.constants import HF_HUB_CACHE; print(HF_HUB_CACHE)' 2>/dev/null)" \
    || fail "Could not determine the Hugging Face model cache location."

if [ "$BACKEND_HEALTHY" -eq 0 ]; then
    # Only start the backend when both models are already available locally.
    model_is_cached() {
        local repo_dir="$HF_HUB_CACHE/models--$1" revision snapshot
        [ -d "$repo_dir/snapshots" ] && [ -f "$repo_dir/refs/main" ] || return 1
        revision="$(cat "$repo_dir/refs/main")"
        snapshot="$repo_dir/snapshots/$revision"
        [ -d "$snapshot" ] || return 1
        [ -f "$snapshot/config.json" ] || return 1
        [ -f "$snapshot/vocab.json" ] || return 1
        [ -f "$snapshot/merges.txt" ] || return 1
        [ -f "$snapshot/model.safetensors" ] || [ -f "$snapshot/pytorch_model.bin" ]
    }
    missing_models=()
    model_is_cached "cardiffnlp--twitter-roberta-base-sentiment-latest" || missing_models+=("cardiffnlp/twitter-roberta-base-sentiment-latest")
    model_is_cached "cardiffnlp--twitter-roberta-base-irony" || missing_models+=("cardiffnlp/twitter-roberta-base-irony")
    if [ "${#missing_models[@]}" -gt 0 ]; then
        printf '\n[ERROR] Required CardiffNLP model cache is incomplete; no model download was started.\n' >&2
        printf 'Missing or incomplete cache entries:\n' >&2
        for model in "${missing_models[@]}"; do printf '  - %s\n' "$model" >&2; done
        printf 'Cache checked: %s\n' "$HF_HUB_CACHE" >&2
        fail "Backend startup was skipped; cache the models only after approving their download."
    fi
fi

quote_shell() {
    "$PYTHON" -c 'import shlex,sys; print(shlex.quote(sys.argv[1]))' "$1"
}

create_runner() {
    local label="$1"
    runner_dir="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/nastaghar-launch.XXXXXX")" || fail "Could not create a temporary Terminal runner for the $label."
    runner_file="$runner_dir/$label.sh"
    runner_ready="$runner_file.started"
}

write_runner_header() {
    printf '#!/bin/bash\n'
    printf 'trap '\''rm -f "$0" "$0.started"; rmdir "$(dirname "$0")" 2>/dev/null || true'\'' EXIT\n'
    printf 'touch %s\n' "$(quote_shell "$runner_ready")"
}

launch_terminal_runner() {
    local label="$1" file="$2" apple_event_status attempt
    chmod 700 "$file" || fail "Could not make the temporary $label runner executable."
    /usr/bin/osascript - "$file" <<'APPLESCRIPT'
on run argv
    set runnerPath to item 1 of argv
    tell application "Terminal"
        activate
        do script "/bin/bash " & quoted form of runnerPath
    end tell
end run
APPLESCRIPT
    apple_event_status=$?
    if [ "$apple_event_status" -ne 0 ]; then
        rm -f "$file"
        rmdir "$(dirname "$file")" 2>/dev/null || true
        fail "Terminal did not accept the $label command (osascript exit $apple_event_status). Review the AppleScript error above. If it says the operation is not authorized, allow the app running this launcher to control Terminal in System Settings > Privacy & Security > Automation."
    fi
    for attempt in {1..20}; do
        if [ -f "$file.started" ]; then
            rm -f "$file.started"
            printf 'Terminal confirmed it started the %s runner.\n' "$label"
            return 0
        fi
        sleep 0.25
    done
    fail "Terminal accepted the $label request, but the runner did not report execution within 5 seconds. Check the new Terminal window; temporary runner: $file"
}

ROOT_Q="$(quote_shell "$ROOT_DIR")"
FRONTEND_Q="$(quote_shell "$FRONTEND_DIR")"
PYTHON_Q="$(quote_shell "$PYTHON")"
NODE_BIN_Q="$(quote_shell "$NODE_BIN")"
HF_CACHE_Q="$(quote_shell "$HF_HUB_CACHE")"

if [ "$BACKEND_HEALTHY" -eq 0 ]; then
    printf '\n[2/4] Opening dedicated Terminal window for FastAPI backend...\n'
    create_runner backend
    {
        write_runner_header
        printf 'printf "\\033]0;Nasta Ghar API Backend\\007"\n'
        printf 'cd %s || exit 1\n' "$ROOT_Q"
        printf 'export PYTHONPATH=%s HF_HUB_CACHE=%s HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1\n' "$ROOT_Q" "$HF_CACHE_Q"
        printf 'printf "\\nNastaGhar backend on http://127.0.0.1:8000\\nCached CardiffNLP models only; downloads disabled.\\n\\n"\n'
        printf '%s -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload\n' "$PYTHON_Q"
        printf 'result=$?\nprintf "\\nBackend exited with status %%s. Press Ctrl-D to close this Terminal window.\\n" "$result"\n/bin/bash -i\n'
    } > "$runner_file"
    launch_terminal_runner backend "$runner_file"
else
    printf '\n[2/4] Reusing verified healthy FastAPI backend.\n'
fi

if [ "$FRONTEND_HEALTHY" -eq 0 ]; then
    printf '[3/4] Opening dedicated Terminal window for Vite frontend...\n'
    create_runner frontend
    {
        write_runner_header
        printf 'printf "\\033]0;Nasta Ghar React Frontend\\007"\n'
        printf 'cd %s || exit 1\n' "$FRONTEND_Q"
        printf 'export PATH=%s:"$PATH"\n' "$NODE_BIN_Q"
        printf 'printf "\\nNastaGhar frontend on http://127.0.0.1:5173\\n\\n"\n'
        printf 'npm run dev -- --host 127.0.0.1 --strictPort\n'
        printf 'result=$?\nprintf "\\nFrontend exited with status %%s. Press Ctrl-D to close this Terminal window.\\n" "$result"\n/bin/bash -i\n'
    } > "$runner_file"
    launch_terminal_runner frontend "$runner_file"
else
    printf '[3/4] Reusing verified healthy Vite frontend.\n'
fi

# Step 4: Health Diagnostics & Browser Launch (runs directly in this diagnostics window)
printf '\n[4/4] Verifying service health and opening web app in browser...\n'

wait_for_service() {
    local kind="$1" label="$2" max_attempts="${3:-15}" attempt output
    printf '\nChecking %s...\n' "$label"
    for ((attempt=1; attempt<=max_attempts; attempt++)); do
        if output="$(probe_service "$kind" 2 2>&1)"; then
            printf '%s\n' "$output"
            return 0
        else
            printf '  Attempt %s/%s: %s\n' "$attempt" "$max_attempts" "$output"
        fi
        [ "$attempt" -eq "$max_attempts" ] || sleep 2
    done
    printf 'FAIL: %s did not pass its health check after %s attempts.\n' "$label" "$max_attempts"
    return 1
}

backend_ok=0
frontend_ok=0
wait_for_service backend 'FastAPI backend (http://127.0.0.1:8000/healthz)' 15 && backend_ok=1
wait_for_service frontend 'Vite frontend (http://127.0.0.1:5173/@vite/client)' 15 && frontend_ok=1

printf '\nHealth-check summary\n--------------------\n'
printf 'Backend:  %s\n' "$([ "$backend_ok" -eq 1 ] && printf PASS || printf FAIL)"
printf 'Frontend: %s\n' "$([ "$frontend_ok" -eq 1 ] && printf PASS || printf FAIL)"

if [ "$backend_ok" -eq 1 ] && [ "$frontend_ok" -eq 1 ]; then
    review_url='http://127.0.0.1:5173/review'
    printf '\nBoth services passed. Opening %s in Google Chrome...\n' "$review_url"
    if /usr/bin/open -a "Google Chrome" "$review_url"; then
        printf 'Opened Google Chrome successfully.\n'
    else
        printf 'Google Chrome could not be opened by name; trying the default browser...\n'
        if /usr/bin/open "$review_url"; then
            printf 'Opened the review page in the default browser.\n'
        else
            printf 'ERROR: Google Chrome and the default browser could not be opened. Visit %s manually.\n' "$review_url"
        fi
    fi

    LOCAL_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
    printf '\n======================================================\n'
    printf ' ALL SERVERS RUNNING SUCCESSFULLY!\n\n'
    printf ' Customer Review Experience:\n'
    printf ' Local:   http://127.0.0.1:5173/review\n'
    if [ -n "$LOCAL_IP" ]; then
        printf ' Mobile:  http://%s:5173/review (QR scan)\n' "$LOCAL_IP"
    else
        printf ' Mobile:  http://<your-wifi-ip>:5173/review (QR scan)\n'
    fi
    printf '\n Languages: English, Hindi (Hinglish), Gujarati (Gujlish)\n\n'
    printf ' Owner Dashboard:\n'
    printf ' Local:   http://127.0.0.1:5173/owner\n'
    if [ -n "$LOCAL_IP" ]; then
        printf ' Mobile:  http://%s:5173/owner\n' "$LOCAL_IP"
    fi
    printf '\n API Docs & Health:\n'
    printf ' http://127.0.0.1:8000/docs\n'
    printf ' http://127.0.0.1:8000/healthz\n'
    printf '======================================================\n\n'
    printf 'Diagnostics completed successfully. Keep the backend and frontend Terminal windows open.\n'
    printf 'Press Return to close this diagnostics window... '
    read -r _ || true
else
    printf '\n[ERROR] Browser was not opened because both health checks did not pass.\n'
    printf 'Inspect the backend and frontend Terminal windows for startup errors.\n'
    printf 'Press Return to close this diagnostics window... '
    read -r _ || true
    exit 1
fi
