# xcb-shim: easier native X11 protocol implementation

This program produces an intermediate form of the [XCB protocol specification][xcbproto] data
structures, to make it easier to build native bindings rather than wrapping [`libxcb`][libxcb].

The XML files [in the `xcbproto` repository][xml-files] specify most of the necessary data
types and (de)serialization procedures for working with X11, but they require a reasonable
amount of interpretation before they can be used. The [`xcbgen`][xcbgen] Python library
performs a big chunk of this interpretation.

Reimplementing this complex (and not documented outside of the python code?) logic in other
programming languages is a big obstacle to writing X11 bindings using the XCB specifications.
Therefore, I wrote [`xcb-shim.py`](xcb-shim.py) to reduce the burden on programmers trying to
do this. The program uses [`xcbgen`][xcbgen] to do all the complex stuff and emits a JSON
structure containing more the information needed to compute data type definitions and
(de)serialization code than you'd get from reading the XCB XML files alone.

## Versioning

The program and its output are versioned together in two parts: a [semver](https://semver.org/)
part, covering `xcb-shim.py` and the schema of the data structure it produces, and a part
repeating the version of `xcbproto` that it got the input XML files and the `xcbgen` library
from.

For example, version `1.2.3+1.15` means that `xcb-shim` (and the schema governing `xcb.json`)
is at version 1.2.3 and the XML files and `xcbgen` library used to produce `xcb.json` were from
`xcbproto` version 1.15.

## Licence

See [COPYING](./COPYING) for licencing information for all the files in this repository with
the exception of the build product, [`xcb.json`](xcb.json). The [`xcb.json`](xcb.json) file is
essentially a derived work of the input [XML files][xml-files], so presumably falls under the
licence(s) of the input files themselves. I'm no lawyer, and I'm not sure how the licencing
works for compilers like [`xcb-shim.py`](xcb-shim.py).

[xcbproto]: https://gitlab.freedesktop.org/xorg/proto/xcbproto
[libxcb]: https://gitlab.freedesktop.org/xorg/lib/libxcb
[xml-files]: https://gitlab.freedesktop.org/xorg/proto/xcbproto/-/tree/master/src
[xcbgen]: https://gitlab.freedesktop.org/xorg/proto/xcbproto/-/tree/master/xcbgen