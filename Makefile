.PHONY: clean test
clean:
	find ./* -name '*.pyc' -exec rm {} \;
test:
	cd ciscoconfparse; ./runtests.sh; cd ..
