DOCHOST ?= $(shell bash -c 'read -p "documentation host: " dochost; echo $$dochost')

# dynamic ciscoconfparse VERSION detection (via version str in pyproject.toml)
#    Ref -> https://stackoverflow.com/a/71592061/667301
export VERSION := $(shell grep version pyproject.toml | tr -s ' ' | tr -d "'" | tr -d '"' | cut -d' ' -f3)

# We must escape Makefile dollar signs as $$foo...
export PING_STATUS := $(shell perl -e '@output = qx/ping -q -W0.5 -c1 4.2.2.2/; $$alloutput = join "", @output; if ( $$alloutput =~ /\s0\sreceived/ ) { print "failure"; } else { print "success"; }')

export NUMBER_OF_CCP_TESTS := $(shell grep "def " tests/test*py | wc -l)

# Makefile color codes...
#     ref -> https://stackoverflow.com/a/5947802/667301
COL_GREEN=\033[0;32m
COL_CYAN=\033[0;36m
COL_YELLOW=\033[0;33m
COL_RED=\033[0;31m
COL_END=\033[0;0m

.DEFAULT_GOAL := test

# Ref -> https://stackoverflow.com/a/26737258/667301
# Ref -> https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/
.PHONY: pypi-package-infra
pypi-package-infra:
	@echo "$(COL_GREEN)>> building ciscoconfparse pypi artifacts (wheel and tar.gz)$(COL_END)"
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	# Delete bogus files... see https://stackoverflow.com/a/73992288/667301
	perl -e 'unlink( grep { /^\W\d*\.*\d*/ && !-d } glob( "*" ) );'

.PHONY: pypi
pypi:
	@echo "$(COL_CYAN)>> uploading ciscoconfparse pypi artifacts to pypi$(COL_END)"
	make clean
	# upgrade pip if-required
	make pip
	# upgrade packaging infra and ciscoconfparse dependencies...
	make pypi-package-infra
	# tag the repo with $$VERSION and push to origin
	git tag $$VERSION
	git push origin $$VERSION
	poetry lock --no-update
	poetry build
	# twine is the simplest pypi package uploader...
	python -m twine upload dist/*

.PHONY: bump-version-patch
bump-version-patch:
	$(shell python dev_tools/git_helper.py -I patch)

.PHONY: bump-version-minor
bump-version-minor:
	$(shell python dev_tools/git_helper.py -I minor)


.PHONY: repo-push
repo-push:
	@echo "$(COL_GREEN)>> git push and merge (w/o force) to ciscoconfparse main branch to github$(COL_END)"
	make ping
	-git checkout master || git checkout main # Add dash to ignore checkout fails
	# Now the main branch is checked out...
	THIS_BRANCH=$(shell git branch --show-current)  # assign 'main' to $THIS_BRANCH
	git merge @{-1}                           # merge the previous branch into main...
	git push origin $(THIS_BRANCH)            # git push to origin / $THIS_BRANCH
	git checkout @{-1}                        # checkout the previous branch...


.PHONY: repo-push-force
repo-push-force:
	@echo "$(COL_GREEN)>> git push and merge (w/ force) ciscoconfparse local main branch to github$(COL_END)"
	make ping
	-git checkout master || git checkout main # Add dash to ignore checkout fails
	# Now the main branch is checked out...
	THIS_BRANCH=$(shell git branch --show-current)  # assign 'main' to $THIS_BRANCH
	git merge @{-1}                           # merge the previous branch into main...
	git push --force-with-lease origin $(THIS_BRANCH)    # force push to origin / $THIS_BRANCH
	git checkout @{-1}                        # checkout the previous branch...

.PHONY: repo-push-tag
repo-push-tag:
	@echo "$(COL_GREEN)>> git push (w/ local tag) ciscoconfparse local main branch to github$(COL_END)"
	git push origin +main
	git push --tags origin +main

.PHONY: repo-push-tag-force
repo-push-tag-force:
	@echo "$(COL_GREEN)>> git push (w/ local tag and w/ force) ciscoconfparse local main branch to github$(COL_END)"
	git push --force-with-lease origin +main
	git push --force-with-lease --tags origin +main

.PHONY: pylama
pylama:
	@echo "$(COL_GREEN)>> running pylama against ciscoconfparse$(COL_END)"
	# Good usability info here -> https://pythonspeed.com/articles/pylint/
	pylama --ignore=E501,E301,E265,E266 ciscoconfparse/*py | less -XR

.PHONY: pylint
pylint:
	@echo "$(COL_GREEN)>> running pylint against ciscoconfparse$(COL_END)"
	# Good usability info here -> https://pythonspeed.com/articles/pylint/
	pylint --rcfile=./utils/pylintrc --ignore-patterns='^build|^dist|utils/pylintrc|README.rst|CHANGES|LICENSE|MANIFEST.in|Makefile|TODO' --output-format=colorized * | less -XR

.PHONY: tutorial
tutorial:
	@echo ">> building the ciscoconfparse tutorial"
	rst2html5 --jquery --reveal-js --pretty-print-code --embed-stylesheet --embed-content --embed-images tutorial/ccp_tutorial.rst > tutorial/ccp_tutorial.html

.PHONY: parse-ios
parse-ios:
	cd tests; python parse_test.py 1 | less -XR

.PHONY: parse-ios-factory
parse-ios-factory:
	cd tests; python parse_test.py 2 | less -XR

.PHONY: parse-ios-banner
parse-iosxr-banner:
	cd tests; python parse_test.py 3 | less -XR

.PHONY: perf-acl
perf-acl:
	cd tests; python performance_case.py 5 | less -XR

.PHONY: perf-factory-intf
perf-factory-intf:
	cd tests; python performance_case.py 6 | less -XR

.PHONY: flake
flake:
	flake8 --ignore E501,E226,E225,E221,E303,E302,E265,E128,E125,E124,E41,W291 --max-complexity 10 ciscoconfparse | less

.PHONY: coverage
coverage:
	@echo "[[[ py.test Coverage ]]]"
	cd tests;py.test --cov-report term-missing --cov=ciscoconfparse.py -s -v

.PHONY: pydocstyle
pydocstyle:
	# Run a numpy-style doc checker against all files matching ciscoconfparse/*py
	find ciscoconfparse/*py | xargs -I{} pydocstyle --convention=numpy {}

.PHONY: doctest
doctest:
	# Run the doc tests
	cd sphinx-doc; make doctest

.PHONY: pip
pip:
	@echo "$(COL_GREEN)>> Upgrading pip to the latest version$(COL_END)"
	make ping
	pip install -U pip>=22.2.0

.PHONY: dep
dep:
	@echo "$(COL_GREEN)>> installing all ciscoconfparse prod dependencies$(COL_END)"
	pip install -U dnspython==1.15.0 # Previously version 1.14.0
	pip install -U passlib==1.7.4
	pip install -U loguru==0.6.0
	pip install -U toml>=0.10.2
	pip install -U deprecat==2.1.1

.PHONY: dev
dev:
	@echo "$(COL_GREEN)>> installing all prod and development ciscoconfparse dependencies$(COL_END)"
	make pip
	make dep
	pip install -U virtualenv
	pip install -U virtualenvwrapper>=4.8.0
	pip install -U pss
	pip install -U mock
	pip install -U highlights>=0.1.1
	pip install -U diff_highlight>=1.2.0
	pip install -U alabaster==0.7.12
	pip install -U sphinx>=5.2.0
	pip install -U sphinx-bootstrap-theme>=0.8.1
	pip install -U rst2html5>=2.0
	pip install -U rst2html5-tools>=0.5.3
	pip install -U pytest>=7.1.0
	pip install -U mccabe
	pip install -U flake8
	pip install -U black>=22.8.0
	pip install -U yapf
	pip install -U fabric>=2.7.0
	pip install -U invoke>=1.7.0
	pip install -U ipaddr>=2.2.0

.PHONY: rm-timestamp
rm-timestamp:
	@echo "$(COL_GREEN)>> delete .pip_dependency if older than a day$(COL_END)"
	#delete .pip_dependency if older than a day
	$(shell find .pip_dependency -mtime +1 -exec rm {} \;)

.PHONY: timestamp
timestamp:
	@echo "$(COL_GREEN)>> delete .pip_dependency if older than a day$(COL_END)"
	$(shell touch .pip_dependency)

.PHONY: ping
ping:
	@echo "$(COL_GREEN)>> ping to ensure internet connectivity$(COL_END)"
	@if [ "$${PING_STATUS}" = 'success' ]; then return 0; else return 1; fi

.PHONY: test
test:
	@echo "$(COL_GREEN)>> running unit tests$(COL_END)"
	$(shell touch .pip_dependency)
	make timestamp
	#make ping
	make clean
	cd tests && ./runtests.sh

.PHONY: clean
clean:
	@echo "$(COL_GREEN)>> cleaning the repo$(COL_END)"
	# Delete bogus files... see https://stackoverflow.com/a/73992288/667301
	perl -e 'unlink( grep { /^=\d*\.*\d*/ && !-d } glob( "*" ) );'
	find ./* -name '*.pyc' -exec rm {} \;
	find ./* -name '*.so' -exec rm {} \;
	find ./* -name '*.coverage' -exec rm {} \;
	@# A minus sign prefixing the line means it ignores the return value
	-find ./* -path '*__pycache__' -exec rm -rf {} \;
	@# remove all the MockSSH keys
	-find ./* -name '*.key' -exec rm {} \;
	-rm -rf poetry.lock
	-rm -rf .pytest_cache/
	-rm -rf .eggs/
	-rm -rf .cache/
	-rm -rf build/ dist/ ciscoconfparse.egg-info/ setuptools*

.PHONY: help
help:
	@# An @ sign prevents outputting the command itself to stdout
	@echo "help                 : You figured that out ;-)"
	@echo "pypi                 : Build the project and push to pypi"
	@echo "repo-push            : Build the project and push to github"
	@echo "test                 : Run all doctests and unit tests"
	@echo "dev                  : Get all dependencies for the dev environment"
	@echo "dep                  : Get all prod dependencies"
	@echo "devtest              : Run tests - Specific to Mike Pennington's build env"
	@echo "coverage             : Run tests with coverage - Specific to this build env"
	@echo "flake                : Run PyFlake code audit w/ McCabe complexity"
	@echo "clean                : Housecleaning"
	@echo "parse-ios            : Parse configs/sample_01.ios with default args"
	@echo "parse-ios-factory    : Parse configs/sample_01.ios with factory=True"
	@echo "parse-iosxr-banner   : Parse an interesting IOSXR banner"
	@echo "perf-acl             : cProfile configs/sample_05.ios (100 acls)"
	@echo "perf-factory-intf    : cProfile configs/sample_06.ios (many intfs, factory=True)"
	@echo ""
