"""Explicit reviewed converter families; this is not a discoverable plugin loader."""
import copy
import importlib

MODULES = ('mods_converter', 'mp_pack_converter', 'sp_converter', 'skinmods_converter')


def entries():
    result = {}
    for name in MODULES:
        module = importlib.import_module(name)
        for row in module.catalog_entries():
            key = row['id']
            if key in result:
                raise ValueError('Duplicate reviewed adapter recipe: ' + key)
            result[key] = (module, copy.deepcopy(row))
    return result


def catalog_entries():
    return [row for module, row in entries().values()]


def for_recipe(key):
    match = entries().get(key)
    return match[0] if match else None
