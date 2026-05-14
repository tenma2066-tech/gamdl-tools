import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

if getattr(sys, "frozen", False):
    _here = os.path.dirname(sys.executable)
else:
    _here = os.path.dirname(os.path.abspath(__file__))

_default_cookies = os.path.join(_here, "cookies.txt")
_default_output  = os.path.join("D:\\", "music")

CODEC_OPTIONS = [
    ("AAC 256kbps (no Wrapper)", "aac-legacy"),
    ("ALAC lossless (Wrapper required)", "alac"),
]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("gamdl GUI")
        self.resizable(True, True)
        self.minsize(640, 480)
        self._build()
        self._proc = None

    def _build(self):
        pad = {"padx": 8, "pady": 4}

        # URL
        tk.Label(self, text="URL (1 per line):").pack(anchor="w", **pad)
        self.url_box = scrolledtext.ScrolledText(self, height=4, wrap=tk.WORD)
        self.url_box.pack(fill="x", padx=8)

        # Output dir
        f1 = tk.Frame(self); f1.pack(fill="x", **pad)
        tk.Label(f1, text="Output:").pack(side="left")
        self.out_var = tk.StringVar(value=_default_output)
        tk.Entry(f1, textvariable=self.out_var, width=50).pack(side="left", padx=4)
        tk.Button(f1, text="Browse", command=self._browse_out).pack(side="left")

        # Cookies
        f2 = tk.Frame(self); f2.pack(fill="x", **pad)
        tk.Label(f2, text="cookies.txt:").pack(side="left")
        self.cookies_var = tk.StringVar(value=_default_cookies)
        tk.Entry(f2, textvariable=self.cookies_var, width=50).pack(side="left", padx=4)
        tk.Button(f2, text="Browse", command=self._browse_cookies).pack(side="left")

        # Codec
        f3 = tk.Frame(self); f3.pack(fill="x", **pad)
        tk.Label(f3, text="Codec:").pack(side="left")
        self.codec_var = tk.StringVar(value="aac-legacy")
        for label, val in CODEC_OPTIONS:
            tk.Radiobutton(f3, text=label, variable=self.codec_var, value=val).pack(side="left", padx=6)

        # Template
        f4 = tk.Frame(self); f4.pack(fill="x", **pad)
        self.title_only_var = tk.BooleanVar(value=True)
        tk.Checkbutton(f4, text="Title-only filenames (no track number prefix)", variable=self.title_only_var).pack(side="left")

        # Buttons
        f5 = tk.Frame(self); f5.pack(fill="x", **pad)
        self.dl_btn = tk.Button(f5, text="Download", width=14, bg="#2196F3", fg="white",
                                command=self._start)
        self.dl_btn.pack(side="left", padx=4)
        tk.Button(f5, text="Stop", width=8, command=self._stop).pack(side="left")
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(f5, textvariable=self.status_var, fg="gray").pack(side="left", padx=12)

        # Log
        tk.Label(self, text="Log:").pack(anchor="w", **pad)
        self.log = scrolledtext.ScrolledText(self, height=16, state="disabled",
                                             bg="#1e1e1e", fg="#d4d4d4",
                                             font=("Consolas", 9))
        self.log.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _browse_out(self):
        d = filedialog.askdirectory(initialdir=self.out_var.get())
        if d: self.out_var.set(d)

    def _browse_cookies(self):
        f = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("All", "*")])
        if f: self.cookies_var.set(f)

    def _log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _start(self):
        urls = [u.strip() for u in self.url_box.get("1.0", "end").splitlines() if u.strip()]
        if not urls:
            self._log("[ERROR] No URL entered.\n"); return

        out  = self.out_var.get().strip()
        cook = self.cookies_var.get().strip()
        codec = self.codec_var.get()

        if getattr(sys, "frozen", False):
            exe = sys.executable
        else:
            exe = os.path.join(_here, "gamdl_dl.py")
            exe = [sys.executable, exe]

        cmd = (exe if isinstance(exe, list) else [exe]) + [
            "--cookies-path", cook,
            "--output-path", out,
            "--no-config-file",
            "--song-codec-priority", codec,
        ]
        if self.title_only_var.get():
            cmd += [
                "--single-disc-file-template", "{title}",
                "--multi-disc-file-template",  "{title}",
                "--no-album-file-template",    "{title}",
            ]
        cmd += urls

        os.makedirs(out, exist_ok=True)
        self._log(f"\n[START] {' '.join(str(c) for c in cmd)}\n\n")
        self.dl_btn.configure(state="disabled")
        self.status_var.set("Downloading...")

        def run():
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            self._proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", env=env,
            )
            for line in self._proc.stdout:
                # filter out the noisy [download] progress lines
                if line.startswith("[download]") and "%" in line:
                    continue
                self.after(0, self._log, line)
            self._proc.wait()
            code = self._proc.returncode
            self.after(0, self._log, f"\n[DONE] exit code {code}\n")
            self.after(0, self.status_var.set, "Done" if code == 0 else f"Error (exit {code})")
            self.after(0, self.dl_btn.configure, {"state": "normal"})
            self._proc = None

        threading.Thread(target=run, daemon=True).start()

    def _stop(self):
        if self._proc:
            self._proc.terminate()
            self._log("\n[STOPPED]\n")
            self.status_var.set("Stopped")
            self.dl_btn.configure(state="normal")


if __name__ == "__main__":
    app = App()
    app.mainloop()
