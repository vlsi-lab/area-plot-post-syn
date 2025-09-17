## @section Build targets

## @subsection Default target
.PHONY: all
all: install

## @subsection Requirements
.PHONY: conda
conda:
	conda env create -f environment.yml

.PHONY: pip
pip:
	python3 -m pip install -r requirements.txt

## @subsection Build package
.PHONY: build
build:
	python3 -m pip install build
	python3 -m build

## @subsection Install package
.PHONY: install
install: build
	python3 -m pip install dist/area_plot-0.1.1-py3-none-any.whl

.PHONY: uninstall
uninstall:
	python3 -m pip uninstall area-plot -y

## @subsection Clean
.PHONY: clean
clean:
	$(RM) -r src/area_plot.egg-info
	$(RM) -r dist
