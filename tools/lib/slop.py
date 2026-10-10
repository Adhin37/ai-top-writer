"""EQ-Bench's slop index: hits on its lists of words, bigrams and trigrams that models overuse,
per 1,000 words (`tools/data/eqbench/NOTICE.md`). The formula is theirs, unchanged, so the figure
can be set beside their published scores: (words + 2 x bigrams + 8 x trigrams) / tokens x 1000,
over lowercased alphanumeric tokens. A reference, not a rule: a fantasy name can be on the list.
"""

import json
import os
import re
from collections import Counter

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "eqbench")
TOKEN = re.compile(r"\b\w+\b")
_LISTS = {}


def lists():
    """(words, bigrams, trigrams), each a set of lowercased strings, loaded once."""
    if not _LISTS:
        for n, name in ((1, "slop_list.json"), (2, "slop_list_bigrams.json"),
                        (3, "slop_list_trigrams.json")):
            with open(os.path.join(DATA, name), encoding="utf-8") as fh:
                _LISTS[n] = {item[0].lower() for item in json.load(fh) if item}
    return _LISTS[1], _LISTS[2], _LISTS[3]


def score(text):
    """(index, tokens, Counter of hits by item), the index per 1,000 tokens."""
    tokens = TOKEN.findall(text.lower())
    if not tokens:
        return 0.0, 0, Counter()
    hits = Counter()
    for n, items in zip((1, 2, 3), lists()):
        for i in range(len(tokens) - n + 1):
            gram = " ".join(tokens[i:i + n])
            if gram in items:
                hits[gram] += 1
    weight = {1: 1, 2: 2, 3: 8}
    total = sum(c * weight[len(g.split())] for g, c in hits.items())
    return total * 1000.0 / len(tokens), len(tokens), hits
