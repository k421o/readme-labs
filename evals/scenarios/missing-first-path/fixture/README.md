# pebble-count

`pebble-count` counts non-empty lines in a UTF-8 text file.

## Getting started

Install the package from this repository and run one file:

```console
python -m pip install -e .
pebble-count notes.txt
```

The command prints one integer: the number of non-empty lines.

## Development

```console
python -m pip install -e '.[dev]'
pytest
```

## License

MIT
