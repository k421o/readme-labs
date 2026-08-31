# Markdown structure v1

This built-in analyzer is the first calibration instrument for README static
analysis. It deliberately checks context-free Markdown properties rather than
requiring a particular README section set or progressive-disclosure design.

Its four rules localize heading-level jumps, empty headings, repeated normalized
heading labels, and Markdown images with empty alternative text. A diagnostic
means “inspect this property in context.” It does not mean the README failed,
that a hypothesis should stop, or that an agent should mechanically rewrite the
document.

The initial corpus characterization exists to show how these rules behave on
real, high-exposure README documents before their feedback is incorporated into
iteration. The same adapter can then run on a generated or ingested README and
place a diagnostic record beside soft agent-review evidence.
