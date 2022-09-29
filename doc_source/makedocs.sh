#!/bin/bash

# We retain the _build/html directory to allow caching of generated documentation.
# You can run `rm -r _build` to force a complete rebuild of the documentation.

make html
rm -fr ../docs
cp -r _build/html ../docs
touch ../docs/.nojekyll
