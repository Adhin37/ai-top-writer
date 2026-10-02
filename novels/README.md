# novels/

One directory per book, `novels/<slug>/`. Gitignored: the toolkit does not version or back up the
books it helps write. Format: [docs/novel-format.md](../docs/novel-format.md).

`_template/` is the empty novel `/new` starts from: `python3 tools/scaffold.py new <slug>` copies
it, the planner's init interview fills every `{{…}}` in it, and `python3 tools/scaffold.py check
novels/<slug>` says what is left.
