PYTHON ?= python3
VERSION ?= 0.0.0
OUT ?= dist

.PHONY: all render check package preview bin-project clean

all: package

render:
	$(PYTHON) scripts/generate.py --out $(OUT)

check: render
	$(PYTHON) scripts/validate.py --dist $(OUT)

package:
	$(PYTHON) scripts/build.py --version $(VERSION) --out $(OUT)

preview: render
	@echo "→ $(OUT)/preview/preview.png"

bin-project:
	$(PYTHON) scripts/binface.py --out build/fprj
	$(PYTHON) scripts/validate_fprj.py build/fprj
	@echo "→ build/fprj/face.fprj (biên dịch: xem docs/watchface-bin.md)"

clean:
	rm -rf dist dist2
