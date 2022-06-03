all: xcbproto xcb.json

xcbproto:
	git submodule update --init --remote

xcb.json: xcb-shim.py xcbproto/src/*.xml
	python3 xcb-shim.py > $@.tmp
	mv $@.tmp $@

clean:
	rm -f xcb.json

veryclean: clean
	rm -rf xcbproto

.PHONY: all clean veryclean
