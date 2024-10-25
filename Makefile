trunk := node_modules/.bin/trunk
$(trunk):
	yarn install

.PHONY: check
check: $(trunk)
	yarn run trunk check

.PHONY: fmt
fmt: $(trunk)
	yarn run trunk fmt
