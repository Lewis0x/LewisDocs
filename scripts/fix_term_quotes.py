#!/usr/bin/env python3
"""Fix inner ASCII double quotes inside <Term def="..."> attribute values.

Vue's HTML parser treats inner ASCII `"` as the closing of the def attribute,
breaking parsing. Convert each inner pair to fullwidth U+201C/U+201D.

Strategy:
- Walk the file char-by-char.
- When we see `<Term def="`, switch to "inside-def" mode.
- Track inner ASCII `"`s: alternating open (U+201C) / close (U+201D).
- When we hit `">` followed by content, that's the def-end + tag-end —
  but we can't simply look for `">` because innerASCII `"` could fool us.
- Instead, since inner quotes always come in even number (paired text quotes),
  and the def value never legitimately ends with `"...string"` sub-quote,
  we use heuristic: inside def, count ASCII `"` from the start; if even,
  the next `"` is real closer; if odd, it's an inner pair-end.

Simpler: assume the structural pattern is `<Term def="...">term</Term>`.
The first `>` after `<Term def="` is the closing `>`. So the def value is
between `<Term def="` and the LAST `"` BEFORE that first `>`.
"""

import sys, re
from pathlib import Path


def fix_one(s: str) -> tuple[str, int]:
    out = []
    i = 0
    fixed = 0
    prefix = '<Term def="'
    while i < len(s):
        ms = s.find(prefix, i)
        if ms < 0:
            out.append(s[i:])
            break
        out.append(s[i:ms])
        val_start = ms + len(prefix)
        # Find the def attribute's closing quote.
        # A real attribute terminator is `"` followed by ` ` (next attr) or `>` (tag end) or `/` (self-close).
        # Inner ASCII quotes inside the value would be `"<chinese-char>` or similar — never followed by ` ` or `>`.
        j = val_start
        end = -1
        while j < len(s):
            if s[j] == '"' and j + 1 < len(s) and s[j+1] in ' >/':
                end = j
                break
            if s[j] == '\n' and j - val_start > 1000:
                # safety: don't scan unbounded
                break
            j += 1
        if end < 0:
            # malformed; skip
            out.append(s[ms:val_start])
            i = val_start
            continue
        value = s[val_start:end]
        # Convert inner ASCII `"` to alternating U+201C/U+201D
        new_chars = []
        opening = True
        for ch in value:
            if ch == '"':
                new_chars.append('“' if opening else '”')
                opening = not opening
                fixed += 1
            else:
                new_chars.append(ch)
        new_value = ''.join(new_chars)
        out.append(prefix + new_value + '"')
        i = end + 1  # resume right after the def-closing quote (the rest of the tag stays intact)
    return ''.join(out), fixed


def main():
    files = sys.argv[1:] or list(Path('source').glob('*.md'))
    total = 0
    for f in files:
        f = Path(f)
        s = f.read_text(encoding='utf-8')
        new_s, n = fix_one(s)
        if n > 0:
            f.write_text(new_s, encoding='utf-8')
            print(f'  {f}: fixed {n} inner ASCII quotes')
            total += n
    print(f'TOTAL fixed: {total}')


if __name__ == '__main__':
    main()
