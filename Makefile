.PHONY: test perf-acl perf-factory-intf parse-ios parse-ios-factory clean
parse-ios:
	cd ciscoconfparse; python parse_test.py 1 | less; cd ..
parse-ios-factory:
	cd ciscoconfparse; python parse_test.py 2 | less; cd ..
perf-acl:
	cd ciscoconfparse; python performance_test.py 5 | less; cd ..
perf-factory-intf:
	cd ciscoconfparse; python performance_test.py 6 | less; cd ..
test:
	# Run the doc tests and unit tests
	cd ciscoconfparse; python ciscoconfparse.py; ./runtests.sh; cd ..
clean:
	find ./* -name '*.pyc' -exec rm {} \;
	find ./* -path '*__pycache__*' -exec rm {} \;
	find ./* -name '*__pycache__' -exec rm -rf {} \;
