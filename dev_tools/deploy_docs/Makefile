DOCHOST ?= $(shell bash -c 'read -p "documentation host: " dochost; echo $$dochost')

# Makefile color codes...
#     ref -> https://stackoverflow.com/a/5947802/667301
COL_GREEN=\033[0;32m
COL_CYAN=\033[0;36m
COL_YELLOW=\033[0;33m
COL_RED=\033[0;31m
COL_END=\033[0;0m

GOOS=linux

# Good primer on Makefile variables...
#    https://earthly.dev/blog/makefile-variables/
GO_SOURCE_FILE=deploy_docs.go
GO_BINARY_FILE=deploy_docs
GO_BIN_DIR=bin/
# Find the platform (Linux or Darwin) from 'uname -a'...
PLATFORM := $(shell perl -e '`uname -a` =~ /^(\w+).*?$$/;print("$$1");')

# .SILENT suppresses bash if-elif-else noise on the listed targets...
.SILENT: build
.DEFAULT_GOAL := build

# Ref -> https://stackoverflow.com/a/26737258/667301
build:
	@echo "$(COL_GREEN)>> compiling the project.$(COL_END)"
	# Very Important... do not skip the backup step here...
	mkdir -p $(GO_BIN_DIR)
	make backup
	-make fmt
	make dep
	make lint
	go build $(GO_SOURCE_FILE)
	strip deploy_docs
	-make lint
	############################################################################
	#
	# Replace this line with PLATFORM detection...
	#
	#go build -o bin/deploy_docs -ldflags="-s -w" $(GO_SOURCE_FILE)
	#
	############################################################################
	if [ "$(PLATFORM)" = "Linux" ]; then \
		GOARCH=amd64 GOOS=linux go build -ldflags "-s -w" -o ./$(GO_BINARY_FILE) $(GO_SOURCE_FILE); \
	elif [ "$(PLATFORM)" = "Darwin" ]; then \
		GOARCH=amd64 GOOS=darwin go build -ldflags "-s -w" -o ./$(GO_BINARY_FILE) $(GO_SOURCE_FILE); \
	else \
		echo "$(COL_RED)Unknown PLATFORM -> $(PLATFORM)$(COL_END)"; \
	fi
	#upx --ultra-brute deploy_docs
.PHONY: build

deploy:
	make build
	cd bin && ./deploy_docs
	make clean
.PHONY: deploy

fmt:
	@echo "$(COL_GREEN)>> reformatting with 'go fmt'$(COL_END)"
	go fmt $(GO_SOURCE_FILE)
.PHONY: fmt

lint:
	@echo "$(COL_GREEN)>> checking / linting the project$(COL_END)"
	revive -config revive_lint.toml .
.PHONY: lint

dep:
	@echo "$(COL_GREEN)>> getting deploy_docs dependencies$(COL_END)"
	@echo "$(COL_CYAN)>> delete old go files$(COL_END)"
	-rm go.mod
	-rm go.sum
	@echo "$(COL_CYAN)>> create a new go.mod$(COL_END)"
	go mod init github.com/mpenning/ciscoconfparse/dev_tools/deploy_docs
	go mod tidy
	go mod download
.PHONY: dep

backup:
	@echo "$(COL_GREEN)>> backup files to _bak/$(COL_END)"
	# Delete this binary because it's just huge and we can rebuild from src...
	-rm deploy_docs
	mkdir -p _bak/
	# Delete backups older than 30 days... dont crash if directory is empty
	-find ./_bak/*tgz -maxdepth 1 -type f -mtime +30 -delete
	# Create a timestamped backup tarball... exclude the _bak directory
	tar --exclude=bin --exclude=_bak -zcv -f _bak/$(shell date "+%Y%m%d_%H.%M.%S").tgz .
.PHONY: backup

clean:
	@echo "$(COL_GREEN)>> cleaning up bin/deploy_docs and other build artifacts.$(COL_END)"
	# Delete this binary because it's just huge and we can rebuild from src...
	-rm -rf bin/
.PHONY: clean
