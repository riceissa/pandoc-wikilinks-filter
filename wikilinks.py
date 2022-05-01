#!/usr/bin/env python3

import json
import sys
import io

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

def is_wikilink_start(string):
    return string.startswith("[[")

def is_wikilink_end(string):
    return string.endswith("]]")

def wikilinked(source):
    doc = json.loads(source)

    altered = doc
    altered = walk(altered)
    # altered["blocks"] = walk(altered["blocks"])

    return json.dumps(altered)

'''
two bugs:
    - if wikilink is the last thing in the file, then we lose all the elements. so need to check if saved_elements is non-empty after the loop.
'''

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
        state = "free"
        for item in x:
            if isinstance(item, dict) and 't' in item:
                if item['t'] == 'Str' and is_wikilink_start(item['c']) and is_wikilink_end(item['c']):
                    array.extend(saved_elements)
                    wikilink_text = item['c'][len("[["):-len("]]")]
                    new_element = link(wikilink_text, "https://issarice.com/" + slugify(wikilink_text))
                    array.append(new_element)
                    saved_elements = []
                    state = "free"
                elif item['t'] == 'Str' and is_wikilink_start(item['c']):
                    state = "in"
                    wikilink_text = item['c'][len("[["):]
                    array.extend(saved_elements)
                    saved_elements = [item]
                elif item['t'] == 'Str' and state == "in" and is_wikilink_end(item['c']):
                    wikilink_text += item['c'][:-len("]]")]
                    new_element = link(wikilink_text, "https://issarice.com/" + slugify(wikilink_text))
                    array.append(new_element)
                    wikilink_text = None
                    saved_elements = []
                    state = "free"
                elif item['t'] not in ['Str', 'Space']:
                    state = "free"
                    wikilink_text = None
                    array.extend(saved_elements)
                    saved_elements = []
                    array.append(walk(item))
                elif item['t'] == 'Space' and state == "in":
                    saved_elements.append(item)
                    wikilink_text += " "
                elif item['t'] == 'Str' and state == "in":
                    saved_elements.append(item)
                    wikilink_text += item['c']
                elif item['t'] in ['Str', 'Space'] and state == "free":
                    array.append(item)
                else:
                    raise ValueError("Unknown thing")
            else:
                array.append(walk(item))
                state = "free"
        return array
    elif isinstance(x, dict):
        return {k: walk(v) for k, v in x.items()}
    else:
        return x



# https://github.com/jgm/pandocfilters/blob/06f4db99548a129c3ee8ac667436cb51a80c0f58/pandocfilters.py#L170
input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

source = input_stream.read()
sys.stdout.write(wikilinked(source))
