
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

clean:
	rm -rf ./build ./sparkplug.egg-info ./dist
