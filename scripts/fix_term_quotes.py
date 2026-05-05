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
    while i < len(s):
        match_start = s.find('<Term def="', i)
        if match_start < 0:
            out.append(s[i:])
            break
        out.append(s[i:match_start])
        # find closing > of this tag
        gt = s.find('>', match_start)
        if gt < 0:
            out.append(s[match_start:])
            break
        tag = s[match_start:gt+1]
        # tag = '<Term def="<value>">'
        # value = everything between match_start+11 and the last `"` before gt
        prefix = '<Term def="'
        # find LAST `"` before the closing `>`
        last_quote = tag.rfind('"', 0, len(tag)-1)  # exclude trailing >
        # Actually `tag` ends with `>`, so we need last `"` before that >
        # tag[len(tag)-1] = '>'; tag[len(tag)-2] should be '"'
        if tag[-2] != '"':
            # malformed; skip
            out.append(tag)
            i = gt + 1
            continue
        value = tag[len(prefix):-2]  # strip prefix and trailing `">`
        # convert inner ASCII `"` to alternating U+201C/U+201D
        new_value_chars = []
        opening = True
        for ch in value:
            if ch == '"':
                new_value_chars.append('“' if opening else '”')
                opening = not opening
                fixed += 1
            else:
                new_value_chars.append(ch)
        new_value = ''.join(new_value_chars)
        new_tag = prefix + new_value + '">'
        out.append(new_tag)
        i = gt + 1
    return ''.join(out), fixed


def main():
    files = sys.argv[1:] or list(Path('source').glob('3.*.md'))
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
