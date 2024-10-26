.PHONY: init
init:
	yarn install
	$(TRUNK) init --allow-existing
	$(VALE) sync

.PHONY: upgrade
upgrade:
	yarn upgrade
	$(TRUNK) upgrade
	$(VALE) sync

.PHONY: check
check: $(trunk)
	$(TRUNK) check

.PHONY: fmt
fmt: $(trunk)
	$(TRUNK) fmt
