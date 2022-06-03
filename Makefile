all: xcbproto xcb.json

xcbproto:
	git submodule update --init

xcb.json: xcb-shim.py $(wildcard xcbproto/src/*.xml)
	python3 xcb-shim.py > $@.tmp
	mv $@.tmp $@

check-schema: xcb.prb xcb.json check-schema.py
	./check-schema.py

xcb.prb: xcb.prs
	preserves-schemac .:xcb.prs > $@.tmp
	mv $@.tmp $@

clean:
	rm -f xcb.json
	rm -f xcb.prb

veryclean: clean
	rm -rf xcbproto
	rm -rf .venv

.PHONY: all clean veryclean check-schema
