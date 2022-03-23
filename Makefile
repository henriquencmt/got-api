run:
	uvicorn src.main:app --reload

test:
	pytest
	rm test.db