#!/bin/bash
make html
rm -fr ../docs
mv _build/html ../docs
rm -fr _build
touch ../docs/.nojekyll
