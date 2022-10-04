#!/bin/bash

# We retain the _build/html directory to allow caching of generated documentation.
# You can run `rm -r _build` to force a complete rebuild of the documentation.

make html
if [ $? -ne 0 ];then
    echo "Failed make HTML. Exiting."
    exit 1
fi
rm -fr ../docs
cp -r _build/html ../docs
touch ../docs/.nojekyll
