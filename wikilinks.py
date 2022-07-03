#!/usr/bin/env python3

import json
import sys
import io
import argparse

BASE_URL = ""
SAVE_LINKS = False
LINKS = []

def link(link_text, url):
    return {
               't': 'Link',
               'c': [
                   ["", [], []],
                   [{'t': 'Str', "c": link_text}],
                   [url, ""]
               ]
           }

def slugify(s):
    '''
    "Slugify" the string s as follows: keep only the characters that are
    alphabetic or numerical, and group them together; all other characters are
    replaced by "-" and squeezed together.
    '''
    s = s.lower()
    s = "".join(c if (c.isalpha() or c.isdigit()) else "-" for c in s)
    s = "-".join(filter(bool, s.split("-")))
    return s


def wikilinked(source):
    doc = json.loads(source)
    doc = walk(doc)
    return json.dumps(doc)


def process_elements(x):
    """
    Given a list containing just Str and Space elements, like
    [{"t":"Str","c":"[[hello"},{"t":"Space"},{"t":"Str","c":"world]]"}]
    convert all wikilinks into actual links.
    """
    return process_string(stringify_elements_list(x))

def stringify_elements_list(x):
    """We assume that only Str and Space elements appear in a flat (i.e., not
    nested) list."""
    string = ""
    for item in x:
        if item['t'] == 'Space':
            string += " "
        else:
            string += item['c']
    return string

def process_string(string):
    array = []
    state = "free"
    saved_inner = ""
    saved_outer = ""
    for c in string:
        # At every point in time, we should be exactly one of: (1) inside a
        # wikilink ("in"), (2) outside a wikilink ("free"), or (3) in between
        # (one of the bracket states). So we should only be using one of
        # saved_inner or saved_outer. This means that we could get away with
        # using just a single variable "saved", but I think that would be a bit
        # more confusing to think about.
        assert not (saved_inner and saved_outer)
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
            if saved_outer:
                array.append({"t": "Str", "c": saved_outer})
            saved_outer = ""
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
                array.append(link(text, BASE_URL + slugify(target)))
                if SAVE_LINKS:
                    LINKS.append(target)
            else:
                array.append(link(saved_inner, BASE_URL + slugify(saved_inner)))
                if SAVE_LINKS:
                    LINKS.append(saved_inner)
            saved_inner = ""
        elif state == "1]":
            state = "in"
            saved_inner += "]" + c
        else:
            raise ValueError("This shouldn't happen")
    # Only one of these should be non-empty, for the same reasoning as above.
    assert not (saved_inner and saved_outer)
    # print(x, state, saved_inner, file=sys.stderr)
    if state == "in":
        array.append({"t": "Str", "c": "[[" + saved_inner})
    elif state == "1[":
        array.append({"t": "Str", "c": saved_outer + "["})
    elif state == "2[":
        array.append({"t": "Str", "c": saved_outer + "[["})
    elif state == "empty ]":
        array.append({"t": "Str", "c": "[[]"})
    elif state == "1]":
        array.append({"t": "Str", "c": "[[" + saved_inner + "]"})
    elif state == "free" and saved_outer:
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
                array.extend(process_elements(saved_elements))
                saved_elements = []

                array.append(walk(item))
        array.extend(process_elements(saved_elements))
        return array
    elif isinstance(x, dict):
        return {k: walk(v) for k, v in x.items()}
    else:
        return x


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='A Pandoc filter to convert wikilinks.')
    parser.add_argument('--base-url', nargs='?',
                        help=('The base URL that all wikilinks will use.'
                              ' For example, if BASE_URL is'
                              ' "https://example.com/", then [[wikilink]]'
                              ' will be converted to'
                              ' [wikilink](https://example.com/wikilink).'),
                        default='')
    parser.add_argument('--save-links', action="store_true", help="Save wikilinks in a file specified by this flag. Wikilinks will be appended to this file, so that running this script with a bunch of markdown files will collect wikilinks for all input files, thereby building a link graph. Having such a file is useful if for instance one wants to invert the link graph to create Roam-style backlinks sections. To use this flag, one must also specify a filename to associate with the current file, using the --filename flag.")
    args = parser.parse_args()
    BASE_URL = args.base_url
    SAVE_LINKS = args.save_links

    # https://github.com/jgm/pandocfilters/blob/06f4db99548a129c3ee8ac667436cb51a80c0f58/pandocfilters.py#L170
    input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

    source = input_stream.read()
    wikilinked_source = wikilinked(source)
    if not SAVE_LINKS:
        sys.stdout.write(wikilinked_source)

    if SAVE_LINKS:
        sys.stdout.write('[' +
            ", ".join(map(lambda x: '"' + x.replace('"', '\\"') + '"', LINKS)) +
            ']\n')
