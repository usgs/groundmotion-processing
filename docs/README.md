## Preview documentation locally

See (GitHub Pages Help)[https://help.github.com/en/articles/setting-up-your-github-pages-site-locally-with-jekyll] for more information.

1. Verify you have ruby 2.1.0 or later
```
$ ruby --version
```

2. **Optional** Set location for gems
```
$ export GEM_HOME=PATH_TO_USER_GEMS
$ export PATH=$PATH:$GEM_HOME/bin
```

3. Install bundler
```
$ gem install bundler
```

4. Install local gems
```
$ cd groundmotion-processing/docs
$ bundle install
```

5. Run Jekyll site locally
```
$ cd groundmotion-processing/docs
$ bundle exec jekyll serve
```

## Jekyll documentation

* (Data Files)[https://jekyllrb.com/docs/datafiles/]
* (Static Files)[https://jekyllrb.com/docs/static-files/]
* (Navigation)[https://jekyllrb.com/tutorials/navigation/]
* (Variables)[https://jekyllrb.com/docs/variables/]

## Quick Reference

* Table of contents is set in in `_data/navbar.yml`
* Include script `{% include_relative FILENAME %}`
