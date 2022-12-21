tests:
	python3 -m unittest 02_test_insel.py

clean:
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
