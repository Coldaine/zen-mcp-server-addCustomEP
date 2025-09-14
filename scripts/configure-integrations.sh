#!/usr/bin/env bash
set -euo pipefail

# Optional integration script: safely and idempotently register Zen MCP
# with supported developer tools / CLIs.
# This script NEVER prompts. It only adds or updates entries if missing/stale.
# Tools handled (if detected):
# - Codex CLI (config: ~/.codex/config.toml)
# - Gemini CLI (config: ~/.gemini/settings.json)
# - Claude CLI (via `claude mcp add`)
# - Claude Desktop (claude_desktop_config.json)
#
# Usage examples:
#   ./scripts/configure-integrations.sh            # do all
#   ONLY=codex,gemini ./scripts/configure-integrations.sh
#   DRY_RUN=1 ./scripts/configure-integrations.sh  # show actions only
#
# Environment variables:
#   ONLY        Comma separated subset: codex,gemini,claude-cli,claude-desktop
#   DRY_RUN     If set to 1, no writes performed.
#   PYTHON_CMD  Override python command used for registration (default: python3 or python)

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

echo_info(){ echo -e "${YELLOW}$*${NC}" >&2; }
echo_ok(){ echo -e "${GREEN}✓${NC} $*" >&2; }
echo_warn(){ echo -e "${YELLOW}!${NC} $*" >&2; }
echo_err(){ echo -e "${RED}✗${NC} $*" >&2; }

PYTHON_CMD=${PYTHON_CMD:-}
if [[ -z "${PYTHON_CMD}" ]]; then
  for c in python3 python; do
    if command -v "$c" &>/dev/null; then PYTHON_CMD=$c; break; fi
  done
fi
[[ -z "${PYTHON_CMD}" ]] && { echo_err "No python interpreter found"; exit 1; }
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVER_PATH="$SCRIPT_DIR/server.py"

want(){ local n=$1; [[ -z "${ONLY:-}" ]] && return 0; IFS=, read -ra parts <<<"$ONLY"; for p in "${parts[@]}"; do [[ "$p" == "$n" ]] && return 0; done; return 1; }

maybe_write(){ if [[ "${DRY_RUN:-0}" == "1" ]]; then echo_info "DRY_RUN: would write $1"; return 0; fi; eval "$2"; }

register_codex(){
  want codex || return 0
  if ! command -v codex &>/dev/null; then echo_warn "Codex CLI not found"; return 0; fi
  local cfg="$HOME/.codex/config.toml"
  if [[ -f "$cfg" ]] && grep -q '\[mcp_servers\.zen\]' "$cfg"; then
    echo_ok "Codex already configured"; return 0; fi
  echo_info "Registering zen in Codex CLI config"
  local tmp=$(mktemp)
  [[ -f "$cfg" ]] && cat "$cfg" > "$tmp"
  {
    echo ""; echo "[mcp_servers.zen]"; echo "command = \"bash\"";
    echo "args = [\"-c\", \"for p in $(which uvx 2>/dev/null) $HOME/.local/bin/uvx /opt/homebrew/bin/uvx /usr/local/bin/uvx uvx; do [ -x \\\"$p\\\" ] && exec \\\"$p\\\" --from git+https://github.com/BeehiveInnovations/zen-mcp-server.git zen-mcp-server; done; echo 'uvx not found' >&2; exit 1\"]";
    echo ""; echo "[mcp_servers.zen.env]";
    echo "PATH = \"/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:$HOME/.local/bin:$HOME/.cargo/bin:$HOME/bin\"";
  } >> "$tmp"
  maybe_write "codex" "mv '$tmp' '$cfg'" && echo_ok "Codex configured: $cfg"
}

register_gemini(){
  want gemini || return 0
  local cfg="$HOME/.gemini/settings.json"
  [[ -f "$cfg" ]] || { echo_warn "Gemini settings not found (skipping)"; return 0; }
  if grep -q '"zen"' "$cfg" 2>/dev/null; then echo_ok "Gemini already configured"; return 0; fi
  echo_info "Registering zen in Gemini CLI settings"
  local wrapper="$SCRIPT_DIR/zen-mcp-server"
  if [[ ! -f "$wrapper" ]]; then
    cat > "$wrapper" <<'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
exec .zen_venv/bin/python server.py "$@"
EOF
    chmod +x "$wrapper"
  fi
  local tmp=$(mktemp)
  python3 - <<PY || { echo_err "Gemini config update failed"; return 0; }
import json,sys,os
cfg_path=os.path.expanduser("$cfg")
with open(cfg_path,'r') as f: data=json.load(f)
ms=data.setdefault('mcpServers',{})
ms['zen']={'command': '$wrapper'}
with open('$tmp','w') as f: json.dump(data,f,indent=2)
PY
  maybe_write "gemini" "mv '$tmp' '$cfg'" && echo_ok "Gemini configured: $cfg"
}

register_claude_cli(){
  want claude-cli || return 0
  if ! command -v claude &>/dev/null; then echo_warn "Claude CLI not found"; return 0; fi
  local list
  if ! list=$(claude mcp list 2>/dev/null); then echo_warn "Unable to list Claude MCP servers"; return 0; fi
  local env_args=""; while IFS= read -r line; do [[ -z "$line" || "$line" != *"="* ]] && continue; k=${line%%=*}; v=${line#*=}; env_args+=" -e $k=\"$v\""; done < <(grep -E '^(GEMINI|OPENAI|OPENROUTER|CUSTOM|DEFAULT_MODEL|LOG_LEVEL|DISABLED_TOOLS)_' "$SCRIPT_DIR/.env" 2>/dev/null || true)
  if echo "$list" | grep -q '^zen '; then
    # Try to detect mismatch path
    if ! echo "$list" | grep -F "$SERVER_PATH" >/dev/null; then
      echo_info "Updating Claude CLI zen path"
      maybe_write "claude-cli-update" "claude mcp remove zen -s user >/dev/null 2>&1 || true; claude mcp add zen -s user$env_args -- '$PYTHON_CMD' '$SERVER_PATH' >/dev/null 2>&1" && echo_ok "Claude CLI updated"
    else
      echo_ok "Claude CLI already configured"
    fi
  else
    echo_info "Adding zen to Claude CLI"
    maybe_write "claude-cli-add" "claude mcp add zen -s user$env_args -- '$PYTHON_CMD' '$SERVER_PATH' >/dev/null 2>&1" && echo_ok "Claude CLI configured"
  fi
}

register_claude_desktop(){
  want claude-desktop || return 0
  local path=""
  case "$(uname -s | tr '[:upper:]' '[:lower:]')" in
    darwin*) path="$HOME/Library/Application Support/Claude/claude_desktop_config.json" ;;
    linux*) path="$HOME/.config/Claude/claude_desktop_config.json" ;;
    *) echo_warn "Unsupported platform for Claude Desktop"; return 0;;
  esac
  [[ -f "$path" ]] || { echo_warn "Claude Desktop config not found (skipping)"; return 0; }
  local tmp=$(mktemp)
  python3 - <<PY || { echo_err "Claude Desktop update failed"; return 0; }
import json,os,sys
p=os.path.expanduser('$path')
try:
  with open(p,'r') as f: data=json.load(f)
except: data={}
ms=data.setdefault('mcpServers',{})
zen=ms.get('zen') or {}
zen['command']='$PYTHON_CMD'
zen['args']=['$SERVER_PATH']
ms['zen']=zen
with open('$tmp','w') as f: json.dump(data,f,indent=2)
PY
  maybe_write "claude-desktop" "mv '$tmp' '$path'" && echo_ok "Claude Desktop configured"
}

main(){
  echo_info "Zen MCP Integration Configuration"
  echo_info "Server: $SERVER_PATH"
  [[ "${DRY_RUN:-0}" == "1" ]] && echo_info "(dry-run mode)"
  register_codex
  register_gemini
  register_claude_cli
  register_claude_desktop
  echo_ok "Done"
}

main "$@"
