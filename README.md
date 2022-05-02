# Pandoc wikilinks filter

Use as follows:

```bash
pandoc -f markdown -t json file.md | ./wikilinks.py | pandoc -f json -t html
```

The wikilinks logic cannot be done by looking at Pandoc API elements in
isolation (this is because Pandoc splits strings using a separate `Space`
element), so I don't believe it can be done by
[pandocfilters](https://github.com/jgm/pandocfilters). I have therefore
modified the `walk(...)` function in pandocfilters to have the flexibility to
process "sibling" elements at once.

Backslash escaping does not work with wikilinks: `\[\[blah\]\]` will still be
converted to a wikilink. This happens because Pandoc's Markdown reader will
convert both `[[blah]]` and `\[\[blah\]\]` to `{"t":"Str","c":"[[blah]]"}` in
the JSON representation. Respecting backslash escaping will require modifying
Pandoc's Markdown reader and internal JSON representation, so cannot be done
purely via scripting.
