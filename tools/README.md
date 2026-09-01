# Asset toolchain

`gen.py` generates everything in `../assets`. Text is converted to outlines, so the
rendering does not depend on fonts installed on the viewer's machine.

```bash
pip install uharfbuzz fonttools
python gen.py
```

Change the brand colour in `BRAND`, the light/dark tokens in `LIGHT` / `DARK`,
and the section titles in `SECTIONS`.

Fonts in `fonts/` are Archivo and JetBrains Mono, both SIL Open Font License 1.1.
Brand icons in `icons/` come from Simple Icons (CC0); LinkedIn, mail and globe are
drawn in `gen.py` itself.
