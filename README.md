# Cull Segments by Length — Inkscape Extension

**Author:** [DeepfishAI](https://github.com/JeffreyWoodson) · **License:** MIT · **Requires:** Inkscape 1.2+

---

Ever exported a vector trace, laser engraving file, or hatch-fill drawing and ended up with **hundreds of tiny stray line segments** cluttering your artwork? This extension fixes that in seconds.

**Cull Segments by Length** lets you interactively sweep through your drawing's segments by size, watching them disappear in real time, until you've dialed in exactly the right cutoff. One click commits. Nothing is ever permanently deleted.

---

## What It Does

- Scans every `<path>` element in your SVG and measures its length
- Auto-scales to your drawing — no manual threshold guessing needed
- Lets you **step through a live preview** using the arrow keys
- Moves culled segments to a hidden **"Culled"** layer (non-destructive)
- Runs as a native Inkscape dialog with instant canvas updates

---

## How the Math Works

```
baseline  =  longest segment in file  ×  0.20
step      =  baseline  ×  0.01  (1% of baseline per arrow press)
cutoff    =  position  ×  step
```

So on a drawing where the longest line is 700 px:
- **baseline** = 140 px
- **each ↑ press** raises the cutoff by ~1.4 px
- **position 100** hides everything under 140 px (20% of longest line)

This scales automatically — no configuration needed across different file sizes.

---

## Install

1. **Find your Inkscape extensions folder:**

   | OS | Path |
   |----|------|
   | Linux | `~/.config/inkscape/extensions/` |
   | macOS | `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/` |
   | Windows | `%APPDATA%\inkscape\extensions\` |

2. **Copy both files** into a subfolder there:
   ```
   cull_segments.py
   cull_segments.inx
   ```

3. **Restart Inkscape.**

4. The extension appears under:
   **Extensions → DeepfishAI → Cull Segments by Length**

---

## How to Use

| Step | Action |
|------|--------|
| 1 | Open your SVG in Inkscape |
| 2 | Go to **Extensions → DeepfishAI → Cull Segments by Length** |
| 3 | Tick the **☑ Live preview** checkbox at the bottom of the dialog |
| 4 | Click the **Position** spinner to focus it |
| 5 | Tap **↑** — watch segments disappear from the canvas in real time |
| 6 | Keep tapping until the drawing looks clean |
| 7 | Gone too far? Tap **↓** to bring some back |
| 8 | Happy with the result? Click **Apply** |
| 9 | Changed your mind? Click **Close** — everything is restored |

> **Tip:** The "Culled" layer stays in your document (invisible) after Apply.
> Toggle it visible in the Layers panel anytime to review or recover segments.

---

## Performance Note

Path length calculations are expensive on complex files.
The extension caches results to `~/.cache/deepfish/cull_segments.json` after the first run, making every subsequent arrow press near-instant. The cache auto-invalidates when the SVG file changes.

---

## Non-Destructive by Design

- Segments are **moved**, never deleted
- The **"Culled"** layer is hidden but always recoverable
- **Close** (without Apply) restores everything — zero changes to your document
- Full **Undo** support via Inkscape's standard Ctrl+Z after Apply

---

## Requirements

- Inkscape 1.2 or later
- Python 3.8+ (bundled with Inkscape on all platforms)
- GTK 3 (bundled with Inkscape on all platforms)

---

## Contributing

Forks and pull requests are warmly welcomed!
Ideas for future features:

- [ ] Adjustable baseline percentage
- [ ] Scope to selection only (instead of whole document)
- [ ] "Delete" mode as an alternative to the Culled layer
- [ ] Progress bar for very large files

Open an issue or start a discussion — let's build on it.

---

## License

MIT License — Copyright © 2026 DeepfishAI

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
