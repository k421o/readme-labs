# High-exposure pilot, version 1

## Result

The 16-document pilot successfully replayed pinned README files from 16 public
repositories, verified every Git blob, and emitted schema-valid structural
observations. It demonstrates a working collection path; it does not estimate
population or training-data prevalence.

The generated aggregate is
[`pilot-high-exposure-v1-summary.json`](pilot-high-exposure-v1-summary.json).

## Descriptive findings

- The sample spans six annotated source distributions, four frameworks or
  platforms, three published packages, and one each of a CLI, end-user
  application, and monorepo root.
- Length is strongly right-skewed: the median is 687 words while the mean is
  1,902.69 and the maximum is 12,672.
- Navigation and example density are also right-skewed. Median counts are nine
  headings, 20 links, and one code block; maxima are 96 headings, 683 links,
  and 106 code blocks.
- Exact conventional-heading signals find a first-successful-path heading in
  six documents, development or participation in seven, and legal/provenance
  in seven.

These distributions already argue against using a mean document or one fixed
template as the definition of normal. A few extensive package manuals dominate
the upper tail, while mature source distributions may use the root README as a
compact router.

## Measurement cautions

The v1 extractor deliberately recognizes exact normalized heading aliases. A
missing signal means “not detected by this structural rule,” not “the README
lacks the semantic category.” For example, only ten documents exposed identity
through a Markdown H1; the others may use HTML titles, image-based wordmarks,
badges, or an opening without a conventional title.

Consequently, the pilot's category rates are parser diagnostics rather than
content-prevalence estimates. The next annotation round should compare exact
heading signals with blinded human semantic labels, calculate precision and
recall, and decide whether broader rules improve measurement without hiding
ambiguity.

Stars, forks, age, and public visibility made these repositories useful
high-exposure examples. None is treated as a quality label or evidence of its
weight in an undisclosed training corpus.
