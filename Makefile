DOCHOST ?= $(shell bash -c 'read -p "documentation host: " dochost; echo $$dochost')
# VERSION detection:
#    Ref -> https://stackoverflow.com/a/71592061/667301
VERSION := $(shell grep version pyproject.toml | tr -s ' ' | tr -d "'" | tr -d '"' | cut -d' ' -f3)

.DEFAULT_GOAL := test

# Ref -> https://stackoverflow.com/a/26737258/667301
# Ref -> https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/
.PHONY: pypi-packaging
pypi-packaging:
	@echo ">> building ciscoconfparse pypi artifacts (wheel and tar.gz)"
	pip install -U setuptools>=58.0.0
	pip install -U wheel>=0.37.1
	pip install -U twine>=4.0.1
	pip install -U poetry>=1.0.0
	# Delete bogus files... see https://stackoverflow.com/a/73992288/667301
	perl -e 'unlink( grep { /^\W\d*\.*\d*/ && !-d } glob( "*" ) );'

.PHONY: pypi
pypi:
	@echo ">> uploading ciscoconfparse pypi artifacts to pypi"
	make clean
	make pypi-packaging
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
	@echo ">> git push (w/o force) ciscoconfparse local main branch to github"
	#git remote remove origin
	#git remote add origin "git@github.com:mpenning/ciscoconfparse"
	#git push git@github.com:mpenning/ciscoconfparse.git
	#git push origin +main
	$(shell python dev_tools/git_helper.py -P ciscoconfparse --push)

.PHONY: repo-push-force
repo-push-force:
	@echo ">> git push (w/ force) ciscoconfparse local main branch to github"
	#git remote remove origin
	#git remote add origin "git@github.com:mpenning/ciscoconfparse"
	#git push --force-with-lease git@github.com:mpenning/ciscoconfparse.git
	#git push --force-with-lease origin +main
	$(shell python dev_tools/git_helper.py -P ciscoconfparse --push --force)

.PHONY: repo-push-tag
repo-push-tag:
	@echo ">> git push (w/ local tag) ciscoconfparse local main branch to github"
	#make repo-push
	$(shell python dev_tools/git_helper.py -P ciscoconfparse --push --tag)

.PHONY: repo-push-tag-force
repo-push-tag-force:
	@echo ">> git push (w/ local tag and w/ force) ciscoconfparse local main branch to github"
	#make repo-push-force
	$(shell python dev_tools/git_helper.py -P ciscoconfparse --push --tag --force)

.PHONY: pylama
pylama:
	@echo ">> running pylama against ciscoconfparse"
	# Good usability info here -> https://pythonspeed.com/articles/pylint/
	pylama --ignore=E501,E301,E265,E266 ciscoconfparse/*py | less -XR

.PHONY: pylint
pylint:
	@echo ">> running pylint against ciscoconfparse"
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

.PHONY: doctest
doctest:
	# Run the doc tests
	cd sphinx-doc; make doctest

.PHONY: pip
pip:
	@echo ">> Upgrading pip to the latest version"
	pip install -U pip

.PHONY: dep
dep:
	@echo ">> installing all ciscoconfparse prod dependencies"
	make pip
	pip install -U pip>=22.2.0
	pip install -U dnspython==2.1.0 # Previously version 1.14.0
	pip install -U passlib==1.7.4
	pip install -U loguru==0.6.0
	pip install -U toml>=0.10.2

.PHONY: dev
dev:
	@echo ">> installing all prod and development ciscoconfparse dependencies"
	make dep
	pip install -U pip>=22.2.0
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


.PHONY: test
test:
	make clean
	cd tests && ./runtests.sh

.PHONY: clean
clean:
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
