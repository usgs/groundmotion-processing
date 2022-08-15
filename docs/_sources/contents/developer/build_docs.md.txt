# Build Documentation

Some additional packages are required to build the documentation, which can be included
with the `doc` install option, e.g.,

```
$ pip install .[doc]
```

Then the docs are built with

```
$ cd doc_source/
$ ./makedocs.sh
```

The docs can then be previewed by opening `../docs/index.html` in a browser.

Notes:
 - Never edit the contents of `docs`, only edit the files in `doc_source`.
 - Remember that the notebooks run gmprocess code when you build the docs, 
   so please be sure to check that the tutorials ran sucessfully. 
 - The result of the tutorials will depend on your config file options, 
   so I recommend having a project with the default config file set up 
   and use that project when building the docs. 