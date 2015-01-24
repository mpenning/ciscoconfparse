.PHONY: test perf-acl perf-factory-intf clean
perf-acl:
	cd ciscoconfparse; python performance_test.py 5 | less; cd ..
perf-factory-intf:
	cd ciscoconfparse; python performance_test.py 6 | less; cd ..
test:
	# Run the doc tests and unit tests
	cd ciscoconfparse; python ciscoconfparse.py; ./runtests.sh; cd ..
clean:
	find ./* -name '*.pyc' -exec rm {} \;
