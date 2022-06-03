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

for m in decoded.modules:
    for i in m.items:
        # if i.name.value[-1] == 'Connect':
        #     print(i)
        if i.type.detail.VARIANT.name == 'unknown':
            # print(i.type)
            sys.stderr.write(f'UNKNOWN {i.name}\n')
            pass

# with open('x', 'w') as f:
#     f.write(repr(decoded))
