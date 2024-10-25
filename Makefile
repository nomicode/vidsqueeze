# Mirror the function of `.envrc` so echoed commands look the same (i.e.
# `trunk` doesn't have to be prefixed with `yarn run`)
PATH:=$(shell pwd)/node_modules/.bin:$(PATH)

trunk:=node_modules/.bin/trunk
$(trunk):
	yarn install

.PHONY: check
check: $(trunk)
	trunk check

.PHONY: fmt
fmt: $(trunk)
	trunk fmt
