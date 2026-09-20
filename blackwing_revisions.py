"""Per-recipe archive revisions and a bounded, read-only installation inventory.

Revision numbers describe a recipe's output contract, independently of the app
version. The embedded marker detects accidental edits; it is not a signature or
proof of publisher identity. Neither scanning nor stamping installs any files.
"""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import os
import re
import stat
import struct

from gob import ArchiveError, Gob, build_gob, resource_name


RECIPE_REVISIONS = {
    'nar-shaddaa': 1, 'bespin': 1, 'blades-of-death': 1, 'canyon-oasis': 1,
    'valley': 1, 'battleground': 1, 'ctf-duel': 1, 'ctf-arena': 1,
    'ctf-challenge': 1, 'dojo': 1, 'caesars': 1, 'atlantis': 1,
    'death-star-arena': 1, 'naboo': 1, 'morpheus': 1,
    'duel-of-the-fates-se': 1, 'jawa-dwelling-se': 1, 'mos-espa-rpg': 1,
    'area-21': 1, 'stargate': 1, 'drazen-isle': 1, 'purgatory': 1,
    'courtyard': 1, 'shadow-caverns': 1, 'deicide': 1, 'jhs': 1,
    'ninja-kage': 1,
    'mp-blue-rain': 1, 'mp-goldeneye-facility': 1, 'mp-egypt': 1,
    'mp-castle-conflict': 1,
    'mp-4h-gun-yard': 1,
    'mod-flame-saber': 1, 'mod-16bit-sabers': 1,
    'mp-6000-block': 1, 'sp-phantom-menace-final-battle': 1,
    'mp-gladiator': 1, 'mp-the-matrix': 1,
    'mp-acid-storage-facility': 1,
    'mp-bar-and-grill': 1,
    'sp-maul-vs-qui-gon': 1,
    'mod-agent-han': 1,
    'mp-heart-of-the-forest': 1, 'mp-jedi-tower-2000': 1,
    'mp-barons-head-at-night': 1,
    'mp-dbz-tdir-tournament': 1,
    'sp-imperial-pumping-station': 1,
    'mod-anime-characters': 1,
    'sp-steal-the-bottle': 1,
    'canyon-stream': 1,
    'mod-als-star-wars': 1,
}
MARKER_NAME = 'wbw/recipe.json'
MARKER_SCHEMA = 1
MAX_MARKER_BYTES = 16_384
MAX_DIRECTORY_ENTRIES = 65_536
STATUSES = ('current', 'update_available', 'newer', 'unversioned',
            'modified', 'unrecognized', 'error')
_HASH = re.compile(r'[0-9a-f]{64}\Z')
_ID = re.compile(r'[a-z0-9][a-z0-9_-]{0,95}\Z')


class RevisionError(ArchiveError):
    """The archive's revision marker or its logical payload is invalid."""


def _positive_int(value):
    return type(value) is int and 0 < value <= 2_147_483_647


def revision(recipe_id):
    """Return the explicitly maintained revision; unknown recipes fail closed."""
    return RECIPE_REVISIONS[recipe_id]


def versioned_name(filename, number):
    """Replace a terminal legacy/revision suffix, retaining path and extension."""
    if not _positive_int(number):
        raise ValueError('Recipe revision must be a positive integer')
    text = os.fspath(filename)
    match = re.fullmatch(r'(.*[/\\])?([^/\\]+)', text)
    if not match:
        raise ValueError('Expected an archive filename')
    prefix, name = match.groups()
    stem, extension = os.path.splitext(name)
    if extension.lower() not in ('.goo', '.gob'):
        raise ValueError('Expected a .goo or .gob archive filename')
    stem = re.sub(r'(?:_wbw_v\d+|-v\d+|-rc\d+)$', '', stem, flags=re.IGNORECASE)
    if not stem:
        raise ValueError('Expected a nonempty archive basename')
    versioned_stem = f'{stem}_wbw_v{number}'
    try:
        encoded_stem = versioned_stem.encode('cp1252')
    except UnicodeEncodeError as exc:
        raise ValueError('Archive basename is not representable in MotS encoding') from exc
    if len(encoded_stem) > 31:
        raise ValueError('Versioned archive basename exceeds the engine 31-byte episode-name limit')
    return f'{prefix or ""}{versioned_stem}{extension}'


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RevisionError(f'Duplicate marker field: {key}')
        result[key] = value
    return result


def _decode_marker(raw):
    if len(raw) > MAX_MARKER_BYTES:
        raise RevisionError('Revision marker exceeds the size limit')
    try:
        marker = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_json)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise RevisionError(f'Invalid revision marker JSON: {exc}') from exc
    required = {'schema', 'id', 'revision', 'appversion', 'role', 'payload_sha256'}
    if (not isinstance(marker, dict) or not required.issubset(marker)
            or set(marker) - required - {'recipe_sha256'}):
        raise RevisionError('Invalid revision marker fields')
    if type(marker['schema']) is not int or marker['schema'] != MARKER_SCHEMA:
        raise RevisionError('Unsupported revision marker schema')
    if not isinstance(marker['id'], str) or not _ID.fullmatch(marker['id']):
        raise RevisionError('Invalid recipe identity')
    if not _positive_int(marker['revision']):
        raise RevisionError('Invalid recipe revision')
    if not isinstance(marker['role'], str) or not _ID.fullmatch(marker['role']):
        raise RevisionError('Invalid archive role')
    version = marker['appversion']
    if (not isinstance(version, str) or not 1 <= len(version) <= 80
            or any(ord(char) < 32 for char in version)):
        raise RevisionError('Invalid application version')
    for field in ('payload_sha256', 'recipe_sha256'):
        if field in marker and (not isinstance(marker[field], str)
                                or not _HASH.fullmatch(marker[field])):
            raise RevisionError(f'Invalid {field}')
    return marker


def _canonical_hash(archive):
    return hashlib.sha256(build_gob({name: archive.read(name)
                                   for name in archive.entries
                                   if name != MARKER_NAME})).hexdigest()


def stamp_archive(data, recipe_id, revision, *, tool_version, role='primary',
                  recipe_sha256=None):
    """Return deterministically stamped bytes and the exact embedded metadata.

    Restamping an already marked archive first validates its existing marker,
    so this helper cannot silently certify a damaged prior conversion.
    """
    if recipe_id not in RECIPE_REVISIONS:
        raise ValueError(f'Unknown recipe: {recipe_id}')
    archive = Gob(data)
    if MARKER_NAME in archive.entries:
        validate_archive(data)
    marker = {'schema': MARKER_SCHEMA, 'id': recipe_id, 'revision': revision,
              'appversion': tool_version, 'role': role,
              'payload_sha256': _canonical_hash(archive)}
    if recipe_sha256 is not None:
        marker['recipe_sha256'] = recipe_sha256
    encoded = json.dumps(marker, sort_keys=True, separators=(',', ':')).encode('utf-8')
    _decode_marker(encoded)
    resources = {name: archive.read(name) for name in archive.entries
                 if name != MARKER_NAME}
    resources[MARKER_NAME] = encoded
    return build_gob(resources), marker


def validate_archive(data):
    """Read a valid marker, return None if absent, or raise RevisionError.

    The payload hash covers deterministic GOB serialization of every logical
    resource except the marker, independent of archive order and padding.
    """
    try:
        archive = Gob(data)
        if MARKER_NAME not in archive.entries:
            return None
        marker = _decode_marker(archive.read(MARKER_NAME))
        if marker['payload_sha256'] != _canonical_hash(archive):
            raise RevisionError('Archive payload differs from its revision marker')
        return marker
    except (ArchiveError, UnicodeError, struct.error) as exc:
        if isinstance(exc, RevisionError):
            raise
        raise RevisionError(str(exc)) from exc


class _BudgetError(RevisionError):
    pass


class _ReadBudget:
    def __init__(self, limit):
        self.limit, self.used = limit, 0
        self.blocked = False

    def read(self, stream, size):
        if size < 0 or self.used + size > self.limit:
            self.blocked = True
            raise _BudgetError('Total scan read-byte limit reached')
        data = stream.read(size)
        self.used += len(data)
        if len(data) != size:
            raise RevisionError('Archive changed or was truncated during scan')
        return data


def _directory(stream, size, budget):
    """Validate the directory without loading retail/resource payloads."""
    header = budget.read(stream, 16)
    magic, version, table = struct.unpack_from('<4sII', header)
    if magic != b'GOB ' or version != 20:
        raise RevisionError('Expected Jedi Knight GOB/GOO version 20')
    if table < 12 or table + 4 > size:
        raise RevisionError('Invalid directory offset')
    stream.seek(table)
    count = struct.unpack('<I', budget.read(stream, 4))[0]
    if count > MAX_DIRECTORY_ENTRIES:
        raise _BudgetError('Archive directory-entry limit reached')
    end = table + 4 + 136 * count
    if end > size:
        raise RevisionError('Truncated archive directory')
    entries = {}
    for _ in range(count):
        offset, length, raw = struct.unpack('<II128s', budget.read(stream, 136))
        if b'\0' not in raw:
            raise RevisionError('Unterminated archive resource name')
        name = resource_name(raw.split(b'\0', 1)[0].decode('cp1252'))
        if name in entries:
            raise RevisionError(f'Duplicate resource: {name}')
        if (offset < 12 or offset + length > size
                or (length and offset < end and offset + length > table)):
            raise RevisionError(f'Invalid resource bounds: {name}')
        entries[name] = (offset, length)
    spans = sorted((offset, offset + length) for offset, length in entries.values()
                   if length)
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        raise RevisionError('Overlapping archive resource payloads')
    return entries


def _stream_canonical_hash(stream, entries, budget):
    ordered = sorted((name, extent) for name, extent in entries.items()
                     if name != MARKER_NAME)
    digest = hashlib.sha256()
    digest.update(struct.pack('<4sIII', b'GOB ', 20, 12, len(ordered)))
    next_offset = 16 + 136 * len(ordered)
    for name, (_, length) in ordered:
        digest.update(struct.pack('<II128s', next_offset, length,
                                  name.replace('/', '\\').encode('cp1252')))
        next_offset += length
    for _, (offset, length) in ordered:
        stream.seek(offset)
        while length:
            chunk = budget.read(stream, min(length, 1024 * 1024))
            digest.update(chunk)
            length -= len(chunk)
    return digest.hexdigest()


def _is_link(info):
    return (stat.S_ISLNK(info.st_mode)
            or bool(getattr(info, 'st_file_attributes', 0)
                    & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)))


def _same_file(before, after):
    return (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)


def scan_installation(root, recipes, *, max_depth=6, max_files=2048,
                      max_archive_bytes=512 * 1024 * 1024,
                      max_total_bytes=2 * 1024 * 1024 * 1024,
                      max_entries=16_384):
    """Inventory .goo files under an explicitly selected absolute MotS folder.

    The scan never follows symlinks or Windows reparse points, never writes,
    and reports limits/partial results. Filenames only identify unversioned
    candidates; only a valid embedded marker establishes a revision. Returned
    ``can_update`` permits selection for a fresh conversion, never overwrite.
    Legacy hashes can establish recipe identity, but not an invented revision.
    """
    path = Path(root)
    if not path.is_absolute():
        raise ValueError('Select an absolute MotS installation folder')
    if not path.exists() or not path.is_dir():
        raise ValueError('The selected MotS folder does not exist')
    # Reject a selected alias, including any reparse-point parent: lexical
    # containment would otherwise hide a traversal outside the selected tree.
    if any(_is_link(parent.lstat()) for parent in (path, *path.parents)):
        raise ValueError('The selected MotS path must not traverse links or junctions')
    path = path.resolve(strict=True)
    limits = (max_files, max_archive_bytes, max_total_bytes, max_entries)
    if (type(max_depth) is not int or max_depth < 0
            or not all(type(value) is int and value > 0 for value in limits)):
        raise ValueError('Scan limits must be positive integers; depth may be zero')
    catalog = {}
    legacy_names = defaultdict(list)
    legacy_hashes = defaultdict(list)
    for item in recipes:
        recipe_id = item['id']
        if recipe_id in catalog or not _positive_int(item['revision']):
            raise ValueError('Recipe catalog has a duplicate identity or invalid revision')
        catalog[recipe_id] = dict(item)
        for filename in item.get('legacy_filenames', []):
            legacy_names[str(filename).replace('\\', '/').rsplit('/', 1)[-1].lower()].append(recipe_id)
        for digest in item.get('legacy_sha256', []):
            if not isinstance(digest, str) or not _HASH.fullmatch(digest.lower()):
                raise ValueError('Invalid legacy archive hash')
            legacy_hashes[digest.lower()].append(recipe_id)

    response = {'root': str(path), 'results': [], 'counts': {}, 'warnings': [],
                'truncated': False}
    budget = _ReadBudget(max_total_bytes)
    seen_entries = 0
    halted = False

    def warning(message, *, incomplete=True):
        if len(response['warnings']) < 100:
            response['warnings'].append(message)
        if incomplete:
            response['truncated'] = True

    def identify(row, recipe_id):
        recipe = catalog[recipe_id]
        row.update(id=recipe_id, title=recipe.get('title', recipe_id),
                   kind=recipe.get('kind', 'unknown'), current_revision=recipe['revision'])

    def selectable(recipe_id):
        # Older scan callers may omit status. An explicit unavailable/unknown
        # status must never suggest an update that selection() will reject.
        return catalog[recipe_id].get('status', 'available') in {
            'verified', 'supported', 'ready', 'available', 'prototype'}

    def inspect(file_path, before):
        row = {'path': str(file_path), 'filename': file_path.name, 'id': None,
               'title': file_path.stem, 'kind': 'unknown', 'role': None,
               'installed_revision': None, 'current_revision': None,
               'status': 'unrecognized', 'message': 'No WBW recipe marker or recognized legacy name.',
               'can_update': False, 'duplicate': False}
        response['results'].append(row)
        marker_seen = False
        try:
            if before.st_size > max_archive_bytes:
                raise _BudgetError('Archive exceeds the per-file scan size limit')
            # Recheck aliases/containment immediately before opening the file.
            if any(_is_link(part.lstat()) for part in (file_path, *file_path.parents)
                   if part == path or path in part.parents):
                raise RevisionError('File path became a link or junction during scan')
            if not file_path.resolve(strict=True).is_relative_to(path):
                raise RevisionError('File resolves outside the selected MotS folder')
            with file_path.open('rb') as stream:
                opened = os.fstat(stream.fileno())
                if not _same_file(before, opened):
                    raise RevisionError('Archive changed before it could be scanned')
                entries = _directory(stream, opened.st_size, budget)
                if MARKER_NAME in entries:
                    marker_seen = True
                    offset, length = entries[MARKER_NAME]
                    if length > MAX_MARKER_BYTES:
                        raise RevisionError('Revision marker exceeds the size limit')
                    stream.seek(offset)
                    marker = _decode_marker(budget.read(stream, length))
                    row.update(role=marker['role'], appversion=marker['appversion'])
                    recipe_id = marker['id']
                    if recipe_id in catalog:
                        identify(row, recipe_id)
                    # Never present a forged/mismatching version as installed.
                    if _stream_canonical_hash(stream, entries, budget) != marker['payload_sha256']:
                        raise RevisionError('Archive payload differs from its revision marker')
                    row['installed_revision'] = marker['revision']
                    if recipe_id not in catalog:
                        row.update(message='Valid marker names a recipe unavailable in this WBW catalog.',
                                   marker_id=recipe_id)
                    else:
                        installed, current = marker['revision'], catalog[recipe_id]['revision']
                        if installed < current:
                            row.update(status='update_available', can_update=selectable(recipe_id),
                                       message=f'Recipe revision {current} is available; installed revision is {installed}.')
                        elif installed > current:
                            row.update(status='newer', message='Installed recipe is newer than this WBW catalog; do not downgrade.')
                        else:
                            row.update(status='current', message='Installed payload matches the current recipe revision marker.')
                        if not selectable(recipe_id):
                            row['message'] += ' This recipe is currently unavailable for conversion in this catalog.'
                else:
                    matches = set(legacy_names.get(file_path.name.lower(), []))
                    # Explicit pins optionally recover renamed legacy outputs.
                    if legacy_hashes:
                        stream.seek(0)
                        digest = hashlib.sha256()
                        remaining = opened.st_size
                        while remaining:
                            chunk = budget.read(stream, min(remaining, 1024 * 1024))
                            digest.update(chunk)
                            remaining -= len(chunk)
                        pinned = set(legacy_hashes.get(digest.hexdigest(), []))
                        if pinned:
                            matches = pinned
                    if len(matches) == 1:
                        recipe_id = next(iter(matches))
                        identify(row, recipe_id)
                        row.update(status='unversioned', can_update=selectable(recipe_id), role='primary',
                                   message=('Recognized legacy candidate without a revision marker; regenerate to establish its version.'
                                            if selectable(recipe_id) else
                                            'Recognized legacy candidate without a revision marker. This recipe is currently unavailable for conversion in this catalog.'))
                    elif len(matches) > 1:
                        row['message'] = 'Legacy identity is ambiguous; no recipe was assigned.'
                    elif re.search(r'_wbw_v\d+\.goo$', file_path.name, flags=re.IGNORECASE):
                        row['message'] = 'Filename has a revision suffix but no embedded marker; its identity and version are unverified.'
                if not _same_file(opened, os.fstat(stream.fileno())):
                    raise RevisionError('Archive changed during scan')
            if not _same_file(before, file_path.lstat()):
                raise RevisionError('Archive changed during scan')
        except _BudgetError as exc:
            row.update(status='error', installed_revision=None, can_update=False, message=str(exc))
            warning(f'{file_path.name}: {exc}')
        except (ArchiveError, OSError, ValueError, struct.error) as exc:
            row.update(status='modified' if marker_seen else 'error',
                       installed_revision=None, can_update=False, message=str(exc))
        return row

    def walk(folder, depth):
        nonlocal seen_entries, halted
        if halted:
            return
        try:
            if _is_link(folder.lstat()) or not folder.resolve(strict=True).is_relative_to(path):
                warning(f'Skipped changed directory link or junction: {folder}')
                return
            with os.scandir(folder) as listing:
                for entry in listing:
                    if halted:
                        break
                    seen_entries += 1
                    if seen_entries > max_entries:
                        warning('Directory-entry scan limit reached; inventory is incomplete.')
                        halted = True
                        break
                    candidate = Path(entry.path)
                    try:
                        info = entry.stat(follow_symlinks=False)
                        if _is_link(info):
                            warning(f'Skipped link or junction: {candidate.relative_to(path)}')
                            continue
                        if stat.S_ISDIR(info.st_mode):
                            if depth >= max_depth:
                                warning(f'Depth limit: skipped {candidate.relative_to(path)}')
                            else:
                                walk(candidate, depth + 1)
                        elif stat.S_ISREG(info.st_mode) and candidate.suffix.lower() == '.goo':
                            if len(response['results']) >= max_files:
                                warning('Archive-count scan limit reached; inventory is incomplete.')
                                halted = True
                                break
                            # Windows DirEntry.stat() can return zero device and
                            # inode fields; lstat obtains a usable file identity.
                            inspect(candidate, candidate.lstat())
                            if budget.blocked or budget.used >= budget.limit:
                                warning('Total read-byte scan limit reached; inventory is incomplete.')
                                halted = True
                    except OSError as exc:
                        warning(f'Cannot inspect {candidate.relative_to(path)}: {exc}')
        except OSError as exc:
            warning(f'Cannot enumerate {folder}: {exc}')

    walk(path, 0)
    duplicates = defaultdict(list)
    for row in response['results']:
        if row['id'] is not None:
            duplicates[(row['id'], row['role'])].append(row)
    for (recipe_id, role), rows in duplicates.items():
        if len(rows) > 1:
            for row in rows:
                row['duplicate'] = True
                row['message'] += ' Multiple archives identify this recipe and role; review possible load-order conflicts.'
            warning(f'Multiple archives for {recipe_id} ({role}); older files can shadow an updated level.',
                    incomplete=False)
    response['results'].sort(key=lambda row: row['path'].lower())
    counts = Counter(row['status'] for row in response['results'])
    response['counts'] = {name: counts[name] for name in STATUSES}
    response['counts'].update(total=len(response['results']),
                              duplicates=sum(row['duplicate'] for row in response['results']))
    response['scanned_bytes'] = budget.used
    response['limits'] = dict(max_depth=max_depth, max_files=max_files,
                              max_archive_bytes=max_archive_bytes,
                              max_total_bytes=max_total_bytes, max_entries=max_entries)
    return response
