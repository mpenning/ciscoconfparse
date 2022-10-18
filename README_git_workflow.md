
my typical git workflow...

```
cd ciscoconfparse/
git checkout main
# Ensure I start with a local git master branch in sync with remote master
#   -> https://stackoverflow.com/a/62653400/667301
git pull --ff-only

# Create and checkout a new branch (named some_feature_branch) and edit code...
git checkout -b some_feature_branch

# -> run tests after modifying some_feature_branch
make test

# -> be sure to update pyproject.toml and CHANGES.md
git commit <files> -m "Describe changes here"

# If releasing on pypi, bump version number in pyproject.toml...
vi pyproject.toml

# If releasing on pypi, add changes into CHANGES.md
vi CHANGES.md

git commit pyproject.toml -m "Roll version number"
git commit CHANGES.md -m "Roll version number"

# Use either A> or B> below...
#   A> rebase some_feature_branch into the main branch...  then 'git merge'...
git checkout some_feature_branch (warning: do NOT rebase a public branch!)
git rebase main
git checkout main
# https://stackoverflow.com/a/21717431/667301
git merge --no-ff some_feature_branch

#   B> Merge some_feature_branch into master...
git checkout main
# https://stackoverflow.com/a/21717431/667301
git merge --no-ff some_feature_branch -m "Bring a new feature into the main branch"

make repo-push-tag
make pypi

# Clean up the working feature branch
git branch -d some_feature_branch
```
