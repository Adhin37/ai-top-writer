# EQ-Bench slop lists

`slop_list.json` (1,000 words), `slop_list_bigrams.json` and `slop_list_trigrams.json` (200 each),
copied unchanged from EQ-Bench's [creative-writing-bench](https://github.com/EQ-bench/creative-writing-bench)
`data/` (last changed in commit `9bbcf6c1d86a`, 2025-03-31; the same files ship in
[longform-writing-bench](https://github.com/EQ-bench/longform-writing-bench)). By Sam Paech;
MIT licence, per the repositories' READMEs.

`tools/lib/slop.py` scores a text with them exactly as `calculate_slop_index_new` in that repo's
`core/metrics.py` does, so the figure sits beside EQ-Bench's published slop scores.
