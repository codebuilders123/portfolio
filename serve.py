"""
BSVS Vidyalayam - Web Server + ngrok
Usage: python serve.py
"""
import http.server, socketserver, threading
import subprocess, time, json, urllib.request
import sys, os

# ─── Settings ────────────────────────────────────────────
TOKEN    = "3FPBq1siA1eRJaQQhkAovFkF6Bw_3K7dPBPnjR3yq7rDZCXUV"
PORT     = 8082
DIR      = r"C:\3051"
NGROK    = (r"C:\Users\HP\AppData\Local\Packages"
            r"\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0"
            r"\LocalCache\local-packages\Python311\Scripts\ngrok.exe")

# ─── 1. Kill any existing ngrok ───────────────────────────
subprocess.run(["taskkill","/F","/IM","ngrok.exe"],
               capture_output=True)
time.sleep(2)

# ─── 2. Save auth token ───────────────────────────────────
subprocess.run([NGROK,"config","add-authtoken", TOKEN],
               capture_output=True, timeout=10)

# ─── 3. HTTP server ───────────────────────────────────────
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**k):
        super().__init__(*a,directory=DIR,**k)
    def log_message(self,*a): pass
    def end_headers(self):
        self.send_header("ngrok-skip-browser-warning","true")
        super().end_headers()

socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(("",PORT),H)
threading.Thread(target=srv.serve_forever,daemon=True).start()
print(f"\n[✓] HTTP server  →  http://localhost:{PORT}/bsvs_school.html")

# ─── 4. Start ngrok ───────────────────────────────────────
ng = subprocess.Popen(
    [NGROK,"http",str(PORT),
     "--log","stdout",
     "--log-format","json",
     "--log-level","info"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True, bufsize=1
)
print("[✓] ngrok started, waiting for URL...\n")

# ─── 5. Read URL from ngrok stdout directly ───────────────
url = None
deadline = time.time() + 20
for line in ng.stdout:
    if time.time() > deadline:
        break
    try:
        obj = json.loads(line)
        # ngrok logs the URL in the "url" field when tunnel is started
        if obj.get("url","").startswith("http"):
            url = obj["url"]
            if url.startswith("http://"):
                url = "https://" + url[7:]
            break
        # also check "msg":"started tunnel"
        if "started tunnel" in obj.get("msg",""):
            addr = obj.get("addr","") or obj.get("url","")
            if addr.startswith("http"):
                url = addr
                if url.startswith("http://"):
                    url = "https://" + url[7:]
                break
    except Exception:
        # check raw line for URL pattern
        if "ngrok-free" in line or "ngrok.io" in line:
            import re
            m = re.search(r"https?://[^\s\"]+(?:ngrok-free\.app|ngrok\.io|ngrok-free\.dev)[^\s\"]*", line)
            if m:
                url = m.group(0).rstrip('"').rstrip("'")
                break

# fallback: poll the REST API
if not url:
    for _ in range(10):
        time.sleep(1)
        try:
            with urllib.request.urlopen(
                    "http://127.0.0.1:4040/api/tunnels",timeout=3) as r:
                d = json.loads(r.read())
                for t in d.get("tunnels",[]):
                    u = t.get("public_url","")
                    if u.startswith("https://"):
                        url = u; break
                if url: break
        except Exception:
            pass

# ─── 6. Print result ──────────────────────────────────────
print("="*62)
if url:
    print("  🎉  BSVS VIDYALAYAM IS LIVE!")
    print("="*62)
    print()
    print("  ┌─ SHARE THIS LINK ─────────────────────────────────┐")
    print(f"  │  {url}/bsvs_school.html")
    print("  └───────────────────────────────────────────────────┘")
    print()
    print(f"  📊  Inspector  →  http://127.0.0.1:4040")
    print(f"  💻  Local      →  http://localhost:{PORT}/bsvs_school.html")
else:
    print("  ⚠  Could not fetch public URL automatically.")
    print("  → Open http://127.0.0.1:4040 in your browser")
    print(f"  → Local: http://localhost:{PORT}/bsvs_school.html")
print()
print("  Press Ctrl+C to stop.")
print("="*62)

# ─── 7. Keep alive ───────────────────────────────────────
try:
    threading.Event().wait()
except KeyboardInterrupt:
    print("\n[✓] Stopped.")
    ng.terminate()
    srv.shutdown()
    sys.exit(0)
