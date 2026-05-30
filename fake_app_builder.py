#!/usr/bin/env python3
"""
Fake App Builder
Generates real .exe files with custom names and icons that can be
pinned to the Windows taskbar.

Requirements (auto-installed on first run):
  pip install pyinstaller pillow

Usage:
  python fake_app_builder.py
"""

import subprocess
import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import shutil
import tempfile

# ── Auto-install dependencies ─────────────────────────────────────────────────
def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

try:
    import PyInstaller
except ImportError:
    print("Installing PyInstaller...")
    install("pyinstaller")

try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    install("pillow")
    from PIL import Image

# ── Helpers ───────────────────────────────────────────────────────────────────

EMOJIS = [
    "🚀","💎","🔥","⚡","🎯","🛸","🤖","🧬","🌐","🧠",
    "🎮","🛡️","🔮","💡","🦄","🐉","🎵","📡","🧲","⚙️",
    "🌈","🏆","🦊","🐺","🌙","☀️","🧊","🎲","🔑","💣",
]

EMOJI_COLORS = {
    "🚀":"#4e9af1","💎":"#a8d8ff","🔥":"#ff6b35","⚡":"#ffd700",
    "🎯":"#e94560","🛸":"#7b68ee","🤖":"#5bc0be","🧬":"#6fbe6f",
    "🌐":"#4e9af1","🧠":"#e890c0","🎮":"#9b59b6","🛡️":"#3498db",
    "🔮":"#8e44ad","💡":"#f1c40f","🦄":"#ff6eb4","🐉":"#e74c3c",
    "🎵":"#1abc9c","📡":"#95a5a6","🧲":"#e67e22","⚙️":"#7f8c8d",
    "🌈":"#e74c3c","🏆":"#f39c12","🦊":"#e67e22","🐺":"#7f8c8d",
    "🌙":"#f1c40f","☀️":"#f39c12","🧊":"#74b9ff","🎲":"#6c5ce7",
    "🔑":"#fdcb6e","💣":"#2d3436",
}

def make_ico_from_emoji(emoji: str, out_path: str):
    """Render an emoji into a .ico file using Pillow."""
    from PIL import Image, ImageDraw, ImageFont
    size = 256
    color = EMOJI_COLORS.get(emoji, "#4e9af1")
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Rounded rect background
    margin = 12
    draw.rounded_rectangle([margin, margin, size-margin, size-margin],
                            radius=48, fill=color)
    # Try to draw emoji with a system font
    font = None
    font_size = 160
    candidates = [
        "seguiemj.ttf",  # Windows Segoe UI Emoji
        "/System/Library/Fonts/Apple Color Emoji.ttc",  # macOS
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",  # Linux
    ]
    for c in candidates:
        if os.path.exists(c) or (not os.path.sep in c and shutil.which(c)):
            try:
                font = ImageFont.truetype(c, font_size)
                break
            except Exception:
                continue

    if font:
        # Center the emoji
        bbox = draw.textbbox((0, 0), emoji, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        x = (size - tw) // 2 - bbox[0]
        y = (size - th) // 2 - bbox[1]
        draw.text((x, y), emoji, font=font, embedded_color=True)
    else:
        # Fallback: draw a white letter
        try:
            fb_font = ImageFont.truetype("arial.ttf", 120)
        except Exception:
            fb_font = ImageFont.load_default()
        letter = emoji[0] if emoji else "A"
        bbox = draw.textbbox((0, 0), letter, font=fb_font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        x = (size - tw) // 2
        y = (size - th) // 2
        draw.text((x, y), letter, font=fb_font, fill="white")

    # Save all sizes into one .ico
    sizes = [(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
    imgs = [img.resize(s, Image.LANCZOS) for s in sizes]
    imgs[0].save(out_path, format="ICO", sizes=[(i.width, i.height) for i in imgs],
                 append_images=imgs[1:])


def make_ico_from_image(src_path: str, out_path: str):
    """Convert any image to a proper .ico, center-cropping to square first."""
    from PIL import Image
    img = Image.open(src_path).convert("RGBA")

    # Center-crop to square so the image is never squished
    w, h = img.size
    side = min(w, h)
    left   = (w - side) // 2
    top    = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))

    # Resize to each ico size using high-quality LANCZOS
    sizes = [(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
    imgs = [img.resize(s, Image.LANCZOS) for s in sizes]
    imgs[0].save(out_path, format="ICO", sizes=[(i.width, i.height) for i in imgs],
                 append_images=imgs[1:])


def build_exe(app_name: str, version: str, ico_path: str,
              out_dir: str, log_callback):
    """
    Create a minimal stub .py, then compile it with PyInstaller
    into a single .exe with the given icon.
    """
    safe_name = "".join(c for c in app_name if c.isalnum() or c in " _-").strip()
    if not safe_name:
        safe_name = "FakeApp"

    tmpdir = tempfile.mkdtemp(prefix="fakeapp_")
    stub_path = os.path.join(tmpdir, "stub.py")

    # The stub: a real Windows app that sits quietly in the tray / does nothing
    stub_code = f'''
import sys
import os

APP_NAME = {repr(app_name)}
VERSION   = {repr(version)}

# Hide the console window on Windows
if sys.platform == "win32":
    import ctypes
    ctypes.windll.user32.ShowWindow(
        ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Just keep the process alive briefly so Windows registers it properly
import time
time.sleep(0.5)
'''
    with open(stub_path, "w", encoding="utf-8") as f:
        f.write(stub_code)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", safe_name,
        "--icon", ico_path,
        "--version-file", _write_version_file(tmpdir, app_name, version, safe_name),
        "--distpath", out_dir,
        "--workpath", os.path.join(tmpdir, "build"),
        "--specpath", tmpdir,
        "--noconfirm",
        "--clean",
        stub_path,
    ]

    log_callback(f"Building {safe_name}.exe …\n")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    for line in proc.stdout:
        log_callback(line)
    proc.wait()

    shutil.rmtree(tmpdir, ignore_errors=True)

    exe_path = os.path.join(out_dir, safe_name + ".exe")
    if proc.returncode == 0 and os.path.exists(exe_path):
        return exe_path
    return None


def _write_version_file(tmpdir, app_name, version, safe_name):
    """Write a Windows version-info file for PyInstaller."""
    parts = version.split(".")
    while len(parts) < 4:
        parts.append("0")
    try:
        nums = ",".join(str(int(p)) for p in parts[:4])
    except ValueError:
        nums = "1,0,0,0"

    content = f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({nums}),
    prodvers=({nums}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(u'040904B0', [
        StringStruct(u'CompanyName', u'Fake Corp'),
        StringStruct(u'FileDescription', u'{app_name}'),
        StringStruct(u'FileVersion', u'{version}'),
        StringStruct(u'InternalName', u'{safe_name}'),
        StringStruct(u'LegalCopyright', u'© 2025 Fake Corp'),
        StringStruct(u'OriginalFilename', u'{safe_name}.exe'),
        StringStruct(u'ProductName', u'{app_name}'),
        StringStruct(u'ProductVersion', u'{version}'),
      ])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    path = os.path.join(tmpdir, "version.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ── GUI ───────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fake App Builder")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")

        self.app_name    = tk.StringVar(value="TurboSyncer Pro")
        self.app_version = tk.StringVar(value="3.1.4")
        self.selected_emoji = tk.StringVar(value="🚀")
        self.custom_icon_path = None
        self.emoji_btns  = {}

        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        BG    = "#1a1a2e"
        CARD  = "#16213e"
        ACCENT= "#e94560"
        FG    = "#eaeaea"
        FG2   = "#9a9ab0"
        EBG   = "#0f3460"
        FONT  = ("Segoe UI", 10)
        FBOLD = ("Segoe UI", 11, "bold")
        FSMALL= ("Segoe UI", 9)
        FTITLE= ("Segoe UI", 15, "bold")
        FMONO = ("Consolas", 9)

        # Header
        hdr = tk.Frame(self, bg=CARD, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙  Fake App Builder", font=FTITLE, bg=CARD, fg=FG).pack()
        tk.Label(hdr, text="Generates a real .exe you can pin to your taskbar",
                 font=FSMALL, bg=CARD, fg=FG2).pack()

        body = tk.Frame(self, bg=BG, padx=16, pady=14)
        body.pack(fill="both", expand=True)

        left  = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky="n", padx=(0,14))
        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")

        def lbl(parent, text):
            tk.Label(parent, text=text.upper(), font=("Segoe UI",8),
                     bg=BG, fg=FG2).pack(anchor="w", pady=(10,3))

        # Name
        lbl(left, "App Name")
        tk.Entry(left, textvariable=self.app_name, font=FBOLD,
                 bg=EBG, fg=FG, insertbackground=FG,
                 relief="flat", width=26, bd=6).pack(fill="x")

        # Version
        lbl(left, "Version")
        tk.Entry(left, textvariable=self.app_version, font=FONT,
                 bg=EBG, fg=FG, insertbackground=FG,
                 relief="flat", width=26, bd=6).pack(fill="x")

        # Emoji grid
        lbl(left, "Icon — pick emoji")
        gf = tk.Frame(left, bg=BG)
        gf.pack(fill="x")
        cols = 6
        for i, em in enumerate(EMOJIS):
            def _cmd(e=em):
                self.selected_emoji.set(e)
                self.custom_icon_path = None
                self.icon_note.configure(text="No custom icon selected", fg=FG2)
                for em2, b in self.emoji_btns.items():
                    b.configure(bg=ACCENT if em2==e else EBG)
            b = tk.Button(gf, text=em, font=("",13), bg=ACCENT if em=="🚀" else EBG,
                          fg=FG, relief="flat", width=2, cursor="hand2",
                          command=_cmd, bd=0, padx=2, pady=2)
            b.grid(row=i//cols, column=i%cols, padx=2, pady=2)
            self.emoji_btns[em] = b

        # Custom icon upload
        lbl(left, "Or upload your own .ico / .png")
        tk.Button(left, text="📂  Browse…", font=FONT, bg=EBG, fg=FG,
                  relief="flat", cursor="hand2", pady=5,
                  command=self._browse).pack(fill="x")
        self.icon_note = tk.Label(left, text="No custom icon selected",
                                  font=FSMALL, bg=BG, fg=FG2, wraplength=220)
        self.icon_note.pack(anchor="w", pady=(3,0))

        # Output folder
        lbl(left, "Save .exe to folder")
        row = tk.Frame(left, bg=BG)
        row.pack(fill="x")
        self.out_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop"))
        tk.Entry(row, textvariable=self.out_var, font=FSMALL,
                 bg=EBG, fg=FG, insertbackground=FG,
                 relief="flat", bd=4, width=19).pack(side="left", fill="x", expand=True)
        tk.Button(row, text="…", font=FONT, bg=EBG, fg=FG, relief="flat",
                  cursor="hand2", width=2,
                  command=self._pick_out).pack(side="left", padx=(4,0))

        # Build button
        tk.Button(left, text="🔨  Build .exe", font=FBOLD,
                  bg=ACCENT, fg="white", relief="flat",
                  cursor="hand2", pady=8,
                  command=self._start_build).pack(fill="x", pady=(16,0))

        # Right: log
        lbl(right, "Build log")
        log_frame = tk.Frame(right, bg="#0d1117")
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(log_frame, font=FMONO, bg="#0d1117", fg="#58a6ff",
                           relief="flat", width=42, height=26,
                           bd=8, state="disabled", wrap="word",
                           insertbackground=FG)
        sb = tk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._log("Ready. Fill in the details and click Build .exe.\n\n"
                  "Note: first build may take ~30–60 s while\n"
                  "PyInstaller sets up its cache.\n")

    # ── Actions ───────────────────────────────────────────────────────────────
    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select icon",
            filetypes=[("Images", "*.ico *.png *.jpg *.jpeg *.bmp"), ("All", "*.*")])
        if path:
            self.custom_icon_path = path
            self.icon_note.configure(text=f"✓ {os.path.basename(path)}", fg="#58a6ff")
            self.selected_emoji.set("🖼")
            for b in self.emoji_btns.values():
                b.configure(bg="#0f3460")

    def _pick_out(self):
        d = filedialog.askdirectory(title="Choose output folder")
        if d:
            self.out_var.set(d)

    def _log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _start_build(self):
        name    = self.app_name.get().strip()
        version = self.app_version.get().strip() or "1.0.0"
        out_dir = self.out_var.get().strip()

        if not name:
            messagebox.showwarning("Missing name", "Please enter an app name.")
            return
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning("Bad folder", "Please choose a valid output folder.")
            return

        self._log(f"\n{'─'*40}\nStarting build: {name} v{version}\n{'─'*40}\n")
        threading.Thread(target=self._build_thread,
                         args=(name, version, out_dir), daemon=True).start()

    def _build_thread(self, name, version, out_dir):
        tmpdir = tempfile.mkdtemp(prefix="fakeico_")
        ico_path = os.path.join(tmpdir, "icon.ico")

        try:
            # Build the .ico
            if self.custom_icon_path:
                self._log("Converting custom image to .ico …\n")
                make_ico_from_image(self.custom_icon_path, ico_path)
            else:
                emoji = self.selected_emoji.get()
                self._log(f"Rendering emoji {emoji} to .ico …\n")
                make_ico_from_emoji(emoji, ico_path)

            # Compile
            exe = build_exe(name, version, ico_path, out_dir, self._log)

            if exe:
                self._log(f"\n✅  Done!  {exe}\n\n"
                          f"Right-click it → Pin to taskbar\n")
                self.after(0, lambda: messagebox.showinfo(
                    "Done!", f"Built successfully:\n{exe}\n\n"
                             "Right-click the .exe → Pin to taskbar!"))
            else:
                self._log("\n❌  Build failed. See log above.\n")
                self.after(0, lambda: messagebox.showerror(
                    "Failed", "Build failed. Check the log for details."))
        except Exception as e:
            self._log(f"\n❌  Error: {e}\n")
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    App().mainloop()