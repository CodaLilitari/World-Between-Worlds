"""Original, standard-library GOB/GOO v20 reader and deterministic writer.

No copyrighted game resources are shipped with this module.
"""
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import hashlib
import struct


class ArchiveError(ValueError):
    pass


def resource_name(name):
    """Validate a virtual path before it can become a filesystem path."""
    name = name.replace('\\', '/')
    p = PurePosixPath(name)
    if (not name or p.is_absolute() or ':' in name or '\x00' in name
            or any(x in ('', '.', '..') for x in name.split('/'))):
        raise ArchiveError(f'Unsafe resource name: {name!r}')
    if any(x.endswith((' ', '.')) for x in p.parts):
        raise ArchiveError(f'Ambiguous Windows resource name: {name!r}')
    reserved = {'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(1,10)), *(f'lpt{i}' for i in range(1,10))}
    if any(x.split('.')[0].lower() in reserved for x in p.parts):
        raise ArchiveError(f'Reserved Windows resource name: {name!r}')
    if any(ord(x) < 32 or x in '<>"|?*' for x in name):
        raise ArchiveError(f'Invalid resource character: {name!r}')
    try:
        encoded = name.replace('/', '\\').encode('cp1252')
    except UnicodeEncodeError as exc:
        raise ArchiveError('Name is not representable in legacy game encoding') from exc
    if len(encoded) > 127:
        raise ArchiveError('Resource name exceeds the 127-byte limit')
    return name.lower()


@dataclass(frozen=True)
class Entry:
    name: str
    offset: int
    size: int


class Gob:
    def __init__(self, data, label='<bytes>'):
        self.data = bytes(data)
        self.label = str(label)
        if len(data) < 16:
            raise ArchiveError('Truncated GOB header')
        magic, version, table = struct.unpack_from('<4sII',data)
        if magic != b'GOB ' or version != 20:
            raise ArchiveError('Expected Jedi Knight GOB/GOO version 20')
        if table < 12 or table + 4 > len(data):
            raise ArchiveError('Invalid directory offset')
        count = struct.unpack_from('<I',data,table)[0]
        end = table + 4 + 136*count
        if end > len(data):
            raise ArchiveError('Truncated GOB directory')
        self.entries = {}
        for index in range(count):
            off,size,raw = struct.unpack_from('<II128s',data,table+4+136*index)
            if b'\x00' not in raw:
                raise ArchiveError('Unterminated GOB filename')
            name = resource_name(raw.split(b'\x00',1)[0].decode('cp1252'))
            if name in self.entries:
                raise ArchiveError(f'Duplicate resource: {name}')
            if off < 12 or off + size > len(data) or (size and off < end and off+size > table):
                raise ArchiveError(f'Invalid resource bounds: {name}')
            self.entries[name] = Entry(name,off,size)
        extents = sorted((entry.offset, entry.offset + entry.size, entry.name)
                         for entry in self.entries.values() if entry.size)
        for left, right in zip(extents, extents[1:]):
            if left[1] > right[0]:
                raise ArchiveError(f'Overlapping resource payloads: {left[2]}, {right[2]}')

    @classmethod
    def open(cls,path):
        path=Path(path)
        if path.stat().st_size > 1_000_000_000:
            raise ArchiveError('Archive exceeds the prototype one-gigabyte limit')
        return cls(path.read_bytes(),path)

    def read(self,name):
        entry=self.entries[resource_name(name)]
        return self.data[entry.offset:entry.offset+entry.size]

    @property
    def sha256(self):
        return hashlib.sha256(self.data).hexdigest()

    def inventory(self):
        return {'source':self.label,'bytes':len(self.data),'sha256':self.sha256,
                'entries':[{'path':name,'bytes':entry.size,'sha256':hashlib.sha256(self.read(name)).hexdigest()}
                           for name,entry in sorted(self.entries.items())]}


def build_gob(resources):
    normalized={}
    for name,data in resources.items():
        key=resource_name(name)
        if key in normalized:
            raise ArchiveError(f'Duplicate normalized output name: {key}')
        normalized[key]=bytes(data)
    ordered=sorted(normalized.items())
    offset=16+136*len(ordered)
    directory=[]; payload=[]
    for name,data in ordered:
        if offset + len(data) > 0xffffffff:
            raise ArchiveError('GOB exceeds 32-bit offset bounds')
        encoded=name.replace('/','\\').encode('cp1252')
        directory.append(struct.pack('<II128s',offset,len(data),encoded))
        payload.append(data)
        offset+=len(data)
    result=struct.pack('<4sIII',b'GOB ',20,12,len(ordered))+b''.join(directory)+b''.join(payload)
    check=Gob(result)
    if any(check.read(name)!=data for name,data in ordered):
        raise ArchiveError('Writer round-trip verification failed')
    return result


def write_gob(path,resources):
    """Write a new file only, then verify exact bytes by rereading it."""
    path=Path(path)
    data=build_gob(resources)
    with path.open('xb') as out:
        out.write(data)
    if path.read_bytes()!=data:
        raise ArchiveError('Post-write verification failed')
    return hashlib.sha256(data).hexdigest()
