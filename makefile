SHELL := bash

.PHONY: all
all: exec ## 
	
.PHONY: exec
exec: ## execute interperter
	cd src/ && python3 pybean.py


.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
