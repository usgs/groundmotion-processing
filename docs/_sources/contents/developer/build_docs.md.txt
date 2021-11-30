---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: '0.8'
    jupytext_version: '1.4.1'
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---
# Build Documentation

Some additional packages are required to build the documentation:

```
cd doc_source
mamba install --file requirements.txt
```

Then the docs are built with

```
./makedocs.sh
```

The docs can then be previewed by opening `docs/index.html` in a browser.

Note that you should never edit the contents of `docs`, only edit the
files in `docs_source`.
