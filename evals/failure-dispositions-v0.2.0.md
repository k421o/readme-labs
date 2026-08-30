# v0.2.0 evaluation failure dispositions

The first factory retained failures as design evidence. A later passing run
does not erase them.

| Failure | Material implication | Disposition |
| --- | --- | --- |
| Corpus roles labeled by the bootstrap author were emitted as if declared by upstream repositories. | Observations overstated source authority. | `READMEObservation` v2 separates document identity from derivation identity and requires role-assignment provenance; the pilot was regenerated without relabeling annotation as declaration. |
| Capsule commits used wall-clock time and ambient Git identity; observation IDs ignored derivation inputs. | Repeated runs were not reproducible and distinct derivations could collide. | Fixed timestamps, Git configuration, commit/tree hashes, capsule and mutation hashes, taxonomy hash, and extractor version are recorded and tested. |
| Wrapping Codex in a second host sandbox failed closed because Codex also sandboxes its commands. | The intended blind boundary could not execute and nesting was not evidence of stronger isolation. | The runner uses a Codex permission profile that disables network, allows the materialized workspace, denies the factory checkout, and proves both sides before inference. |
| Early Structured Outputs schemas used unsupported general conditionals and omitted required explicit node types. | Runs could fail before inference while appearing to test capability behavior. | The response schema uses the executor-supported subset; finding/conclusion consistency remains a post-exit scoring rule. |
| Initial responses described an attempted Python check that had no matching exported command event. | Plausible prose could launder an execution claim. | The interface now requires an exact command ledger; the skill audits execution verbs; the scorer reconciles claims with exported events. |
| The intended no-finding fixture said “non-empty” while its implementation excluded whitespace-only lines. | The fixture contained a defensible second finding and could not serve as a clean control. | The README now defines “non-blank” consistently, the implementation and test use that contract, and fixture correctness is tested. |
| Codex serializes shell commands through a quoted `shell -lc` wrapper. | Literal substring comparison rejected true command records. | The scorer parses only recognized shell wrappers and compares their exact payload and outcome. |
| A sandbox-denied tool call is visible to the executor but omitted from Codex `exec --json`; stderr contains only an unattributed violation warning. | Exact automated attribution is impossible with the current host event surface. | The scorer may correlate at most one failed response command per stderr violation, labels it `correlated_unattributed_sandbox_violation`, and leaves semantic acceptance to the independent reviewer. It never calls that an exact command event. |

The release evidence must include one finding and one no-material-finding run
after these dispositions, plus an independent review that checks evidence,
anti-findings, and the unattributed-denial limitation.
