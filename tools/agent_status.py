#!/usr/bin/env python3
"""Generate a one-file HTML status board for the eval harnesses.

Reads LIVE state (no hand-typed data, so it can't drift):
  - rich image introspection (skills + their SKILL.md, persona/identity + config
    file CONTENTS, MCP servers, plugins) via a single `docker run`,
  - memory-service health via HTTP pings to <memory-host>.

Self-contained (works opened directly from disk): every persona/identity/config
file AND every skill's SKILL.md is embedded, and clicking a chip opens a modal
viewer. Skills + plugins get a "View on GitHub" link to the source repo path
when the source location is known.

Usage:
    python3 tools/agent_status.py            # writes agent-status.html
    python3 tools/agent_status.py --open     # also opens it in the default browser
"""

import argparse
import json
import os
import subprocess
import urllib.request
import webbrowser
from datetime import datetime
from html import escape
from pathlib import Path

IMAGE = "harbor-agents-rich:latest"
OUT = Path(__file__).resolve().parent.parent / "agent-status.html"

HARNESS_REPO = {
    "openclaw": "https://github.com/openclaw/openclaw",
    "hermes": "https://github.com/NousResearch/hermes-agent",
}

MEMORY = [
    # recall-eval (port 8408, coding-eval entity ontology) is what the
    # eval harnesses (openclaw + hermes) point at; the dashboard tracks
    # eval-side health. recall-prod on :8407 (agent-memory ontology) serves
    # the unrelated <prod-group>/<prod-group>/<prod-group> production groups.
    # Internal endpoints from env (gitignored configs/local.env) — no topology in this public repo.
    ("recall", f"{os.environ.get('RECALL_URL', '')}/health", "Graphiti temporal KG (eval, 23 tools, coding ontology)"),
    ("hindsight", f"{os.environ.get('HINDSIGHT_URL', '')}/health", "learning memory (57 tools)"),
    ("honcho", f"{os.environ.get('HONCHO_URL', '')}/health", "ambient user model"),
    ("mem-embed", None, "bge-m3 shared embedder, 1024-dim (bridge-internal; serves all three)"),
]

AGENT_MEMORY = {
    "openclaw": [("recall", "eval-openclaw"), ("hindsight", "eval-openclaw")],
    "hermes": [
        ("recall", "eval-hermes"),
        ("hindsight", "eval-hermes"),
        ("honcho", "eval-hermes"),
    ],
}

# Container introspection — emits one JSON blob on stdout.
_INTROSPECT = r"""
. ~/.nvm/nvm.sh && nvm use 22 >/dev/null 2>&1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
python3 - <<'PY'
import json, subprocess, re, os
out = {}
files = []  # {agent, group, name, path, content, github?}
MAX = 80000

def addfile(agent, group, path, github=None, name=None, active=None, content=None):
    name = name or os.path.basename(path)
    if content is None:
        try:
            content = open(path, encoding='utf-8', errors='replace').read()
            if len(content) > MAX:
                content = content[:MAX] + f"\n\n... [truncated at {MAX} chars]"
        except Exception as e:
            content = f"(could not read {path}: {e})"
    entry = {"agent": agent, "group": group, "name": name, "path": path, "content": content}
    if github: entry["github"] = github
    if active is not None: entry["active"] = bool(active)
    files.append(entry)

def parse_rich_table(text):
    # Parse a rich-library Table (header ┃, body │) into a list of dicts.
    lines = text.splitlines()
    hdr = -1
    for i, l in enumerate(lines):
        if l.lstrip().startswith('┃'):  # ┃ (header rows)
            hdr = i; break
    if hdr < 0: return []
    headers = [c.strip() for c in lines[hdr].split('┃')[1:-1]]
    rows, current, started = [], [''] * len(headers), False
    for l in lines[hdr+1:]:
        s = l.lstrip()
        if s.startswith('│') or s.startswith('┃'):  # │ or ┃
            parts = [c.strip() for c in s.split(s[0])[1:-1]]
            if len(parts) != len(headers): continue
            if parts[0]:
                if started: rows.append(dict(zip(headers, current)))
                current = list(parts); started = True
            else:
                for i, p in enumerate(parts):
                    if p: current[i] = (current[i] + ' ' + p).strip()
        elif any(c in l for c in '┗┘└'):  # ┗ ┘ └
            break
    if started: rows.append(dict(zip(headers, current)))
    return rows

# ---------- openclaw config + MCP ----------
try:
    cfg = json.load(open('/root/.openclaw/openclaw.json'))
    prov = (cfg.get('models', {}).get('providers', {}) or {})
    xr = prov.get('xrouter', {})
    models = xr.get('models', [{}])
    out['oc_model'] = models[0].get('id', '?') if models else '?'
    out['oc_reasoning'] = bool(models[0].get('reasoning')) if models else False
    out['oc_thinking'] = cfg.get('agents', {}).get('defaults', {}).get('thinkingDefault', '?')
    mcp_srv = (cfg.get('mcp', {}).get('servers', {}) or {})
    out['oc_mcp'] = [{"name": n, "url": v.get('url',''), "transport": v.get('transport','streamable-http'),
                      "headers": v.get('headers', {})} for n,v in sorted(mcp_srv.items())]
except Exception as e:
    out['oc_config_err'] = str(e)

# ---------- openclaw active skills + SKILL.md ----------
try:
    PKG = subprocess.check_output(
        ['bash','-lc','. ~/.nvm/nvm.sh && nvm use 22 >/dev/null 2>&1 && dirname $(dirname $(readlink -f $(which openclaw)))'],
        text=True).strip() + '/openclaw'
    r = subprocess.run(['openclaw','skills','check'], capture_output=True, text=True, timeout=90)
    txt = r.stdout
    m = re.search(r'Eligible:\s*(\d+)', txt); out['oc_skills_active'] = int(m.group(1)) if m else None
    m = re.search(r'Total:\s*(\d+)', txt); out['oc_skills_total'] = int(m.group(1)) if m else None

    # Parse ALL classification sections (active = "Ready and visible to model";
    # available-but-not-active = "Missing requirements" / "Disabled" / "Blocked").
    section, classified = None, {}  # name -> active bool
    SECTIONS = {
        'Ready and visible to model:': True,
        'Missing requirements:': False,
        'Disabled:': False,
        'Blocked by allowlist:': False,
        'Excluded by agent allowlist:': False,
    }
    for line in txt.splitlines():
        s = line.rstrip()
        for hdr, active in SECTIONS.items():
            if s.strip() == hdr.rstrip(':') + ':' or s.strip() == hdr:
                section = active; break
        else:
            if section is None: continue
            t = s.strip()
            if not t: continue
            # bullet/emoji prefix; name is the first word (skills are slug-named)
            m2 = re.match(r'^[^\w]*(\S+)', t)
            if not m2: continue
            name = m2.group(1)
            # stop if we hit a new header-looking line
            if name.endswith(':'): section = None; continue
            if name not in classified:
                classified[name] = section
    out['oc_skills'] = sorted(n for n,a in classified.items() if a)
    out['oc_skills_all'] = classified

    # For every skill (active + available), locate SKILL.md and embed.
    ext_dir = f'{PKG}/dist/extensions'
    exts = sorted(os.listdir(ext_dir)) if os.path.isdir(ext_dir) else []
    for name, active in classified.items():
        candidates = [
            (f'{PKG}/skills/{name}/SKILL.md',
             f'https://github.com/openclaw/openclaw/blob/main/skills/{name}/SKILL.md'),
        ]
        for ext in exts:
            candidates.append((
                f'{ext_dir}/{ext}/skills/{name}/SKILL.md',
                f'https://github.com/openclaw/openclaw/blob/main/extensions/{ext}/skills/{name}/SKILL.md',
            ))
        placed = False
        for path, gh in candidates:
            if os.path.exists(path):
                addfile('openclaw','skill', path, github=gh, name=name, active=active)
                placed = True; break
        if not placed:
            addfile('openclaw','skill',
                    f'(SKILL.md not located for {name})', name=name, active=active,
                    content=f'(SKILL.md source not found in image for skill "{name}")')
except Exception as e:
    out['oc_skills_err'] = str(e)

# ---------- openclaw plugins (via `openclaw plugins list --json`) ----------
oc_plugins = []
try:
    r = subprocess.run(['openclaw','plugins','list','--json'],
                       capture_output=True, text=True, timeout=60)
    pj = json.loads(r.stdout) if r.returncode == 0 else {}
    for p in (pj.get('plugins') or []):
        oc_plugins.append({
            "id": p.get('id'), "name": p.get('name'),
            "version": p.get('version'), "enabled": bool(p.get('enabled')),
            "status": p.get('status'), "origin": p.get('origin'),
        })
        root = p.get('rootDir')
        if root and os.path.isdir(root):
            for cand in ('openclaw.plugin.json','package.json','index.js'):
                fp = os.path.join(root, cand)
                if os.path.exists(fp):
                    base = os.path.basename(root)
                    gh = (f'https://github.com/openclaw/openclaw/tree/main/extensions/{base}'
                          if p.get('origin') == 'bundled' else None)
                    addfile('openclaw','plugin', fp,
                            name=p.get('id') or base, github=gh,
                            active=bool(p.get('enabled')))
                    break
except Exception as e:
    out['oc_plugins_err'] = str(e)
out['oc_plugins'] = oc_plugins

# ---------- openclaw persona/identity files (full contents) + config ----------
ws = '/opt/harness/openclaw-workspace'
try:
    for f in sorted(os.listdir(ws)):
        if f.endswith('.md'):
            addfile('openclaw', 'persona', os.path.join(ws, f))
    ident = os.path.join(ws, 'IDENTITY.md')
    if os.path.exists(ident):
        soul = open(ident).read()
        first = next((re.sub(r'^[\s\-\*#]+', '', l).replace('**','').strip()
                      for l in soul.splitlines() if l.strip() and not l.startswith('#')), '')
        out['oc_identity'] = first[:120]
except Exception as e:
    out['oc_persona_err'] = str(e)
addfile('openclaw', 'config', '/root/.openclaw/openclaw.json')

# ---------- hermes config + MCP ----------
try:
    import yaml
    hc = yaml.safe_load(open('/root/.hermes/config.yaml'))
    out['hm_model'] = (hc.get('model', {}) or {}).get('default', '?')
    out['hm_provider'] = (hc.get('model', {}) or {}).get('provider', '?')
    out['hm_reasoning'] = (hc.get('agent', {}) or {}).get('reasoning_effort', '?')
    out['hm_mem_provider'] = (hc.get('memory', {}) or {}).get('provider', 'built-in only')
    mcp_srv = (hc.get('mcp_servers', {}) or {})
    out['hm_mcp'] = [{"name": n, "url": v.get('url',''), "transport": v.get('transport','streamable-http'),
                      "headers": v.get('headers', {})} for n,v in sorted(mcp_srv.items())]
except Exception as e:
    out['hm_config_err'] = str(e)

# ---------- hermes skills via `hermes skills list` ----------
try:
    HM_ROOT = '/usr/local/lib/hermes-agent'
    r = subprocess.run(['hermes','skills','list'], capture_output=True, text=True, timeout=60,
                       env={**os.environ, 'HERMES_HOME':'/root/.hermes', 'PATH':os.environ.get('PATH','')})
    rows = parse_rich_table(r.stdout)
    hm_skills = []  # {name, category, source, status, active}
    for row in rows:
        nm = row.get('Name','').strip().rstrip('…')
        if not nm: continue
        st = row.get('Status','').strip().lower()
        hm_skills.append({
            "name": nm,
            "category": row.get('Category','').strip(),
            "source": row.get('Source','').strip(),
            "status": st,
            "active": st == 'enabled',
        })
    out['hm_skills_count'] = len(hm_skills)
    out['hm_skills_active'] = sum(1 for s in hm_skills if s['active'])
    out['hm_skills'] = [s['name'] for s in hm_skills]

    for s in hm_skills:
        name, cat = s['name'], s['category']
        # Try the package source under skills/ then optional-skills/, with optional category sub-dir.
        candidates = []
        for base, repo_sub in [('skills','skills'), ('optional-skills','optional-skills')]:
            paths = [f'{HM_ROOT}/{base}/{name}', f'{HM_ROOT}/{base}/{cat}/{name}'] if cat else [f'{HM_ROOT}/{base}/{name}']
            for dpath in paths:
                if not os.path.isdir(dpath): continue
                for cand in ('SKILL.md','README.md'):
                    fp = f'{dpath}/{cand}'
                    if os.path.exists(fp):
                        rel = f'{repo_sub}/{cat+"/" if cat else ""}{name}/{cand}'
                        candidates.append((fp, f'https://github.com/NousResearch/hermes-agent/blob/main/{rel}'))
                        break
        # Fallback to seeded home (no github mapping).
        seeded = [f'/root/.hermes/skills/{name}', f'/root/.hermes/skills/{cat}/{name}'] if cat else [f'/root/.hermes/skills/{name}']
        for dpath in seeded:
            if not os.path.isdir(dpath): continue
            for cand in ('SKILL.md','README.md'):
                fp = f'{dpath}/{cand}'
                if os.path.exists(fp):
                    candidates.append((fp, None))
                    break
        if candidates:
            fp, gh = candidates[0]
            addfile('hermes','skill', fp, name=name, github=gh, active=s['active'])
        else:
            addfile('hermes','skill', f'(no SKILL.md found for {name})',
                    name=name, active=s['active'],
                    content=f'(no SKILL.md / README.md found in image for skill "{name}")')
except Exception as e:
    out['hm_skills_err'] = str(e)

# ---------- hermes plugins: dual-system activation ----------
# hermes has TWO independent plugin activation tracks:
#   1. `plugins.enabled` allow-list (what `hermes plugins list` reads;
#      defaults to None = nothing enabled — gates user-installed plugins).
#   2. Direct config-driven import (`memory.provider`, `agent.context.engine`,
#      etc. — `agent_init.py` imports the matching plugin module directly,
#      completely bypassing System 1).
# `hermes plugins list` is BLIND to System 2. We compute the union from both
# and enumerate bundled plugins from the filesystem (the CLI list omits whole
# categories like memory/ and context_engine/).
hm_plugins = []
try:
    HM_PLUG = '/usr/local/lib/hermes-agent/plugins'

    # System 2: <category> -> (config-getter -> active plugin name).
    # Add a new (category, getter) here as new bypass paths are discovered in
    # the hermes source.
    cat_getters = {
        'memory': lambda c: (c.get('memory') or {}).get('provider'),
        # default "compressor" — see agent_init.py around the engine load.
        'context_engine': lambda c: (((c.get('agent') or {}).get('context') or {}).get('engine')) or 'compressor',
    }
    cfg_active = {}  # category -> {active plugin name}
    if 'hc' in dir() and hc:
        for cat, fn in cat_getters.items():
            try:
                v = fn(hc)
                if v: cfg_active.setdefault(cat, set()).add(v)
            except Exception:
                pass

    # System 1: explicit allow-list in config.yaml.
    enabled_allow = set()
    pl_cfg = (hc.get('plugins') or {}) if ('hc' in dir() and hc) else {}
    if isinstance(pl_cfg.get('enabled'), list):
        enabled_allow.update(pl_cfg['enabled'])
    # System 1 status from the CLI (reflects allow-list + any user installs).
    cli_status = {}
    try:
        r = subprocess.run(['hermes','plugins','list'], capture_output=True, text=True, timeout=60,
                           env={**os.environ, 'HERMES_HOME':'/root/.hermes', 'PATH':os.environ.get('PATH','')})
        for row in parse_rich_table(r.stdout):
            nm = (row.get('Name') or '').strip()
            st = (row.get('Status') or '').strip().lower()
            if nm: cli_status[nm] = st
    except Exception:
        pass

    # Enumerate ALL bundled plugins from disk (System 1 + System 2 combined).
    bundled = []  # (category, name, dir)
    if os.path.isdir(HM_PLUG):
        for entry in sorted(os.listdir(HM_PLUG)):
            cat_path = os.path.join(HM_PLUG, entry)
            if not os.path.isdir(cat_path):
                continue
            if os.path.exists(os.path.join(cat_path, 'plugin.yaml')):
                bundled.append(("", entry, cat_path))
                continue
            for sub in sorted(os.listdir(cat_path)):
                sub_path = os.path.join(cat_path, sub)
                if os.path.isdir(sub_path) and os.path.exists(os.path.join(sub_path, 'plugin.yaml')):
                    bundled.append((entry, sub, sub_path))

    for cat, name, dpath in bundled:
        full = f"{cat}/{name}" if cat else name
        s1 = (cli_status.get(full) == 'enabled') or (full in enabled_allow) or (name in enabled_allow)
        s2 = (cat in cfg_active and name in cfg_active[cat])
        active = bool(s1 or s2)
        via = None
        if s2 and cat == 'memory': via = 'config: memory.provider'
        elif s2 and cat == 'context_engine': via = 'config: agent.context.engine'
        elif s1: via = 'plugins.enabled allow-list'
        cli_st = cli_status.get(full)
        # Prepend a small banner to the embedded plugin.yaml so the user sees
        # the activation reason inline when they open the modal.
        banner_lines = [
            f'# Activation: {"ACTIVE" if active else "available (bundled, not loaded)"}',
            f'# Via: {via or "(not selected by config; not in plugins.enabled allow-list)"}',
            f'# `hermes plugins list` status: {cli_st or "(not tracked by System 1)"}',
            '# ' + '-' * 60, '',
        ]
        try:
            yaml_text = open(os.path.join(dpath, 'plugin.yaml'), encoding='utf-8', errors='replace').read()
        except Exception as e:
            yaml_text = f"(could not read plugin.yaml: {e})"
        addfile('hermes', 'plugin', os.path.join(dpath, 'plugin.yaml'),
                name=full, active=active,
                github=f'https://github.com/NousResearch/hermes-agent/tree/main/plugins/{full}',
                content='\n'.join(banner_lines) + yaml_text)
        hm_plugins.append({"name": full, "active": active, "via": via,
                           "cli_status": cli_st})
except Exception as e:
    out['hm_plugins_err'] = str(e)
out['hm_plugins'] = hm_plugins

# ---------- hermes persona/identity files + config ----------
try:
    soul = open('/root/.hermes/SOUL.md').read()
    first = next((re.sub(r'^[\s\-\*#]+', '', l).replace('**','').strip()
                  for l in soul.splitlines() if l.strip() and not l.startswith('#')), '')
    out['hm_soul'] = first[:120]
except Exception:
    out['hm_soul'] = ''
addfile('hermes', 'persona', '/root/.hermes/SOUL.md')
addfile('hermes', 'config', '/root/.hermes/config.yaml')
addfile('hermes', 'config', '/root/.hermes/honcho.json')

out['files'] = files
print("JSON_START" + json.dumps(out) + "JSON_END")
PY
"""


def introspect_image() -> dict:
    try:
        r = subprocess.run(
            ["docker", "run", "--rm", IMAGE, "bash", "-lc", _INTROSPECT],
            capture_output=True, text=True, timeout=180,
        )
        out = r.stdout
        s, e = out.find("JSON_START"), out.find("JSON_END")
        if s >= 0 and e > s:
            return json.loads(out[s + len("JSON_START"):e])
        return {"_image_err": (r.stderr or out)[-400:]}
    except Exception as exc:
        return {"_image_err": str(exc)}


def ping(url):
    if not url:
        return None
    try:
        with urllib.request.urlopen(url, timeout=6) as resp:
            return 200 <= resp.status < 500
    except Exception:
        return False


def dot(state) -> str:
    cls = {True: "up", False: "down", None: "na"}[state]
    return f'<span class="dot {cls}"></span>'


def chips_for(files, agent, group, kind):
    """Render clickable chips for files matching agent+group. kind = CSS class flavor."""
    sel = [f for f in files if f["agent"] == agent and f["group"] == group]
    if not sel:
        return '<span class="muted">none</span>'
    # active first, then by name (None treated as active for persona/config)
    sel.sort(key=lambda f: (0 if f.get('active') is not False else 1, f['name']))
    out = []
    for f in sel:
        a = f.get('active')
        mod = ' active' if a is True else (' inactive' if a is False else '')
        out.append(
            f'<span class="chip {kind}{mod}" onclick="showFile({f["_idx"]})" title="{escape(f["path"])}">{escape(f["name"])}</span>'
        )
    return "".join(out)


def count_active(files, agent, group):
    sel = [f for f in files if f["agent"] == agent and f["group"] == group]
    return sum(1 for f in sel if f.get('active') is True), len(sel)


def mcp_rows(servers):
    if not servers:
        return '<div class="muted">none</div>'
    rows = []
    for s in servers:
        headers = s.get("headers") or {}
        hdr_bits = " · ".join(f"{escape(k)}: {escape(str(v))}" for k, v in headers.items())
        rows.append(
            f'<div class="mcprow"><b>{escape(s["name"])}</b> '
            f'<span class="muted">{escape(s["transport"])}</span><br>'
            f'<span class="mono">{escape(s["url"])}</span>'
            + (f'<br><span class="muted">{hdr_bits}</span>' if hdr_bits else "")
            + '</div>'
        )
    return "".join(rows)


def render(data: dict, health: dict) -> str:
    img_ok = "_image_err" not in data
    img_badge = "Ready" if img_ok else "image missing"
    files = data.get("files", []) or []
    for i, f in enumerate(files):
        f["_idx"] = i
    files_js = json.dumps({
        f["_idx"]: {"name": f["name"], "path": f["path"],
                    "content": f["content"], "github": f.get("github")} for f in files
    # Embedding JSON inside <script>: any literal "</script>" in the content
    # would close the tag early. JSON allows "\/" for "/", so "<\/" stays valid
    # JSON while HTML's tokenizer no longer matches a closing tag.
    }).replace("</", "<\\/")

    def mem_rows(agent):
        rows = []
        for backend, key in AGENT_MEMORY[agent]:
            rows.append(
                f'<div class="memrow">{dot(health.get(backend))}<b>{backend}</b>'
                f'<span class="muted">→ {key}</span></div>'
            )
        return "".join(rows)

    oc_reason = f'on · {data.get("oc_thinking","?")}' if data.get("oc_reasoning") else "OFF"
    hm_reason_ok = str(data.get("hm_reasoning")) not in ("?", "off", "None")
    oc_repo = HARNESS_REPO["openclaw"]
    hm_repo = HARNESS_REPO["hermes"]
    oc_sk_a, oc_sk_t = count_active(files, 'openclaw', 'skill')
    oc_pl_a, oc_pl_t = count_active(files, 'openclaw', 'plugin')
    hm_sk_a, hm_sk_t = count_active(files, 'hermes', 'skill')
    hm_pl_a, hm_pl_t = count_active(files, 'hermes', 'plugin')

    cards = f"""
    <div class="card">
      <div class="chead"><span class="agent">openclaw</span>
        <a class="repo" href="{oc_repo}" target="_blank" rel="noopener">github ↗</a>
        <span class="badge {'ok' if img_ok else 'bad'}">{img_badge}</span></div>
      <table>
        <tr><th>Model</th><td>{escape(str(data.get('oc_model','?')))}</td></tr>
        <tr><th>Reasoning</th><td><span class="badge {'ok' if data.get('oc_reasoning') else 'bad'}">{oc_reason}</span></td></tr>
        <tr><th>Identity</th><td class="muted">{escape(data.get('oc_identity','—') or '—')}</td></tr>
      </table>
      <div class="sec">Persona / identity files <span class="muted">(click to view)</span></div>
      <div>{chips_for(files, 'openclaw', 'persona', 'file')}</div>
      <div class="sec">Config</div>
      <div>{chips_for(files, 'openclaw', 'config', 'file')}</div>
      <div class="sec">Skills <span class="counts"><span class="ok">{oc_sk_a} active</span> / {oc_sk_t} total</span> <span class="muted">(click to view SKILL.md)</span></div>
      <div>{chips_for(files, 'openclaw', 'skill', 'skill')}</div>
      <div class="sec">MCP servers</div>
      {mcp_rows(data.get('oc_mcp', []))}
      <div class="sec">Plugins <span class="counts"><span class="ok">{oc_pl_a} enabled</span> / {oc_pl_t} total</span> <span class="muted">(click to view manifest)</span></div>
      <div>{chips_for(files, 'openclaw', 'plugin', 'plugin')}</div>
      <div class="sec">Memory</div>
      {mem_rows('openclaw')}
      <div class="sec">Subagents</div>
      <div class="muted">native: sessions_spawn / sessions_yield</div>
    </div>

    <div class="card">
      <div class="chead"><span class="agent">hermes</span>
        <a class="repo" href="{hm_repo}" target="_blank" rel="noopener">github ↗</a>
        <span class="badge {'ok' if img_ok else 'bad'}">{img_badge}</span></div>
      <table>
        <tr><th>Model</th><td>{escape(str(data.get('hm_model','?')))} <span class="muted">via {escape(str(data.get('hm_provider','?')))}</span></td></tr>
        <tr><th>Reasoning</th><td><span class="badge {'ok' if hm_reason_ok else 'bad'}">effort: {escape(str(data.get('hm_reasoning','?')))}</span></td></tr>
        <tr><th>Identity</th><td class="muted">{escape(data.get('hm_soul','—') or '—')}</td></tr>
        <tr><th>Memory provider</th><td>{escape(str(data.get('hm_mem_provider','?')))}</td></tr>
      </table>
      <div class="sec">Persona / identity files <span class="muted">(click to view)</span></div>
      <div>{chips_for(files, 'hermes', 'persona', 'file')}</div>
      <div class="sec">Config</div>
      <div>{chips_for(files, 'hermes', 'config', 'file')}</div>
      <div class="sec">Skills <span class="counts"><span class="ok">{hm_sk_a} active</span> / {hm_sk_t} total</span> <span class="muted">(click to view SKILL.md)</span></div>
      <div>{chips_for(files, 'hermes', 'skill', 'skill')}</div>
      <div class="sec">MCP servers</div>
      {mcp_rows(data.get('hm_mcp', []))}
      <div class="sec">Plugins <span class="counts"><span class="ok">{hm_pl_a} active</span> / {hm_pl_t} bundled</span> <span class="muted">(click for activation reason + plugin.yaml)</span></div>
      <div class="muted" style="font-size:11px;margin-bottom:6px">active = matched via <code>memory.provider</code> / <code>agent.context.engine</code> / <code>plugins.enabled</code> allow-list. `hermes plugins list` alone only reports the allow-list track.</div>
      <div>{chips_for(files, 'hermes', 'plugin', 'plugin')}</div>
      <div class="sec">Memory</div>
      {mem_rows('hermes')}
      <div class="sec">Subagents</div>
      <div class="muted">native: delegate_task / kanban</div>
    </div>
    """

    mem_legend = "".join(
        f'<div class="memrow">{dot(health.get(label))}<b>{label}</b>'
        f'<span class="muted">{desc}</span></div>'
        for label, _url, desc in MEMORY
    )

    err = (
        f'<div class="err">image introspection failed: {escape(str(data["_image_err"]))}</div>'
        if not img_ok else ""
    )
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Agent status</title>
<style>
  body{{font:14px/1.5 system-ui,sans-serif;margin:0;background:#0f1117;color:#e6e6e6;padding:24px}}
  h1{{font-size:18px;margin:0 0 2px}} .ts{{color:#8a8f98;font-size:12px;margin-bottom:18px}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;max-width:1100px}}
  .card{{background:#171a22;border:1px solid #262b36;border-radius:10px;padding:16px}}
  .chead{{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap}}
  .agent{{font-size:16px;font-weight:700;margin-right:auto}}
  .repo{{font-size:12px;color:#9db4d6;text-decoration:none;border:1px solid #2f3645;border-radius:6px;padding:1px 8px}}
  .repo:hover{{background:#1c2331}}
  table{{width:100%;border-collapse:collapse;margin-bottom:6px}}
  th{{text-align:left;color:#8a8f98;font-weight:500;width:120px;vertical-align:top;padding:3px 0}}
  td{{padding:3px 0}}
  .sec{{color:#8a8f98;font-size:11px;text-transform:uppercase;letter-spacing:.5px;margin:12px 0 6px;border-top:1px solid #262b36;padding-top:8px}}
  .chip{{display:inline-block;background:#222734;border:1px solid #2f3645;border-radius:6px;padding:1px 7px;margin:2px;font-size:12px;cursor:pointer}}
  .chip.file{{background:#1c2331;color:#9db4d6}} .chip.file:hover{{background:#28344a;border-color:#3d4d6b}}
  .chip.skill{{color:#bfe3c5}} .chip.skill:hover{{filter:brightness(1.2)}}
  .chip.skill.active{{background:#1b2a1f;border-color:#3a5a44;color:#9fe0a5;font-weight:600}}
  .chip.skill.inactive{{background:#1a1c22;border-color:#262b36;color:#7a8190;opacity:.7}}
  .chip.plugin{{color:#e6c98a}} .chip.plugin:hover{{filter:brightness(1.2)}}
  .chip.plugin.active{{background:#2a2519;border-color:#5a4a2a;color:#f0d590;font-weight:600}}
  .chip.plugin.inactive{{background:#1a1c22;border-color:#262b36;color:#7a8190;opacity:.7}}
  .counts{{font-size:11px;color:#8a8f98;margin-left:6px}}
  .counts .ok{{color:#5fd07e}}
  .muted{{color:#8a8f98}} .mono{{font:12px ui-monospace,Menlo,monospace}}
  .badge{{padding:1px 8px;border-radius:6px;font-size:12px;font-weight:600}}
  .badge.ok{{background:#163a22;color:#5fd07e}} .badge.bad{{background:#3a1616;color:#ef7a7a}}
  .dot{{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px;vertical-align:middle}}
  .dot.up{{background:#41c463}} .dot.down{{background:#ef5350}} .dot.na{{background:#6b7280}}
  .memrow{{padding:2px 0}} .memrow b{{margin-right:6px}}
  .mcprow{{padding:4px 0;border-bottom:1px dashed #262b36}} .mcprow:last-child{{border:0}}
  .legend{{max-width:1100px;margin-top:18px;background:#171a22;border:1px solid #262b36;border-radius:10px;padding:14px}}
  .err{{background:#3a1616;color:#ef7a7a;padding:8px;border-radius:6px;margin-bottom:12px;max-width:1100px;white-space:pre-wrap}}
  .nav{{display:flex;gap:10px;align-items:center;margin-bottom:14px}}
  .nav a{{font-size:13px;text-decoration:none;border:1px solid #2f3645;border-radius:6px;padding:4px 12px;color:#9db4d6}}
  .nav a:hover{{background:#1c2331}}
  .nav a.active{{background:#1b2a1f;border-color:#3a5a44;color:#9fe0a5;font-weight:600}}
  /* modal */
  #ov{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:50}}
  #mo{{display:none;position:fixed;top:5%;left:50%;transform:translateX(-50%);width:min(900px,92vw);max-height:88vh;
       background:#10131a;border:1px solid #2f3645;border-radius:10px;flex-direction:column;z-index:51}}
  #mo header{{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 16px;border-bottom:1px solid #262b36}}
  #mo h3{{margin:0;font:13px monospace}} #mo .x{{cursor:pointer;color:#8a8f98;font-size:20px;line-height:1}}
  #mo .gh{{font-size:12px;color:#9db4d6;text-decoration:none;border:1px solid #2f3645;border-radius:6px;padding:2px 10px}}
  #mo .gh:hover{{background:#1c2331}}
  #mo pre{{margin:0;padding:16px;overflow:auto;white-space:pre-wrap;word-break:break-word;font:12.5px/1.55 ui-monospace,Menlo,monospace;color:#cdd6e4}}
  #mo .path{{color:#6b7280;font:11px monospace;padding:0 16px 10px}}
</style></head><body>
<div class="nav">
  <a href="agent-status.html" class="active">Agent status</a>
  <a href="task-catalog.html">Task Suite</a>
  <a href="roadmap.html">Roadmap</a>
</div>
<h1>Eval harness status</h1>
<div class="ts">generated {ts} · source: {IMAGE} + live memory pings · re-run tools/agent_status.py to refresh</div>
{err}
<div class="grid">{cards}</div>
<div class="legend"><div class="sec" style="margin-top:0;border:0;padding:0">Memory services (<memory-host>)</div>{mem_legend}
<div class="muted" style="margin-top:8px">green = reachable · red = down · grey = n/a (internal). Per-agent keys isolate eval memory from prod (<prod-group>/<prod-group>).</div>
</div>

<div id="ov" onclick="hideFile()"></div>
<div id="mo">
  <header>
    <h3 id="mo-name"></h3>
    <div style="display:flex;gap:8px;align-items:center">
      <a id="mo-gh" class="gh" href="#" target="_blank" rel="noopener" style="display:none">View on GitHub ↗</a>
      <span class="x" onclick="hideFile()">&times;</span>
    </div>
  </header>
  <div class="path" id="mo-path"></div>
  <pre id="mo-body"></pre>
</div>
<script>
const FILES = {files_js};
function showFile(i){{
  const f = FILES[i]; if(!f) return;
  document.getElementById('mo-name').textContent = f.name;
  document.getElementById('mo-path').textContent = f.path;
  document.getElementById('mo-body').textContent = f.content;
  const gh = document.getElementById('mo-gh');
  if(f.github){{ gh.href = f.github; gh.style.display = 'inline-block'; }}
  else {{ gh.style.display = 'none'; }}
  document.getElementById('ov').style.display='block';
  document.getElementById('mo').style.display='flex';
}}
function hideFile(){{
  document.getElementById('ov').style.display='none';
  document.getElementById('mo').style.display='none';
}}
document.addEventListener('keydown', e=>{{ if(e.key==='Escape') hideFile(); }});
</script>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", action="store_true", help="open in browser after writing")
    args = ap.parse_args()

    print("introspecting", IMAGE, "...")
    data = introspect_image()
    print("pinging memory services ...")
    health = {label: ping(url) for label, url, _ in MEMORY}

    OUT.write_text(render(data, health))
    print("wrote", OUT)
    if args.open:
        webbrowser.open(f"file://{OUT}")


if __name__ == "__main__":
    main()
