all: xcbproto/src xcb.json

xcbproto/src:
	git submodule update --init

xcb.json: xcb-shim.py $(wildcard xcbproto/src/*.xml)
	python3 xcb-shim.py > $@.tmp
	mv $@.tmp $@

check-schema-prereqs: xcb.prb xcb.json check-schema.py

check-schema: check-schema-prereqs
	./check-schema.py

compare-schematized: check-schema-prereqs
	preserves-tool convert < xcb.json > 1.json
	./check-schema.py | preserves-tool convert > 2.json
	colordiff -u 1.json 2.json

xcb.prb: xcb.prs
	preserves-schemac .:xcb.prs > $@.tmp
	mv $@.tmp $@

clean:
	rm -f xcb.json
	rm -f xcb.prb

veryclean: clean
	rm -rf xcbproto
	rm -rf .venv

.PHONY: all clean veryclean check-schema compare-schematized check-schema-prereqs
