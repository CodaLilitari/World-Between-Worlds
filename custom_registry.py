"""Reviewed community-level metadata and safe original-package loading.

Catalog modules contain original conversion instructions and hashes, not assets.
Adding a package requires source, dependency and gameplay-script review.
"""
import hashlib
import importlib
from io import BytesIO
from pathlib import Path
import re
import zipfile

from gob import ArchiveError, Gob, resource_name


CATALOG_MODULES = ('custom_catalog', 'author_catalog', 'jhs_catalog')


def entries():
    result = {}
    tags = set()
    for module_name in CATALOG_MODULES:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as error:
            if error.name != module_name:
                raise
            continue
        for key, original in module.CATALOG.items():
            spec = dict(original)
            if key in result or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', key):
                raise ValueError('Duplicate or invalid community recipe key: ' + key)
            for required in ('tag', 'title', 'author', 'source_url', 'gob_sha256',
                             'world', 'sha256', 'scripts_sha256', 'runtime_cogs', 'environment'):
                if required not in spec:
                    raise ValueError(f'Missing {required} in community recipe {key}')
            if spec['tag'] in tags or not re.fullmatch(r'[a-z0-9_]{1,22}', spec['tag']):
                raise ValueError('Duplicate or invalid community output tag: ' + spec['tag'])
            tags.add(spec['tag'])
            for field in ('gob_sha256', 'sha256', 'scripts_sha256'):
                if not re.fullmatch(r'[0-9a-f]{64}', spec[field]):
                    raise ValueError(f'Invalid {field} in community recipe {key}')
            spec['world'] = resource_name(spec['world'])
            if not spec['world'].endswith('.jkl'):
                raise ValueError('Community source world must be a JKL')
            if spec.get('episode_type', 2) not in (2, 16):
                raise ValueError('Community RC recipes support audited deathmatch or saber-only episodes')
            for aliases in ('resource_aliases', 'template_aliases'):
                for old, new in spec.get(aliases, {}).items():
                    if old != old.lower() or new != new.lower() or '/' in new or '\\' in new:
                        raise ValueError('Community aliases must be lowercase basenames')
                    if not new.startswith('br_') or len(new.encode('cp1252')) > 31:
                        raise ValueError('Invalid namespaced community alias: ' + new)
            spec['key'] = key
            result[key] = spec
    return result


def select(value):
    value = value.strip().lower()
    matches = [key for key, spec in entries().items()
               if value in (key, spec['tag'], spec['title'].lower())]
    if len(matches) != 1:
        raise ValueError('Unknown or ambiguous community recipe: ' + value)
    return matches[0]


def open_original(path, key):
    spec = entries()[key]
    path = Path(path)
    if path.stat().st_size > 500_000_000:
        raise ArchiveError('Community package exceeds the reviewed loader size limit')
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest == spec['gob_sha256']:
        return Gob(data, str(path))
    if digest != spec.get('zip_sha256'):
        raise ArchiveError('Unreviewed original package hash for ' + spec['title'])
    with zipfile.ZipFile(BytesIO(data)) as archive:
        safe_names = []
        member = None
        for info in archive.infolist():
            name = resource_name(info.filename.rstrip('/') if info.is_dir() else info.filename)
            if not info.is_dir():
                safe_names.append(name)
                if name == resource_name(spec['gob_member']):
                    member = info
            if info.file_size > 500_000_000:
                raise ArchiveError('Oversized community ZIP member')
        if len(safe_names) != len(set(safe_names)) or member is None:
            raise ArchiveError('Duplicate ZIP member or missing reviewed GOB')
        if archive.testzip() is not None:
            raise ArchiveError('Original community ZIP failed CRC verification')
        data = archive.read(member)
    if hashlib.sha256(data).hexdigest() != spec['gob_sha256']:
        raise ArchiveError('Unexpected embedded GOB for ' + spec['title'])
    return Gob(data, str(path) + ':' + spec['gob_member'])


def output_name(key):
    return 'bridge-' + entries()[key]['tag'] + '-rc1.goo'


def apply_cog_edits(value, edits):
    """Apply exact counted source edits only; no general numeric remapping."""
    for edit in edits:
        if not edit.get('reason') or not edit.get('old') or edit.get('count', 0) < 1:
            raise ValueError('A COG edit requires source text, positive count and reason')
        count = value.count(edit['old'])
        if count != edit['count']:
            raise ValueError(f"Unexpected COG source for reviewed edit: {edit['reason']} ({count} matches)")
        value = value.replace(edit['old'], edit['new'])
    return value
