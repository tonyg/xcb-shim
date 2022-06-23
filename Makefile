all: xcbproto/src xorgproto/include/X11/keysymdef.h xcb.json

xcbproto/src:
	git submodule update --init

xorgproto/include/X11/keysymdef.h:
	git submodule update --init

xcb.json: xcb-shim.py $(wildcard xcbproto/src/*.xml)
	python3 xcb-shim.py > $@.tmp
	mv $@.tmp $@

check-schema-prereqs: xcb.prb xcb.json check-schema.py

check-schema: check-schema-prereqs
	./check-schema.py

1.json: xcb.json
	preserves-tool convert < xcb.json > 1.json

2.json: check-schema-prereqs
	./check-schema.py | preserves-tool convert > 2.json

compare-schematized: check-schema-prereqs 1.json 2.json
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
