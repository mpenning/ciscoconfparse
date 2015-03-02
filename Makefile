PY27DEVTESTS=cd ciscoconfparse;find ./* -name 'test_*.py' -exec /opt/virtual_env/py27_test/bin/py.test -s {} \;
PY34DEVTESTS=cd ciscoconfparse;find ./* -name 'test_*.py' -exec /opt/virtual_env/py34_test/bin/py.test -s {} \;
BITBUCKETPUSH = $(shell bash -c 'read -s -p "Bitbucket Password: " pwd; hg push "https://mpenning:$$pwd@bitbucket.org/mpenning/ciscoconfparse"')
DOCHOST ?= $(shell bash -c 'read -p "documentation host: " dochost; echo $$dochost')

.PHONY: pypi
pypi:
	python setup.py sdist; python setup.py register; python setup.py sdist upload
.PHONY: repo-push
repo-push:
	cp .hgrc .hg/
	hg bookmark -f master
	-hg push ssh://hg@bitbucket.org/mpenning/ciscoconfparse
	-hg push git+ssh://git@github.com:mpenning/ciscoconfparse.git
.PHONY: parse-ios
parse-ios:
	cd ciscoconfparse; python parse_test.py 1 | less
.PHONY: parse-ios-factory
parse-ios-factory:
	cd ciscoconfparse; python parse_test.py 2 | less
.PHONY: parse-ios-banner
parse-iosxr-banner:
	cd ciscoconfparse; python parse_test.py 3 | less
.PHONY: perf-acl
perf-acl:
	cd ciscoconfparse; python performance_case.py 5 | less
.PHONY: perf-factory-intf
perf-factory-intf:
	cd ciscoconfparse; python performance_case.py 6 | less
.PHONY: devpkgs
devpkgs:
	pip install --upgrade pip
	pip install --upgrade mercurial
	pip install --upgrade hg-git
	pip install --upgrade virtualenv
	pip install --upgrade virtualenvwrapper
	pip install --upgrade pss
	pip install --upgrade mock
	pip install --upgrade sphinx
	pip install --upgrade sphinx-bootstrap-theme
	pip install --upgrade pytest==2.6.4
	pip install --upgrade mccabe
	pip install --upgrade flake8
.PHONY: flake
flake:
	flake8 --ignore E501,E226,E225,E221,E303,E302,E265,E128,E125,E124,E41,W291 --max-complexity 10 ciscoconfparse | less
.PHONY: devtest
devtest:
	@echo "[[[[ Python 2.7 tests ]]]"
	/opt/virtual_env/py27_test/bin/python ciscoconfparse/ciscoconfparse.py;
	$(PY27DEVTESTS)
	@echo "[[[[ Python 3.4 tests ]]]"
	/opt/virtual_env/py34_test/bin/python ciscoconfparse/ciscoconfparse.py
	$(PY34DEVTESTS)
	make clean
.PHONY: test
test:
	# Run the doc tests and unit tests
	cd ciscoconfparse; python ciscoconfparse.py; ./runtests.sh
.PHONY: clean
clean:
	find ./* -name '*.pyc' -exec rm {} \;
	find ./* -name '*.so' -exec rm {} \;
	@# A minus sign prefixing the line means it ignores the return value
	-find ./* -path '*__pycache__' -exec rm -rf {} \;
	-rm -rf .eggs/
	-rm -rf dist/ ciscoconfparse.egg-info/ setuptools*
.PHONY: help
help:
	@# An @ sign prevents outputting the command itself to stdout
	@echo "help                 : You figured that out ;-)"
	@echo "pypi                 : Build the project and push to pypi"
	@echo "repo-push            : Build the project and push to bitbucket / github"
	@echo "test                 : Run all doctests and unit tests"
	@echo "devpkgs              : Get all dependencies for the dev environment"
	@echo "devtest              : Run tests - Specific to Mike Pennington's build env"
	@echo "flake                : Run PyFlake code audit w/ McCabe complexity"
	@echo "clean                : Housecleaning"
	@echo "parse-ios            : Parse configs/sample_01.ios with default args"
	@echo "parse-ios-factory    : Parse configs/sample_01.ios with factory=True"
	@echo "parse-iosxr-banner   : Parse an interesting IOSXR banner"
	@echo "perf-acl             : cProfile configs/sample_05.ios (100 acls)"
	@echo "perf-factory-intf    : cProfile configs/sample_06.ios (many intfs, factory=True)"
	@echo ""
