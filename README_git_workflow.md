
my typical git workflow...

```
cd ciscoconfparse/
git checkout master
# Ensure I start with a local git master branch in sync with remote master
#   -> https://stackoverflow.com/a/62653400/667301
git pull --ff-only

# Checkout a new branch (some_feature_branch) add / modify code...
git switch -c some_feature_branch

# -> run tests after modifying some_feature_branch
make test

# -> be sure to update pyproject.toml and CHANGES
git commit <files> -m "Describe changes here"

# Merge some_feature_branch into master
git checkout master
git merge some_feature_branch -m "Bring a new feature into the main branch"
make repo-push-tag
make pypi

# Clean up the working feature branch
git branch -d some_feature_branch
```
