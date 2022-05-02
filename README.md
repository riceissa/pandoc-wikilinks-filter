# Pandoc wikilinks filter

Use as follows:

```bash
pandoc -f markdown -t json example.md | ./wikilinks.py --base-url="https://issarice.com/" | pandoc -f json -t html
```

The wikilinks logic cannot be done by looking at Pandoc API elements in
isolation (this is because Pandoc splits strings using a separate `Space`
element, so we can't just apply some function to all `Str` elements),
so I don't believe it can be done by
[pandocfilters](https://github.com/jgm/pandocfilters). I have therefore
modified the `walk` function in pandocfilters to have the flexibility to
process "sibling" elements at once.

Backslash escaping does not work with wikilinks: `\[\[blah\]\]` will still be
converted to a wikilink. This happens because Pandoc's Markdown reader will
convert both `[[blah]]` and `\[\[blah\]\]` to `{"t":"Str","c":"[[blah]]"}` in
the JSON representation. Respecting backslash escaping will require modifying
Pandoc's Markdown reader and internal JSON representation, so cannot be done
purely via scripting.

You may want to modify the `slugify` function if your wikilink URLs use a
different logic. Right now it converts `[[I said I'll do my chores]]` to
`i-said-i-ll-do-my-chores`.

License: Since I've copied some lines from pandocfilters and taken the basic
structure of the `walk` function, I've just copied the license file from that
repo.
