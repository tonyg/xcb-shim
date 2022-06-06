#!/usr/bin/env python3

import sys
import os

xcbproto_dir = sys.argv[1] if len(sys.argv) > 1 else 'xcbproto'
sys.path.append(xcbproto_dir)

# GROSS module xcbgen.xtypes imports __main__ and refers to its binding `output` directly and
# globally. So we define a quasi-parameter `current_translator`, and a global `output`
# direction which delegates to it, *before* we import any xcbgen code.

output = {}
current_translator = None
for name in ['open', 'close', 'simple', 'enum', 'struct',
             'union', 'request', 'eventstruct', 'event', 'error']:
    # Oh my god python's scoping rules again
    def delegator(name):
        return lambda *args, **kwargs: getattr(current_translator, name)(*args, **kwargs)
    output[name] = delegator(name)

from xcbgen.state import Module
from xcbgen.xtypes import *

class_name_map = {
    'BitcaseType': 'bitcase',
    'CaseType': 'case',
    'Enum': 'enum',
    'Error': 'error',
    'Event': 'event',
    'EventStruct': 'eventstruct',
    'ExprType': 'expr',
    'FileDescriptor': 'fd',
    'ListType': 'list',
    'PadType': 'pad',
    'Reply': 'reply',
    'Request': 'request',
    'SimpleType': 'simple',
    'Struct': 'struct',
    'SwitchType': 'switch',
    'Union': 'union',
}

# a decorator
def extend(cls):
    def extender(f):
        setattr(cls, f.__name__, f)
        return f
    return extender

def _base_shim_type_name(self):
    if self.name is None:
        return None
    elif type(self.name) == str:
        # work around xtypes.py bug, see https://github.com/tonyg/xcb-shim/issues/1
        return [self.name]
    else:
        return self.name

@extend(Type)
def shim_type_name(self):
    return _base_shim_type_name(self)

@extend(SimpleType)
def shim_type_name(self):
    if self.xml_type is not None:
        return [self.xml_type]
    else:
        return _base_shim_type_name(self)

@extend(Enum)
def shim_type_name(self):
    return _base_shim_type_name(self)

@extend(Type)
def digest(self):
    d = {}

    n = self.shim_type_name()
    if n is not None:
        d['name'] = n

    d['class'] = class_name_map[self.__class__.__name__]

    if self.size is not None:
        d['size'] = self.size

    if hasattr(self, 'doc') and self.doc: # some subclasses do, but we won't bother enumerating them
        d['doc'] = self.doc.digest()

    # if self.max_align_pad != 1:
    #     d['max_align_pad'] = self.max_align_pad

    if self.get_align_offset():
        d['align_offset'] = self.get_align_offset()

    # d['fixed_size'] = self.fixed_size()  ## implicit by presence/absence of fixed_total_size
    if self.get_total_size():
        d['fixed_total_size'] = self.get_total_size()

    if self.nmemb is not None and self.nmemb != 1:
        d['nmemb'] = self.nmemb

    return d

def digest_type_or_typeref(t, field_type = None):
    if t.is_pad or t.is_expr or t.is_list or t.is_switch or t.is_case_or_bitcase:
        # TODO: this hardcoded list ^ is pretty awful. We want a better way
        # to know whether using a typeref is the right thing to do
        return t.digest()
    elif t.is_simple:
        current_translator.simple_type_collector.push(t)
        return list(field_type) if field_type else t.shim_type_name()
    else:
        return list(field_type) if field_type else t.shim_type_name()

@extend(Enum)
def digest(self):
    def e(es): return [(k, int(v)) for (k, v) in es]
    return super(Enum, self).digest() | {
        'values': e(self.values),
        'bits': e(self.bits),
    }

@extend(ListType)
def digest(self):
    d = super(ListType, self).digest() | {
        'member': digest_type_or_typeref(self.member),
        'expr': self.expr.digest(),
    }
    d.pop('name', None)
    if self.nmemb is not None:
        d['nmemb'] = self.nmemb
    return d

@extend(ExprType)
def digest(self):
    return super(ExprType, self).digest() | {
        'expr': self.expr.digest(),
    }

@extend(PadType)
def digest(self):
    d = super(PadType, self).digest()
    d.pop('nmemb', None)
    return d

@extend(ComplexType)
def digest(self):
    # Python's useless metamodel means we can't make super() work, because we'd have to, in
    # `extend`, introduce a `__class__` cell to the existing digest function, and it's too late
    # by then. So we have to spell it out. Talk about attention to the irrelevant.
    d = super(ComplexType, self).digest() | {
        'fields': [f.digest() for f in self.fields],
    }
    if self.length_expr:
        d['length_expr'] = self.length_expr.digest()
    return d

@extend(SwitchType)
def digest(self):
    switch_types = set()
    for b in self.bitcases:
        if b.type.is_bitcase: switch_types.add('multiple')
        elif b.type.is_case: switch_types.add('single')
        else: raise Exception('Internal error in xcbgen: non-bitcase/case switch member')
    if len(switch_types) != 1:
        raise Exception('Internal error: conflicting switch member types or absent switch members')
    switch_type = list(switch_types)[0]
    all_field_names = set()
    d = super(SwitchType, self).digest() | {
        'switch_type': switch_type,
        'switch_expr': self.expr.digest(),
        'cases': [b.digest(all_field_names) for b in self.bitcases],
    }
    if d.pop('size', None) != 0:
        raise Exception(f'Unexpected size in switch type {self.name}')
    return d

@extend(CaseOrBitcaseType)
def digest(self):
    return super(CaseOrBitcaseType, self).digest() | {
        'matches': [e.digest() for e in self.expr],
    }

@extend(Request)
def digest(self):
    d = super(Request, self).digest() | {
        'opcode': int(self.opcode),
    }
    if self.reply:
        d['reply'] = self.reply.digest()
    return d

def digest_opcodes(opcodes):
    return [[k, int(v)] for (k, v) in opcodes.items()]

@extend(Event)
def digest(self):
    return super(Event, self).digest() | {
        'opcodes': digest_opcodes(self.opcodes),
    }

@extend(Error)
def digest(self):
    return super(Error, self).digest() | {
        'opcodes': digest_opcodes(self.opcodes),
    }

@extend(Field)
def digest(self, all_field_names=None):
    d = {}

    if self.field_name is not None:
        d['name'] = self.field_name
    elif self.type.is_case_or_bitcase:
        # When there's no field name and the type is case or bitcase,
        # xtypes.py synthesises a name (in SwitchType.resolve).
        #
        # Undo this here if we have some enumrefs we could use.
        for candidate in self.type.expr:
            if candidate.op == 'enumref':
                if candidate.lenfield_name not in all_field_names:
                    d['name'] = candidate.lenfield_name
                    self.type.name = self.type.name[:-1] + (candidate.lenfield_name,)
                    # ^ !!!
                    break

    if all_field_names is not None:
        all_field_names.add(d.get('name', None))

    flags = []
    d['flags'] = flags
    if self.visible: flags.append('visible')
    if self.wire: flags.append('wire')
    if self.auto: flags.append('auto')

    replace_type_with_fd = False
    if self.isfd:
        flags.append('isfd')
        if self.type.is_fd: # sometimes it isn't: sometimes it's a *list* of fd!
            replace_type_with_fd = True
    if replace_type_with_fd:
        d['type'] = ["fd"] # typeref, assuming some type named "fd" exists!
        # ^ undoes the special-casing of fd fields in xtypes.py
    else:
        d['type'] = digest_type_or_typeref(self.type, self.field_type)

    if self.enum:
        d['enum'] = self.enum

    return d

@extend(Expression)
def digest(self):
    d = None
    if self.op:
        d = [self.op]
        if self.lhs: d.append(self.lhs.digest())
        if self.rhs: d.append(self.rhs.digest())
        if self.op == 'enumref':
            d.append(digest_type_or_typeref(self.lenfield_type))
            d.append(self.lenfield_name)
    elif self.lenfield_name:
        d = self.lenfield_name
    elif self.nmemb:
        d = self.nmemb
    else:
        raise Exception('Unhandled case in Expression.digest')

    # if self.lenfield: d['lenfield'] = self.lenfield.digest()

    if self.bitfield:
        d = {'bitfield': d}

    return d

@extend(Doc)
def digest(self):
    d = {
        'name': list(self.name),
        'brief': self.brief,
    }
    if self.description: d['description'] = self.description
    if len(self.fields): d['fields'] = self.fields
    if len(self.errors): d['errors'] = self.errors
    if len(self.see): d['see'] = self.see
    if self.example: d['example'] = self.example
    return d

class SimpleTypeCollector:
    def __init__(self):
        self.types = []
        self.seen_names = set()

    def push(self, type):
        key = '.'.join(type.shim_type_name())
        if key not in self.seen_names:
            self.seen_names.add(key)
            self.types.append(type.digest())

class Translator:
    def __init__(self, xmlfilename, simple_type_collector = None):
        self.xmlfilename = xmlfilename
        self.items = []
        self.simple_type_collector = simple_type_collector or SimpleTypeCollector()
        self.output = {
            'xmlfilename': self.xmlfilename,
            'items': self.items,
        }

        global current_translator
        old_translator = current_translator
        try:
            current_translator = self
            self.m = Module(self.xmlfilename, self.handlers())
            self.m.register()
            self.m.resolve()
            self.m.generate()
        finally:
            current_translator = old_translator

    def handlers(self):
        return {}

    def open(self, module):
        pass

    def close(self, module):
        pass

    def push_item(self, name, t):
        self.items.append({ 'definition': name, 'type': t.digest() })

    def request(self, t, name):
        self.push_item(name, t)

    def enum(self, t, name):
        self.push_item(name, t)

    def simple(self, t, name):
        self.push_item(name, t)

    def error(self, t, name):
        self.push_item(name, t)

    def event(self, t, name):
        self.push_item(name, t)

    def struct(self, t, name):
        self.push_item(name, t)

    def union(self, t, name):
        self.push_item(name, t)

    def eventstruct(self, t, name):
        self.push_item(name, t)

if __name__ == '__main__':
    import glob

    simple_type_collector = SimpleTypeCollector()
    modules = [Translator(f, simple_type_collector=simple_type_collector).output
               for f in glob.glob(os.path.join(xcbproto_dir, 'src/*.xml'))]
    output = {
        'modules': modules,
        'simple_types': simple_type_collector.types,
    }

    import json
    json.dump(output, fp=sys.stdout)
    # import json
    # json.dump(output, fp=sys.stdout, indent=2)
    # from pprint import pprint
    # pprint(output, sort_dicts=False, width=100, compact=True)
