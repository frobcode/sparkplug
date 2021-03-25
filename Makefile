.PHONY: shell build install test clean release

PYTHON_DOCKER_REPO=python:latest
PYTHON_2_DOCKER_REPO=python:2-stretch
VERSION_BUMP_TYPE?=minor
PYPI_HOST=https://upload.pypi.org/legacy/
PYPI_INDEX?=$(PYPI_HOST)/project/sparkplug

wheel:
	python setup.py sdist bdist_wheel
	ls -1 dist/*

tester: image_serv image_cons
	true

image_serv:
	docker build -f Dockerfile.server -t sparkplug_tester_rmq:latest .

image_cons: wheel
	$(eval WHEELFILE=$(shell basename `ls -1 dist/*whl | tail -1`)) # get latest wheel
	docker build -f Dockerfile.python --build-arg sparkplug_wheel=${WHEELFILE} -t sparkplug_tester:latest .

tests: tester
	# Run standard unit tests:
	docker run --name sparkplug_tests -it --network host -w /app --mount type=bind,source=${PWD},target=/app --rm sparkplug_tester:latest nosetests -v -s --logging-level=DEBUG

test-all : tests
	# Do more extensive heartbeat testing:
	# You can monitor rabbitmq in a web browser on http://127.0.0.1:15672 using guest/guest
	# Since consumer is hard to kill, we schedule the OS to take the swarm down after 5 minutes
	echo "docker-compose down -v --remove-orphans" | at now + 5 minutes
	docker-compose up

bump: tester
	# Will increment the version in all the necessary source files:
	docker run --name sparkplug_bump --network host -it -w /app --mount type=bind,source=${PWD},target=/app --rm sparkplug_tester:latest sh -f /app/bump.sh

shell:
	docker run -it -v $(shell pwd):/usr/src/code -w /usr/src/code python:latest bash

build: clean
	python setup.py sdist
	python setup.py bdist_wheel

clean:
	rm -fr build/ dist/ *.egg-info
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

install:
	pip install dist/sparkplug-*.whl

test:
	pip install -r requirements.txt -r requirements-dev.txt
	nosetests

# Utility target for checking required parameters
guard-%:
	@if [ "$($*)" = '' ]; then \
		echo "Missing required $* variable."; \
		exit 1; \
	fi;

release: guard-PYPI_USER guard-PYPI_PASS bump-version
	docker run -it \
		-v $(shell pwd):/usr/src/code \
		-w /usr/src/code \
		-e PYPI_USER=$(PYPI_USER) -e PYPI_PASS=$(PYPI_PASS) \
		-e PYPI_HOST=$(PYPI_HOST) \
		$(PYTHON_DOCKER_REPO) \
		/usr/src/code/scripts/release.sh

bump-version:
	docker run -it \
		-v $(shell pwd):/usr/src/code \
		-v ~/.gitconfig:/etc/gitconfig \
		-w /usr/src/code \
		-e VERSION_BUMP_TYPE=minor \
		$(PYTHON_DOCKER_REPO) \
		/usr/src/code/scripts/bump-version.sh
