#!/usr/bin/env python3

import json
import sys
import io
import re

def link(link_text, url):
    return {
            't': 'Link',
            'c': [
                  ["", [], []],
                  [{'t': 'Str', "c": link_text}],
                  [url, ""]
                 ]
           }

def slugify(string):
    return string.lower().replace(" ", "-")

# TODO: hmm, what about things like "[[lol]][[blah]]"?
# also things like "[[work]]ed"
# also things like "[[test|hello]]"

def wikilinked(source):
    doc = json.loads(source)
    doc = walk(doc)
    return json.dumps(doc)


def f(x):
    string = ""
    for item in x:
        if item['t'] == 'Space':
            string += " "
        else:
            string += item['c']
    array = []
    state = "free"
    saved_inner = ""
    saved_outer = ""
    # TODO: check the state transitions here more closely.
    for c in string:
        # print(state, c, "in:", saved_inner, "out:", saved_outer, file=sys.stderr)
        if state == "free" and c == "[":
            state = "1["
        elif state == "free":
            saved_outer += c
        elif state == "1[" and c == "[":
            state = "2["
        elif state == "1[":
            state = "free"
            saved_outer += "[" + c
        elif state == "2[" and c == "[":
            saved_outer += "["
        elif state == "2[" and c == "]":
            state = "empty ]"
        elif state == "2[":
            if saved_outer:
                array.append({"t": "Str", "c": saved_outer})
            saved_outer = ""
            saved_inner = c
            state = "in"
        elif state == "empty ]" and c == "]":
            state = "free"
        elif state == "empty ]":
            saved_inner = "]" + c
            if saved_outer:
                array.append({"t": "Str", "c": saved_outer})
            saved_outer = ""
            state = "in"
        elif state == "in" and c == "]":
            state = "1]"
        elif state == "in":
            saved_inner += c
        elif state == "1]" and c == "]":
            state = "free"
            if "|" in saved_inner:
                target, text = saved_inner.split("|", 1)
                array.append(link(text, "https://issarice.com/" + slugify(target)))
            else:
                array.append(link(saved_inner, "https://issarice.com/" + slugify(saved_inner)))
            saved_inner = ""
        elif state == "1]":
            state = "in"
        else:
            raise ValueError("This shouldn't happen")
    # Only one of these should be non-empty
    assert not (saved_inner and saved_outer)
    if saved_inner:
        array.append({"t": "Str", "c": "[[" + saved_inner})
    if state == "1[":
        array.append({"t": "Str", "c": "["})
    if state == "2[":
        array.append({"t": "Str", "c": "[["})
    if saved_outer:
        array.append({"t": "Str", "c": saved_outer})
    return array


# modified from https://github.com/jgm/pandocfilters/blob/06f4db99548a129c3ee8ac667436cb51a80c0f58/pandocfilters.py#L103
def walk(x):
    # print("IN WALK:", x)
    if isinstance(x, list):
        # We want to look for any contiguous block of Strs and Spaces that look
        # like a wikilink and convert them to a Link, and not touch anything
        # else
        array = []
        # Save up Str and Space elements in a list to process them in bulk
        # (it's way easier to parse wikilinks if each piece of text is all in
        # one place instead of being broken up by Str elements).
        saved_elements = []
        for item in x:
            if isinstance(item, dict) and 't' in item and item['t'] in ['Str', 'Space']:
                saved_elements.append(item)
            else:
                # Process the saved elements
                array.extend(f(saved_elements))
                saved_elements = []

                array.append(walk(item))
        array.extend(f(saved_elements))
        return array
    elif isinstance(x, dict):
        return {k: walk(v) for k, v in x.items()}
    else:
        return x


if __name__ == "__main__":

    # https://github.com/jgm/pandocfilters/blob/06f4db99548a129c3ee8ac667436cb51a80c0f58/pandocfilters.py#L170
    input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

    source = input_stream.read()
    sys.stdout.write(wikilinked(source))
