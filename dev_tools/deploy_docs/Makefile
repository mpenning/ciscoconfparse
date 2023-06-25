DOCHOST ?= $(shell bash -c 'read -p "documentation host: " dochost; echo $$dochost')

# Makefile color codes...
#     ref -> https://stackoverflow.com/a/5947802/667301
COL_GREEN=\033[0;32m
COL_CYAN=\033[0;36m
COL_YELLOW=\033[0;33m
COL_RED=\033[0;31m
COL_END=\033[0;0m

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
	#make fmt
	make dep
	#make lint
	# See this link for -ldflags and reducing binary size...
	#     https://stackoverflow.com/a/21135705/667301
	if [ "$(PLATFORM)" = "Linux" ]; then \
		GOARCH=amd64 GOOS=linux go build -ldflags "-s -w" -o $(GO_BIN_DIR)/$(GO_BINARY_FILE) $(GO_SOURCE_FILE); \
	elif [ "$(PLATFORM)" = "Darwin" ]; then \
		GOARCH=amd64 GOOS=darwin go build -ldflags "-s -w" -o $(GO_BIN_DIR)/$(GO_BINARY_FILE) $(GO_SOURCE_FILE); \
	else \
		echo "$(COL_RED)Unknown PLATFORM -> $(PLATFORM)$(COL_END)"; \
	fi
	#strip $(GO_BIN_DIR)/$(GO_BINARY_FILE)
.PHONY: build

fmt:
	@echo "$(COL_GREEN)>> reformatting with 'go fmt'$(COL_END)"
	go fmt $(GO_SOURCE_FILE) > $(GO_SOURCE_FILE).fmt
	mv $(GO_SOURCE_FILE).fmt $(GO_SOURCE_FILE)
.PHONY: fmt

install_linters:
	@echo "$(COL_GREEN)>> installing linting tools$(COL_END)"
	go install golang.org/x/tools/go/analysis/passes/shadow/cmd/shadow@latest
	go install github.com/kisielk/errlint@latest
	go install github.com/go-critic/go-critic/cmd/gocritic@latest
	go install honnef.co/go/tools/cmd/staticlint@latest
	go install golang.org/x/tools/cmd/goimports@latest
	go install github.com/mgechev/revive
.PHONY: install_linters

lint:
	@echo "$(COL_GREEN)>> checking / linting the project$(COL_END)"
	@echo "$(COL_CYAN)>>     running go vet$(COL_END)"
	go vet ./...
	@echo "$(COL_CYAN)>>     running shadow$(COL_END)"
	shadow $(GO_SOURCE_FILE)
	@echo "$(COL_CYAN)>>     fixing suboptimal / unreferenced imports$(COL_END)"
	goimports $(GO_SOURCE_FILE) > $(GO_SOURCE_FILE).imports
	mv $(GO_SOURCE_FILE).imports $(GO_SOURCE_FILE)
	@echo "$(COL_CYAN)>>     running gocritic$(COL_END)"
	gocritic check -enableAll $(GO_SOURCE_FILE)
	@echo "$(COL_CYAN)>>     running staticcheck$(COL_END)"
	staticcheck .
	@echo "$(COL_CYAN)>>     running errcheck$(COL_END)"
	errcheck -verbose $(GO_SOURCE_FILE)
.PHONY: lint

dep:
	@echo "$(COL_GREEN)>> getting deploy_docs dependencies$(COL_END)"
	go get github.com/melbahja/goph@latest
	go get go.uber.org/zap
	go get go.uber.org/zap/zapcore
.PHONY: dep

backup:
	@echo "$(COL_GREEN)>> backup files to _bak/$(COL_END)"
	# Delete this binary because it's just huge and we can rebuild from src...
	-rm deploy_docs
	mkdir -p _bak/
	# Delete backups older than 30 days... dont crash if directory is empty
	-find ./_bak/*tgz -maxdepth 1 -type f -mtime +30 -delete
	# Create a timestamped backup tarball... exclude the _bak directory
	tar --exclude=$(GO_BIN_DIR) --exclude=_bak -zcv -f _bak/$(shell date "+%Y%m%d_%H.%M.%S").tgz .
.PHONY: backup

