run:
	docker-compose up

test:
	pytest
	rm test.db