DOCHOST ?= $(shell bash -c 'read -p "documentation host: " dochost; echo $$dochost')
VERSION := $(shell grep version pyproject.toml | sed -r 's/^version\s*=\s*"(\S+?)"/\1/g')

.PHONY: pypi
pypi:
	make clean
	poetry build
	poetry publish
.PHONY: repo-push
repo-push:
	git remote remove origin
	git remote add origin "git@github.com:mpenning/ciscoconfparse" 
	git push git@github.com:mpenning/ciscoconfparse.git
	git push origin +master
.PHONY: repo-push-force
repo-push-force:
	git remote remove origin
	git remote add origin "git@github.com:mpenning/ciscoconfparse" 
	git push git@github.com:mpenning/ciscoconfparse.git
	git push --force-with-lease origin +master
.PHONY: repo-push-tag
repo-push-tag:
	git remote remove origin
	git remote add origin "git@github.com:mpenning/ciscoconfparse" 
	git tag -a ${VERSION} -m "Tag with ${VERSION}"
	git push git@github.com:mpenning/ciscoconfparse.git
	git push --tags origin +master
	git push --tags origin ${VERSION}
.PHONY: repo-push-tag-force
repo-push-tag-force:
	git remote remove origin
	git remote add origin "git@github.com:mpenning/ciscoconfparse" 
	git tag -a ${VERSION} -m "Tag with ${VERSION}"
	git push git@github.com:mpenning/ciscoconfparse.git
	git push --force-with-lease --tags origin +master
	git push --force-with-lease --tags origin ${VERSION}
.PHONY: pylint
pylint:
	# Good usability info here -> https://pythonspeed.com/articles/pylint/
	pylint --rcfile=./utils/pylintrc --ignore-patterns='^build|^dist|utils/pylintrc|README.rst|CHANGES|LICENSE|MANIFEST.in|Makefile|TODO' --output-format=colorized * | less -XR
.PHONY: tutorial
tutorial:
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
.PHONY: devpkgs
devpkgs:
	pip install --upgrade pip
	pip install --upgrade virtualenv
	pip install --upgrade virtualenvwrapper
	pip install --upgrade passlib
	pip install --upgrade loguru==0.5.3
	pip install --upgrade pss
	pip install --upgrade mock
	pip install --upgrade sphinx
	pip install --upgrade sphinx-bootstrap-theme
	pip install --upgrade rst2html5
	pip install --upgrade rst2html5-tools
	pip install --upgrade pytest==6.2.4
	pip install --upgrade mccabe
	pip install --upgrade flake8
	pip install --upgrade yapf
	pip install dnspython==1.14.0
	pip install --upgrade fabric
	pip install --upgrade ipaddr
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
.PHONY: test
test:
	# Run the unit tests
	make clean
	cd tests; ./runtests.sh
.PHONY: clean
clean:
	find ./* -name '*.pyc' -exec rm {} \;
	find ./* -name '*.so' -exec rm {} \;
	find ./* -name '*.coverage' -exec rm {} \;
	@# A minus sign prefixing the line means it ignores the return value
	-find ./* -path '*__pycache__' -exec rm -rf {} \;
	@# remove all the MockSSH keys
	-find ./* -name '*.key' -exec rm {} \;
	-rm -rf .pytest_cache/
	-rm -rf .eggs/
	-rm -rf .cache/
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
