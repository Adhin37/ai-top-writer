---
type: howto
title: Where canon comes from
description: Where the canon researcher looks, what outranks what when sources disagree, how to fetch wiki pages with tools/canon_fetch.py, and what to do when a site refuses.
roles: [canon-researcher]
---
# Where canon comes from

## What outranks what

1. **The work itself**, in the edition the scope names: a chapter the user saved into
   `work/canon/inbox/`, or a chapter summary that cites its chapter.
2. **The author and the publisher**: the author's notes, an official guide or databook, the
   author's answers in interviews or on their own pages.
3. **The fan wiki**, for most facts. Good wikis cite chapter and episode; prefer a line that does.
   An infobox is a summary: read the article's history section when an age or a rank changes over
   time.
4. **Fan discussion** (forums, reddit, reviews): only for `## Fans expect`, never for a fact. A
   belief fans share but canon never states is **fanon**: write it down as fanon, so the planner
   neither contradicts fans by accident nor states it as canon.

When two sources disagree, the higher one wins, and inside the scope the version it names wins (the
novel over the anime, say). Write each disagreement fans know about in `## Conflicts`.

## Finding the wiki

WebSearch for `<source work> wiki` and the main characters' names. Most fan wikis are on Fandom
(`<name>.fandom.com`); some stand alone. A wiki whose pages look current and cite their chapters is
the one to use; a stub wiki is worth only what it cites.

## Fetching

Wiki pages come through `tools/canon_fetch.py`, which reads the wiki's own API (the route wikis give
programs; their web pages may sit behind a bot check). Cache every page under the novel:

```
python3 tools/canon_fetch.py search <wiki> <words>
python3 tools/canon_fetch.py category <wiki> Characters
python3 tools/canon_fetch.py page <wiki> <Title> <Title> --out novels/<slug>/work/canon/src/<wiki>
```

- `<wiki>` is the host: `ashfall.fandom.com`. A title takes underscores for spaces and `%28` `%29`
  for brackets: `Corin_Dask`, `Ilse_Maro_%28novel%29`. Search first when unsure of a title.
- Each page lands as a text file: its URL, its categories, the infobox as `key: value` lines, then
  the article. Read it there; cite the page's URL in `## Sources`.
- A page already cached is not fetched again. Fetch the pages you need, not the whole wiki: a
  category listing tells you who exists, and the pages close to the story's start tell you most.

Everything else (Wikipedia, an author's site, a publisher's page) you read with WebFetch.

## A site that refuses

Some sites refuse programs: they answer with a challenge, an error, or a `robots.txt` that shuts
the door. `canon_fetch.py` prints `blocked` and goes on; WebFetch fails. **Do not work around a
refusal** (another address for the same page, a cache or mirror of it, a different tool). Look for
the fact in another source. If no source has it, the fact goes under `## Unsure`, and the page in
your final message as `blocked`: the user can save it into `work/canon/inbox/`, and a lookup picks
it up.
