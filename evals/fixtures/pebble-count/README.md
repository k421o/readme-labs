# pebble-count

`pebble-count` counts non-blank lines in a UTF-8 text file. A line containing
only whitespace is blank.

## Getting started

Install the package from this repository and run one file:

```console
python -m pip install -e .
pebble-count notes.txt
```

The command prints one integer: the number of non-blank lines.

## Development

```console
python -m pip install -e '.[dev]'
pytest
```

## License

MIT
