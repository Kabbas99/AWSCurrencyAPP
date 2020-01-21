

install:
	python -m venv .venv
	./.venv/bin/pip install pip --upgrade
	./.venv/bin/pip install -r ./requirements.txt

test:
	export PYTHONPATH="${PYTHONPATH}:`pwd`" && ./.venv/bin/pytest .

reset:
	rm -rf ./.venv