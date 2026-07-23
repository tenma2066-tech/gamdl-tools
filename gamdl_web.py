#
# gamdl_web.py - Mobile-friendly web UI for gamdl
#
# Runs on a PC/server. Control it from an iPhone (or any device) browser
# on the same Wi-Fi network. The download itself runs on the machine that
# runs this script (gamdl needs Widevine DRM + ffmpeg, which cannot run on
# iOS), while the phone is just a remote control.
#
# Usage:
#   python gamdl_web.py                 # listen on 0.0.0.0:8765
#   python gamdl_web.py --port 9000
#   python gamdl_web.py --output D:\music
#
# Then on the iPhone, open:  http://<PC-LAN-IP>:8765
# (find the PC IP with `ipconfig` on Windows or `ip addr` on Linux/macOS)
#
import argparse
import html
import json
import os
import shlex
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

if getattr(sys, "frozen", False):
    _here = os.path.dirname(sys.executable)
else:
    _here = os.path.dirname(os.path.abspath(__file__))

DEFAULT_COOKIES = os.path.join(_here, "cookies.txt")
DEFAULT_OUTPUT = os.path.join(_here, "music")

CODEC_OPTIONS = [
    ("AAC 256kbps (no Wrapper)", "aac-legacy"),
    ("ALAC lossless (Wrapper required)", "alac"),
]


class Job:
    """A single download job, shared across HTTP connections."""

    def __init__(self):
        self._lock = threading.Lock()
        self._proc = None
        self.lines = []           # full log, index == line id
        self.running = False
        self.status = "Ready"

    # --- state snapshot -----------------------------------------------------
    def snapshot(self, since=0):
        with self._lock:
            new = self.lines[since:]
            return {
                "running": self.running,
                "status": self.status,
                "next": len(self.lines),
                "lines": new,
            }

    def _append(self, text):
        with self._lock:
            for piece in text.splitlines():
                self.lines.append(piece)

    # --- lifecycle ----------------------------------------------------------
    def start(self, urls, output, cookies, codec, title_only):
        with self._lock:
            if self.running:
                return False, "A download is already running."
            self.lines = []
            self.running = True
            self.status = "Downloading..."

        cmd = build_command(urls, output, cookies, codec, title_only)
        os.makedirs(output, exist_ok=True)
        self._append("[START] " + " ".join(shlex.quote(str(c)) for c in cmd) + "\n")

        threading.Thread(target=self._run, args=(cmd,), daemon=True).start()
        return True, "started"

    def _run(self, cmd):
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            self._proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", env=env,
            )
        except Exception as exc:  # noqa: BLE001 - surface any spawn failure to UI
            self._append(f"[ERROR] Failed to start gamdl: {exc}\n")
            with self._lock:
                self.running = False
                self.status = "Error"
            return

        for line in self._proc.stdout:
            # drop the noisy [download] percentage spam, keep everything else
            if line.startswith("[download]") and "%" in line:
                continue
            self._append(line)

        self._proc.wait()
        code = self._proc.returncode
        self._append(f"\n[DONE] exit code {code}\n")
        with self._lock:
            self.running = False
            self.status = "Done" if code == 0 else f"Error (exit {code})"
        self._proc = None

    def stop(self):
        proc = self._proc
        if proc and self.running:
            proc.terminate()
            self._append("\n[STOPPED]\n")
            with self._lock:
                self.status = "Stopped"


def build_command(urls, output, cookies, codec, title_only):
    """Mirror gamdl_gui.py's command construction."""
    if getattr(sys, "frozen", False):
        base = [sys.executable]
    else:
        base = [sys.executable, "-m", "gamdl"]

    cmd = base + [
        "--cookies-path", cookies,
        "--output-path", output,
        "--no-config-file",
        "--song-codec-priority", codec,
    ]
    if title_only:
        cmd += [
            "--single-disc-file-template", "{title}",
            "--multi-disc-file-template", "{title}",
            "--no-album-file-template", "{title}",
        ]
    cmd += urls
    return cmd


JOB = Job()


PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="color-scheme" content="dark light">
<title>gamdl</title>
<style>
  :root { --bg:#111418; --card:#1b1f26; --fg:#e6e9ef; --mut:#8b93a1;
          --accent:#2196F3; --border:#2a2f38; --ok:#37b24d; --err:#e03131; }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  body { margin:0; background:var(--bg); color:var(--fg);
         font: 16px/1.4 -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
         padding: env(safe-area-inset-top) env(safe-area-inset-right)
                  env(safe-area-inset-bottom) env(safe-area-inset-left); }
  .wrap { max-width: 680px; margin: 0 auto; padding: 16px; }
  h1 { font-size: 20px; margin: 8px 0 16px; display:flex; align-items:center; gap:8px; }
  .dot { width:10px; height:10px; border-radius:50%; background:var(--mut); }
  .dot.on { background:var(--accent); animation: pulse 1s infinite; }
  .dot.ok { background:var(--ok); } .dot.err { background:var(--err); }
  @keyframes pulse { 50% { opacity:.3; } }
  label { display:block; font-size:13px; color:var(--mut); margin:14px 0 6px; }
  textarea, input[type=text] {
    width:100%; background:var(--card); color:var(--fg); border:1px solid var(--border);
    border-radius:12px; padding:12px 14px; font-size:16px; font-family:inherit; }
  textarea { min-height:96px; resize:vertical; }
  .row { display:flex; gap:10px; flex-wrap:wrap; }
  .chip { flex:1 1 auto; }
  .chip input { position:absolute; opacity:0; pointer-events:none; }
  .chip span { display:block; text-align:center; padding:12px; border-radius:12px;
    background:var(--card); border:1px solid var(--border); color:var(--mut); font-size:14px; }
  .chip input:checked + span { border-color:var(--accent); color:var(--fg);
    background:rgba(33,150,243,.12); }
  .check { display:flex; align-items:center; gap:10px; margin-top:14px; font-size:15px; color:var(--fg); }
  .check input { width:22px; height:22px; accent-color:var(--accent); }
  .btns { display:flex; gap:10px; margin-top:18px; }
  button { flex:1; border:0; border-radius:14px; padding:16px; font-size:17px; font-weight:600;
    color:#fff; background:var(--accent); }
  button.stop { background:#3a3f48; }
  button:disabled { opacity:.45; }
  pre#log { margin-top:18px; background:#0c0e11; border:1px solid var(--border);
    border-radius:12px; padding:12px; height:44vh; overflow:auto; font-size:12px;
    line-height:1.35; white-space:pre-wrap; word-break:break-word;
    font-family: ui-monospace, "SF Mono", Menlo, monospace; color:#c7ccd4; }
  .hint { font-size:12px; color:var(--mut); margin-top:6px; }
</style>
</head>
<body>
<div class="wrap">
  <h1><span class="dot" id="dot"></span>gamdl <span id="status" style="font-size:13px;color:var(--mut);font-weight:400"></span></h1>

  <label>URL(1行に1つ)</label>
  <textarea id="urls" placeholder="https://music.apple.com/jp/album/..." autocapitalize="off" autocorrect="off" spellcheck="false"></textarea>

  <label>保存先(サーバー側のパス)</label>
  <input id="output" type="text" value="__OUTPUT__" autocapitalize="off" autocorrect="off" spellcheck="false">

  <label>cookies.txt(サーバー側のパス)</label>
  <input id="cookies" type="text" value="__COOKIES__" autocapitalize="off" autocorrect="off" spellcheck="false">

  <label>コーデック</label>
  <div class="row" id="codec">__CODECS__</div>

  <label class="check"><input type="checkbox" id="titleonly" checked> ファイル名をタイトルのみにする</label>

  <div class="btns">
    <button id="go">ダウンロード</button>
    <button id="stop" class="stop" type="button">停止</button>
  </div>

  <pre id="log"></pre>
  <div class="hint">同じWi-Fi内のPCで gamdl を実行します。ダウンロードはPC側に保存されます。</div>
</div>

<script>
  var since = 0, es = null;
  var logEl = document.getElementById('log');
  var dot = document.getElementById('dot');
  var statusEl = document.getElementById('status');
  var goBtn = document.getElementById('go');

  function setStatus(s, running){
    statusEl.textContent = s || '';
    dot.className = 'dot' + (running ? ' on' : (/Error/.test(s) ? ' err' : (s==='Done' ? ' ok' : '')));
    goBtn.disabled = !!running;
  }
  function append(lines){
    if(!lines || !lines.length) return;
    var atBottom = logEl.scrollTop + logEl.clientHeight >= logEl.scrollHeight - 30;
    logEl.textContent += lines.join('\\n') + '\\n';
    if(atBottom) logEl.scrollTop = logEl.scrollHeight;
  }
  function poll(){
    fetch('/api/status?since=' + since).then(function(r){return r.json();}).then(function(d){
      if(d.next > since){ append(d.lines); since = d.next; }
      setStatus(d.status, d.running);
    }).catch(function(){});
  }
  setInterval(poll, 1000);
  poll();

  goBtn.onclick = function(){
    var urls = document.getElementById('urls').value.split('\\n')
      .map(function(s){return s.trim();}).filter(Boolean);
    if(!urls.length){ alert('URLを入力してください'); return; }
    var codec = document.querySelector('input[name=codec]:checked');
    logEl.textContent = ''; since = 0;
    fetch('/api/start', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        urls: urls,
        output: document.getElementById('output').value.trim(),
        cookies: document.getElementById('cookies').value.trim(),
        codec: codec ? codec.value : 'aac-legacy',
        titleOnly: document.getElementById('titleonly').checked
      })
    }).then(function(r){return r.json();}).then(function(d){
      if(!d.ok) alert(d.message || 'error');
    });
  };
  document.getElementById('stop').onclick = function(){ fetch('/api/stop', {method:'POST'}); };
</script>
</body>
</html>
"""


def render_page(default_output, default_cookies):
    chips = []
    for i, (label, val) in enumerate(CODEC_OPTIONS):
        checked = "checked" if i == 0 else ""
        chips.append(
            f'<label class="chip"><input type="radio" name="codec" value="{html.escape(val)}" {checked}>'
            f'<span>{html.escape(label)}</span></label>'
        )
    return (
        PAGE.replace("__OUTPUT__", html.escape(default_output))
        .replace("__COOKIES__", html.escape(default_cookies))
        .replace("__CODECS__", "".join(chips))
    )


class Handler(BaseHTTPRequestHandler):
    server_version = "gamdl-web"

    def log_message(self, *args):  # quieter console
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj), "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/" or path == "/index.html":
            self._send(200, self.server.page, "text/html; charset=utf-8")
        elif path == "/api/status":
            since = 0
            if "?" in self.path:
                q = self.path.split("?", 1)[1]
                for part in q.split("&"):
                    if part.startswith("since="):
                        try:
                            since = int(part[6:])
                        except ValueError:
                            since = 0
            self._json(200, JOB.snapshot(since))
        else:
            self._send(404, "not found", "text/plain; charset=utf-8")

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/start":
            length = int(self.headers.get("Content-Length", 0) or 0)
            try:
                data = json.loads(self.rfile.read(length) or "{}")
            except json.JSONDecodeError:
                self._json(400, {"ok": False, "message": "bad json"})
                return
            urls = [u.strip() for u in data.get("urls", []) if str(u).strip()]
            if not urls:
                self._json(400, {"ok": False, "message": "no url"})
                return
            output = data.get("output") or DEFAULT_OUTPUT
            cookies = data.get("cookies") or DEFAULT_COOKIES
            codec = data.get("codec") or "aac-legacy"
            title_only = bool(data.get("titleOnly", True))
            ok, msg = JOB.start(urls, output, cookies, codec, title_only)
            self._json(200 if ok else 409, {"ok": ok, "message": msg})
        elif path == "/api/stop":
            JOB.stop()
            self._json(200, {"ok": True})
        else:
            self._send(404, "not found", "text/plain; charset=utf-8")


def local_ip():
    """Best-effort LAN IP for the console hint."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:  # noqa: BLE001
        return "127.0.0.1"


def main():
    parser = argparse.ArgumentParser(description="Mobile web UI for gamdl")
    parser.add_argument("--host", default="0.0.0.0", help="bind address (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8765, help="port (default 8765)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="default output path shown in the UI")
    parser.add_argument("--cookies", default=DEFAULT_COOKIES, help="default cookies.txt path shown in the UI")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.page = render_page(args.output, args.cookies)

    ip = local_ip()
    print("=" * 48)
    print("  gamdl web UI is running")
    print("=" * 48)
    print(f"  On this PC:      http://localhost:{args.port}")
    print(f"  On your iPhone:  http://{ip}:{args.port}")
    print("  (iPhone must be on the same Wi-Fi network)")
    print("  Press Ctrl+C to stop")
    print("=" * 48)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBye.")
        server.shutdown()


if __name__ == "__main__":
    main()
