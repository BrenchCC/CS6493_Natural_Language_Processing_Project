# CS6493 Math Reasoning Presentation Deck

This folder contains an English classroom presentation based on `delivery/reports/final_report_en.tex`.

## Files

- `index.html`: keyboard-driven HTML deck with hidden speaker notes.
- `style.css`: Academic Tech styling for the HTML deck.
- `runtime.js`: local copy of the html-ppt runtime for navigation, overview, notes, and presenter mode.
- `CS6493_Math_Reasoning_Presentation.pptx`: editable PowerPoint deck generated with `python-pptx`.
- `slide_manifest.json`: slide titles, layouts, and takeaways.
- `speaker_notes.md`: standalone notes for rehearsal and presenter reference.
- `build_deck.py`: single-source generator for the HTML, manifest, README, and PPTX.
- `validate_deck.py`: validation helper for PPTX structure and 16:9 HTML screenshots.

## Usage

Open `index.html` in a browser for presentation. Keyboard controls:

- `left` / `right` / `space`: navigate slides
- `S`: open presenter mode
- `N`: open the notes drawer
- `O`: open slide overview
- `F`: fullscreen

Regenerate all files:

```bash
python delivery/ppt_slides/build_deck.py
```

Regenerate only HTML assets:

```bash
python delivery/ppt_slides/build_deck.py --skip-pptx
```

Validate the generated deck:

```bash
python delivery/ppt_slides/validate_deck.py
```

The PowerPoint file is intentionally built with editable text boxes, shapes, tables, and charts rather than full-slide screenshots.
