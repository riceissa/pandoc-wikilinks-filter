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
def wikilink_whole(string):
    '''If string is a whole wikilink (i.e., includes both the opening and
    closing brackets), then return the wikilinked text as a dictionary, with
    the surrounding text preserved separately. Otherwise, return an empty
    dictionary.'''
    m = re.match(r'([^\[]*)\[\[([^\[\]]+)\]\](.*)$', string)
    if m:
        return {"before": group(1), "text": m.group(2), "after": m.group(3)}
    else:
        return ""

def wikilink_start(string):
    m = re.match(r'[^\[]*\[\[([^\[]+)$', string)
    if m:
        return m.group(1)
    else:
        return ""

def wikilink_end(string):
    m = re.match(r'([^\]]*)\]\]', string)
    if m:
        return m.group(1)
    else:
        return ""

def wikilinked(source):
    doc = json.loads(source)

    altered = doc
    altered = walk(altered)
    # altered["blocks"] = walk(altered["blocks"])

    return json.dumps(altered)


def f(x):
    string = ""
    for item in x:
        if x['t'] == 'Space':
            string += " "
        else:
            string += x['c']
    array = []
    state = "free"
    for c in string:
        if state == "free" and c == "[":
            state = "1["
        elif state == "free":
            pass
        elif state == "1[" and c == "[":
            state = "2["
        elif state == "1[":
            state = "free"
        elif state == "2[" and c == "[":
            pass
        elif state == "2[" and c == "]":
            state = "empty ]"
        elif state == "2[":
            state = "in"
        elif state == "empty ]" and c == "]":
            state = "free"
        elif state == "empty ]":
            state = "in"
        elif state == "in" and c == "]":
            state = "1]"
        elif state == "in":
            pass
        elif state == "1]" and c == "]":
            state = "free"
        elif state == "1]":
            state = "in"
        else:
            raise ValueError("This shouldn't happen")
    return array


# modified from https://github.com/jgm/pandocfilters/blob/06f4db99548a129c3ee8ac667436cb51a80c0f58/pandocfilters.py#L103
def walk(x):
    # print("IN WALK:", x)
    if isinstance(x, list):
        # We want to look for any contiguous block of Strs and Spaces that look
        # like a wikilink and convert them to a Link, and not touch anything
        # else
        array = []
        # In case we don't encounter a "]]" later, we'll have to
        # append all the elements we _thought_ were going into a
        # wikilink, so save them just in case
        saved_elements = []
        for item in x:
            if isinstance(item, dict) and 't' in item:
                if item['t'] in ['Str', 'Space']:
                    saved_elements.append(item)
                else:
                    # process the saved elements
                    array.extend(f(saved_elements))
                    saved_elements = []
                    array.append(walk(item))
            else:
                array.extend(f(saved_elements))
                saved_elements = []
                array.append(walk(item))
        # If an unclosed wikilink is the last thing in the file, there is still
        # some saved elements that haven't been added to the array
        array.extend(f(saved_elements))
        return array
    elif isinstance(x, dict):
        return {k: walk(v) for k, v in x.items()}
    else:
        return x



# https://github.com/jgm/pandocfilters/blob/06f4db99548a129c3ee8ac667436cb51a80c0f58/pandocfilters.py#L170
input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

source = input_stream.read()
sys.stdout.write(wikilinked(source))
