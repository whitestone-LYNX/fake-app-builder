# Fake App Builder

A simple Python desktop app that generates real `.exe` files with custom names and icons — so you can pin fake apps to your Windows taskbar just for fun.

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey) ![License](https://img.shields.io/badge/License-MIT-green)

---

## What it does

- Type in any app name and version
- Pick an emoji icon or upload your own image (`.ico`, `.png`, `.jpg`)
- Click **Build .exe** — and a real executable lands on your Desktop
- Right-click it → **Pin to taskbar**, just like any real app

---

## Requirements

- Python 3.8 or newer → [python.org](https://python.org/downloads)
- Two dependencies (install once):

```
pip install pyinstaller pillow
```

---

## How to run

Open a terminal wherever you saved the `.py`-file. 
Enter this:
```
python fake_app_builder.py
```
That's it, you're good to go.

---

## Tips

- **Use `.ico` files for the best icon quality.** PNG works too, but `.ico` files already contain all the right sizes Windows needs.
- You can find free `.ico` files at [icons8.com](https://icons8.com) or [flaticon.com](https://flaticon.com).
- The first build takes about 30–60 seconds while PyInstaller warms up. Subsequent builds are much faster.
- The generated `.exe` does nothing when launched — it just exists so you can pin it.
- I recommend saving the `.exe` under `Documents`, if you don't want a desktop "shortcut".

---

## Questions or issues?

Feel free to open an issue on this repo, or reach out to me directly — **[@Whitestone](https://github.com/whitestone-LYNX)**. Happy to help!
