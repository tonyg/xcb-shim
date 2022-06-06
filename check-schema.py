#!/usr/bin/env python3

import sys
import json
from pprint import pprint
from preserves.schema import load_schema_file
from preserves import stringify

s = load_schema_file('xcb.prb')
with open('xcb.json') as f:
    j = json.load(f)

decoded = s.xcb.ProtocolSpec.decode(j)

print(stringify(decoded.__preserve__(), indent=2))

# with open('x', 'w') as f:
#     f.write(repr(decoded).replace(',', '\n'))
