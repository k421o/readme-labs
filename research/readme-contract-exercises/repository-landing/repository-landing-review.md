# Review: repository landing page

Contract evidence: the root `package.json` marks the package private, declares
three Pi skills, and defines `npm test`; the repository host also renders this
root README. The revised document therefore serves visitors and agents seeking
an entry point, not a complete architecture manual.

Changes made:

- Replaced the vague “small prose-quality lab” framing with facts from the
  package manifest.
- Replaced the directory inventory with a task-to-location table, so a reader
  can choose a relevant surface without treating every directory as required
  reading.
- Kept the root test command and linked each optional checker to its own setup
  contract; this removes the implication that the dependency-free root package
  provides those runtimes.
- Removed generic source-of-truth language and retained the architecture link
  only for the concrete need to understand repository boundaries.
