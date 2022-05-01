#!/usr/bin/env python3

import json
import sys
import io
import pdb

def wikilinked(source):
    doc = json.loads(source)

    altered = doc
    altered = walk(altered)
    # altered["blocks"] = walk(altered["blocks"])

    return json.dumps(altered)

# modified from https://github.com/jgm/pandocfilters/blob/06f4db99548a129c3ee8ac667436cb51a80c0f58/pandocfilters.py#L103
def walk(x):
    # print("IN WALK:", x)
    if isinstance(x, list):
        # We want to look for any contiguous block of Strs and Spaces that look
        # like a wikilink and convert them to a Link, and not touch anything
        # else
        array = []
        i = 0
        state = "free"
        for item in x:
            if isinstance(item, dict) and 't' in item:
                if item['t'] == 'Str' and item['c'].startswith("[["):
                    state = "in"
                    wikilink_text = item['c'][len("[["):]
                elif item['t'] == 'Str' and state == "in" and item['c'].endswith("]]"):
                    wikilink_text += item['c'][:len("]]")]
                    new_element = {'t': 'Link',
                                   'c': [["",[],[]],
                                         [{"t":"Str", "c": wikilink_text}],
                                         ["https://issarice.com",""]]}
                    array.append(new_element)
                    wikilink_text = None
                    state = "free"
                elif item['t'] not in ['Str', 'Space']:
                    state = "free"
                    wikilink_text = None
                    array.append(walk(item))
                elif item['t'] == 'Space' and state == "in":
                    wikilink_text += " "
                elif item['t'] == 'Str' and state == "in":
                    wikilink_text += item['c']
                elif item['t'] in ['Str', 'Space'] and state == "free":
                    pass
                else:
                    raise ValueError("Unknown thing")
            else:
                array.append(walk(item))
                state = "free"
        # while True:
        #     try:
        #         x[i]['t']
        #     except TypeError:
        #         print(x)
        #     if x[i]['t'] == 'Str' and x[i]['c'].startswith("[["):
        #         state = "in"
        #         wikilink_text = x[i]['c'][len("[["):]
        #         initial_idx = i
        #         length = 1
        #         i += 1
        #     elif x[i]['t'] == 'Str' and state == "in" and x[i]['c'].endswith("]]"):
        #         wikilink_text += x[i]['c'][:len("]]")]
        #         length += 1
        #         # for k in range(initial_idx, initial_idx + length):
        #         #     x.pop(k)
        #         new_element = {'t': 'Link',
        #                        'c': [["",[],[]],
        #                              [{"t":"Str", "c": wikilink_text}],
        #                              ["https://issarice.com",""]]}
        #         # x.insert(initial_idx, new_element)
        #         array.append(new_element)
        #         state = "free"
        #         # i = initial_idx + 1
        #         i += 1
        #         wikilink_text = None
        #         initial_idx = None
        #         length = None
        #         if i >= len(x):
        #             break
        #     elif x[i]['t'] not in ['Str', 'Space']:
        #         state = "free"
        #         wikilink_text = None
        #         initial_idx = None
        #         length = None
        #         array.append(walk(x[i]))
        #         i += 1
        #     elif x[i]['t'] == 'Space' and state == "in":
        #         wikilink_text += " "
        #         length += 1
        #         i += 1
        #     elif x[i]['t'] == 'Str' and state == "in":
        #         wikilink_text += x[i]['c']
        #         length += 1
        #         i += 1
        #     elif x[i]['t'] in ['Str', 'Space'] and state == "free":
        #         i += 1
        #     else:
        #         raise ValueError("Unknown thing")
        return array
    elif isinstance(x, dict):
        return {k: walk(v) for k, v in x.items()}
    else:
        return x



# https://github.com/jgm/pandocfilters/blob/06f4db99548a129c3ee8ac667436cb51a80c0f58/pandocfilters.py#L170
input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

source = input_stream.read()
sys.stdout.write(wikilinked(source))
