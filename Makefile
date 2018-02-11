PY27DEVTESTS=cd tests;find ./* -name 'test_*.py' -exec /opt/virtual_env/py27_test/bin/py.test -s {} \;
PY34DEVTESTS=cd tests;find ./* -name 'test_*.py' -exec /opt/virtual_env/py34_test/bin/py.test -s {} \;
BITBUCKETPUSH = $(shell bash -c 'read -s -p "Bitbucket Password: " pwd; hg push "https://mpenning:$$pwd@bitbucket.org/mpenning/ciscoconfparse"')
DOCHOST ?= $(shell bash -c 'read -p "documentation host: " dochost; echo $$dochost')

.PHONY: package
package:
	make clean
	python setup.py sdist
.PHONY: pypi
pypi:
	make clean
	python setup.py sdist bdist_wheel
	twine upload dist/*
.PHONY: repo-push
repo-push:
	cp .hgrc .hg/
	hg bookmark -f master
	-hg push ssh://hg@bitbucket.org/mpenning/ciscoconfparse
	-hg push git+ssh://git@github.com:mpenning/ciscoconfparse.git
.PHONY: tutorial
tutorial:
	rst2html5 --jquery --reveal-js --pretty-print-code --embed-stylesheet --embed-content --embed-images tutorial/ccp_tutorial.rst > tutorial/ccp_tutorial.html
.PHONY: parse-ios
parse-ios:
	cd tests; python parse_test.py 1 | less
.PHONY: parse-ios-factory
parse-ios-factory:
	cd tests; python parse_test.py 2 | less
.PHONY: parse-ios-banner
parse-iosxr-banner:
	cd tests; python parse_test.py 3 | less
.PHONY: perf-acl
perf-acl:
	cd tests; python performance_case.py 5 | less
.PHONY: perf-factory-intf
perf-factory-intf:
	cd tests; python performance_case.py 6 | less
.PHONY: devpkgs
devpkgs:
	pip install --upgrade pip
	pip install --upgrade mercurial
	pip install --upgrade hg-git
	pip install --upgrade virtualenv
	pip install --upgrade virtualenvwrapper
	pip install --upgrade passlib
	pip install --upgrade pss
	pip install --upgrade mock
	pip install --upgrade sphinx
	pip install --upgrade sphinx-bootstrap-theme
	pip install --upgrade rst2html5
	pip install --upgrade rst2html5-tools
	pip install --upgrade pytest==2.6.4
	pip install --upgrade mccabe
	pip install --upgrade flake8
	pip install --upgrade yapf
	pip install --upgrade dnspython
	pip install --upgrade colorama
	pip install --upgrade fabric
	pip install --upgrade ipaddr
	pip install --upgrade twine
.PHONY: flake
flake:
	flake8 --ignore E501,E226,E225,E221,E303,E302,E265,E128,E125,E124,E41,W291 --max-complexity 10 ciscoconfparse | less
.PHONY: coverage
coverage:
	@echo "[[[ py.test Coverage ]]]"
	cd tests;py.test --cov-report term-missing --cov=ciscoconfparse.py -s -v
.PHONY: devtest
devtest:
	@echo "[[[ Python 2.7 tests ]]]"
	/opt/virtual_env/py27_test/bin/python ciscoconfparse/ciscoconfparse.py;
	$(PY27DEVTESTS)
	#@echo "[[[ Python 3.4 tests ]]]"
	#/opt/virtual_env/py34_test/bin/python ciscoconfparse/ciscoconfparse.py
	$(PY34DEVTESTS)
	make clean
.PHONY: test
test:
	# Run the doc tests and unit tests
	cd tests; python ../ciscoconfparse/ciscoconfparse.py; ./runtests.sh
.PHONY: clean
clean:
	find ./* -name '*.pyc' -exec rm {} \;
	find ./* -name '*.so' -exec rm {} \;
	find ./* -name '*.coverage' -exec rm {} \;
	@# A minus sign prefixing the line means it ignores the return value
	-find ./* -path '*__pycache__' -exec rm -rf {} \;
	@# remove all the MockSSH keys
	-find ./* -name '*.key' -exec rm {} \;
	-rm -rf .eggs/
	-rm -rf build/ dist/ ciscoconfparse.egg-info/ setuptools*
.PHONY: help
help:
	@# An @ sign prevents outputting the command itself to stdout
	@echo "help                 : You figured that out ;-)"
	@echo "pypi                 : Build the project and push to pypi"
	@echo "repo-push            : Build the project and push to bitbucket / github"
	@echo "test                 : Run all doctests and unit tests"
	@echo "devpkgs              : Get all dependencies for the dev environment"
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
