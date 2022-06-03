all: xcbproto xcb.json

xcbproto:
	git submodule update --init

xcb.json: xcb-shim.py $(wildcard xcbproto/src/*.xml)
	python3 xcb-shim.py > $@.tmp
	mv $@.tmp $@

clean:
	rm -f xcb.json

veryclean: clean
	rm -rf xcbproto

.PHONY: all clean veryclean
