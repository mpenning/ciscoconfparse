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
GO_SOURCE_FILE=src/deploy_docs.go

.DEFAULT_GOAL := build

# 'make release' will perform the ultimate binary packing (sometimes
#     resulting in a 70% smaller binary!!!); however, 'upx' is really slow
release:
	make build
	upx --ultra-brute bin/deploy_docs
.PHONY: release

# Ref -> https://stackoverflow.com/a/26737258/667301
build:
	@echo "$(COL_GREEN)>> compiling the project.$(COL_END)"
	# Very Important... do not skip the backup step here...
	make backup
	make fmt
	make dep
	-make lint
	go build -o bin/deploy_docs -ldflags="-s -w" $(GO_SOURCE_FILE)
.PHONY: build

fmt:
	@echo "$(COL_GREEN)>> reformatting with 'go fmt'$(COL_END)"
	go fmt $(GO_SOURCE_FILE)
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
	staticcheck src/*go
	@echo "$(COL_CYAN)>>     running errcheck$(COL_END)"
	errcheck -verbose $(GO_SOURCE_FILE)
.PHONY: lint

dep:
	@echo "$(COL_GREEN)>> getting deploy_docs dependencies$(COL_END)"
	go mod tidy
	go get github.com/melbahja/goph@latest
	go get github.com/gleich/logoru@latest
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
