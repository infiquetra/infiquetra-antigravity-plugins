# Renderer receipt

**Renderer:** `rsvg-convert version 2.62.3`.

The source diagram is `profile-evolution-antigravity-front-door.svg` with a
fixed 1600 by 900 view box. The checked-in PNG was reproduced byte-for-byte
from that source with:

```bash
rsvg-convert --width 1600 --height 900 \
  profile-evolution-antigravity-front-door.svg \
  --output profile-evolution-antigravity-front-door.png
```

The SVG is the editable source; the PNG is the portable rendered copy.

## Portable source/render binding

| Source / render | Source SHA-256 | Render SHA-256 |
|---|---|---|
| `profile-evolution-antigravity-front-door.svg` / `profile-evolution-antigravity-front-door.png` | `1617282fde4cb7a5fe52945924b561052ded9b86b052f4ba72ee02d5ffa15e6c` | `f94cd25503a585cf2e22a5116e2e1e6aa063636e4bdeb3c38086ee11ed7e391c` |

Any source or render change requires rerendering, visual inspection, and new
digests.
