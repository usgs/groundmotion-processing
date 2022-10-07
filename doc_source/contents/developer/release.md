# Release Steps

1. Start branch with name of release version like "v121"
2. Update version in setup.cfg
3. Add new section to code.json; update "metadataLastUpdated" date and the urls that include the version.
4. Update `doc_source/contents/developer/changelog.md` to include changes for this version.
5. Rebuild docs
6. Create tag locally with
   ```term
   git tag v1.2.1
   ```
7. Push tag to upstream/main
   ```term
   git push origin v1.2.1
   ```
8. Create release from tag in github. Give it a release title like "v1.2.1"
9. Copy/paste the relevant part of the changelog into the "describe this release" section

