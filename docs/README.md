## Preview documentation locally

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
