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
structure containing more of the information needed to compute data type definitions and
(de)serialization code than you'd get from reading the XCB XML files alone.

A [Preserves Schema](https://preserves.dev/preserves-schema.html) describing the output of
`xcb-shim.py` is available in [`xcb.prs`](xcb.prs).

## Versioning

The program and its output are versioned together in two parts: a [semver](https://semver.org/)
part, covering `xcb-shim.py` and the schema of the data structure it produces, and a part
repeating the version of `xcbproto` that it got the input XML files and the `xcbgen` library
from.

For example, version `1.2.3+1.15` means that `xcb-shim` (and the schema governing `xcb.json`)
is at version 1.2.3 and the XML files and `xcbgen` library used to produce `xcb.json` were from
`xcbproto` version 1.15.

## Open questions

**`union` types.** The method for deciding which union member is active is not specified, and
varies from use to use. Fortunately, there are only a few unions in the current protocol suite.
A future improvement could be to come up with some way to specify the connection between the
discriminator and the union.

Current uses:

 - `randr:NotifyData`: member is selected by `subCode` member of the containing `Notify` event,
   whose values are specified to be drawn from enum `Notify`.

 - `xkb:Behavior`: member is selected by `type` field of each member, carefully positioned to
   be in the same place in each, with an unspecified, implicit connection to an enum
   `BehaviorType` which connects `CARD8` values to the active member of `xkb:Behavior`.

 - `xkb:Action`: like `xkb:Behavior`, but the connection to the enum `SAType` is specified by
   an `enum` attribute on the `type` fields in each member.

 - `ClientMessageData`: member is selected by `format` field, able to take on values as
   documented in the XML comments but not specified in the actual structures.

**`mask` attribute on `field` XML elements.** The `xcbgen` code doesn't yet propagate this
information to the resulting `Field` objects. This makes bitmask values appear as simple
integers. Perhaps `xcbgen` could be enhanced to capture this information. Similarly, `xcbgen`
doesn't propagate `altenum` or `altmask`.

**`string_len` in `QueryTextExtents`.** The `odd_length` field refers to `string_len`, but that
is not explicitly defined. The `xcbgen` code autogenerates *listname*`_len` if it's not
present; there's a *strong* convention that *listname*`_len` be used to describe the length of
a list!

**Use of implicit `length` in replies.** In some definitions (e.g. `keysyms_per_keycode` in
`GetKeyboardMapping` reply, `data` in `GetImage` reply, and many others in various extensions),
a list's length expression references a `length` field that is not part of the explicit list of
fields in the definition. It is a field automatically added to replies by `xcbgen` with flags
{`wire`, `auto`}, but not `visible`, so while it's not part of the interface to the structure,
it *is* supposed to be present for the internal serialization code.

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
