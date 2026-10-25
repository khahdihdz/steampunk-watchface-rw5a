PYTHON ?= python3
VERSION ?= 0.0.0
OUT ?= dist

.PHONY: all render check package preview clean

all: package

render:
	$(PYTHON) scripts/generate.py --out $(OUT)

check: render
	$(PYTHON) scripts/validate.py --dist $(OUT)

package:
	$(PYTHON) scripts/build.py --version $(VERSION) --out $(OUT)

preview: render
	@echo "→ $(OUT)/preview/preview.png"

clean:
	rm -rf dist dist2
