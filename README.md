# Pandoc wikilinks filter

Use as follows:

```bash
pandoc -f markdown -t json file.md | ./wikilinks.py | pandoc -f json -t html
```

The wikilinks logic cannot be done by looking at Pandoc API elements in
isolation, so I don't believe it can be done by pandocfilters.
I have therefore modified the `walk(...)` function to have the flexibility
to process "sibling" elements at once.
