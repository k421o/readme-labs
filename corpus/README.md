# README corpus

The corpus layer records reproducible samples and derived structural
observations. It does not treat a collection of popular repositories as a
quality ranking or as proof of inclusion in a model's training data.

## What is committed

- `manifests/`: one JSON object per source document, pinned to repository
  revision and Git blob.
- `observations/`: derived `READMEObservation` JSON Lines without full README
  bodies.
- `analysis/`: reproducible aggregate outputs and interpretation notes.
- `sampling-plan-v1.md`: the planned separation between prevalence,
  high-exposure, and role-edge-case samples.
- `bootstrap-role-annotation-v1.md`: provenance and limitations for the
  historical role labels in the pilot manifest.

Raw third-party README bodies are fetched into an untracked cache. The
collector verifies each body against its Git blob SHA before extracting an
observation.

## Reproduce the pilot

```console
uv run readme-lab corpus collect \
  corpus/manifests/pilot-high-exposure-v1.jsonl \
  --cache /tmp/readme-labs-pilot-cache \
  --observations corpus/observations/pilot-high-exposure-v1.jsonl

uv run readme-lab corpus summarize \
  corpus/observations/pilot-high-exposure-v1.jsonl \
  --output corpus/analysis/pilot-high-exposure-v1-summary.json
```

The committed pilot is intentionally small and purposive. It exists to test
collection and analysis contracts before a population sampling frame is
claimed.
