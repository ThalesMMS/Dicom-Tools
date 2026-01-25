PYTHON ?= python3
CARGO ?= cargo
CMAKE ?= cmake
BUILD_TYPE ?= Release

.PHONY: all python-install python-test rust-build rust-test cpp-configure cpp-build cpp-test interface-run clean

all: python-install rust-build cpp-build

python-install:
	cd python && $(PYTHON) -m pip install -e .

python-test:
	cd python && pytest

rust-build:
	cd rust && $(CARGO) build --release

rust-test:
	cd rust && $(CARGO) test

cpp-configure:
	mkdir -p cpp/build
	cd cpp/build && $(CMAKE) -DCMAKE_BUILD_TYPE=$(BUILD_TYPE) ..

cpp-build: cpp-configure
	cd cpp/build && $(CMAKE) --build .

cpp-test:
	cd cpp/build && ctest --output-on-failure

interface-run:
	$(PYTHON) -m interface.app

clean:
	rm -rf cpp/build rust/target python/build python/dist python/*.egg-info python/.pytest_cache interface/.pytest_cache interface/__pycache__ python/.mypy_cache python/.coverage python/.coverage.* python/htmlcov
