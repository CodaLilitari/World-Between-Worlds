"""Maintainer-only, exact KWP weapon-port review. This is not a mod converter.

The pinned ZIP is read locally. Only hashes/operations are emitted by default;
--export-scripts writes incomplete, private review snippets, never a game archive.
Native player/inventory/template/UI assembly and gameplay acceptance remain open.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gob import Gob

ZIP_SHA = '517d742fe9822364a72e6be1da323ad23117c422cb163259e14f9533a3296126'
GOB_SHA = '18673aea67a633ea890d900049204818646eab5b4fa2b67d7e23ca6b3a7a9adc'
README_SHA = '2175721920d2fc8d5fa41db3742843902e1327cde665c6cb5245f8a016f60e16'
WEAPONS = {1:121, 2:122, 3:123, 4:124, 5:135, 6:126, 7:127, 8:128, 9:129, 10:131}
HELPERS = {116:141, 117:142, 118:143, 119:144, 120:145, 121:146, 122:147}
CALL = re.compile(r'\b(GetInv|SetInv|ChangeInv|IsInvAvailable|SetInvAvailable|'
                  r'IsInvActivated|SetInvActivated|GetInvFlags|SetInvFlags|'
                  r'SetCurWeapon|SelectWeapon|AssignWeapon|GetWeaponPriority)'
                  r'(\(\s*player\s*,\s*)(\d+)(\s*[,\)])', re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def anchor(value):
    return re.compile(r'(?<!\w)' + re.escape(value))


def weapon_edits(value):
    """Enumerate explicit literal descriptor edits; do not remap arbitrary ints.

    Caller must gate the exact source. Runtime weapon ordinals in network trigger
    IDs are deliberately unchanged. The native crossbow and saber differ from JK.
    """
    edits = []
    for match in CALL.finditer(value):
        number = int(match.group(3))
        if number in WEAPONS:
            old = match.group(0)
            new = match.group(1) + match.group(2) + str(WEAPONS[number]) + match.group(4)
            if not any(e['old'] == old for e in edits):
                edits.append({'old': old, 'new': new, 'count': len(anchor(old).findall(value)),
                              'reason': 'JK weapon ownership/selection maps to explicit native MotS descriptor'})
    for old, new, reason in (
        ('SelectWeapon(player, AutoSelectWeapon(player, 1))',
         'SelectWeapon(player, GetWeaponBin(AutoSelectWeapon(player, 1)))',
         'AutoSelectWeapon returns a MotS ordinal; SelectWeapon needs its descriptor for ordinals above ten'),
        ('GetCurWeapon(player) == 10', 'GetWeaponBin(GetCurWeapon(player)) == 131',
         'Saber predicate compares a descriptor without changing other ordinal consumers')):
        if old in value:
            edits.append({'old': old, 'new': new, 'count': len(anchor(old).findall(value)), 'reason': reason})
    return edits


def apply(value, edits):
    for edit in edits:
        if not edit['old'] or len(anchor(edit['old']).findall(value)) != edit['count']:
            raise ValueError('Exact KWP edit anchor/count changed')
        value = anchor(edit['old']).sub(lambda _: edit['new'], value)
    return value


def source(path):
    path = Path(path)
    if path.stat().st_size != 372161:
        raise ValueError('Requires the reviewed original KWP ZIP')
    data = path.read_bytes()
    if sha(data) != ZIP_SHA:
        raise ValueError('KWP original hash mismatch')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        files = archive.infolist()
        if len(files) != 2 or {x.filename for x in files} != {'KWP.gob', 'readme.txt'}:
            raise ValueError('KWP ZIP member set mismatch')
        if any(x.file_size > 2_000_000 for x in files):
            raise ValueError('KWP member size bound exceeded')
        gob, readme = archive.read('KWP.gob'), archive.read('readme.txt')
    if sha(gob) != GOB_SHA or sha(readme) != README_SHA:
        raise ValueError('KWP source member hash mismatch')
    return Gob(gob)


def review(archive):
    result = []
    for path in sorted(archive.entries):
        if not path.startswith('cog/weap_'):
            continue
        raw = archive.read(path)
        text = raw.decode('cp1252').replace('\r\n', '\n').replace('\r', '\n')
        edits = weapon_edits(text)
        converted = apply(text, edits).replace('\n', '\r\n').encode('cp1252')
        result.append({'path': path, 'source_sha256': sha(raw), 'review_output_sha256': sha(converted),
                       'edits': edits, 'operations': sum(x['count'] for x in edits),
                       'remaining_getcurweapon_lines': [i for i, line in enumerate(text.splitlines(), 1)
                                                        if 'GetCurWeapon(' in line]})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--export-scripts', type=Path)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    for target in (args.report, args.export_scripts):
        if target and (target.resolve().is_relative_to(project) or target.exists()):
            parser.error('Use a new private output path outside the repository')
    archive = source(args.original)
    rows = review(archive)
    report = {'schema': 1, 'status': 'incomplete-unselectable-maintainer-review',
              'original_zip_sha256': ZIP_SHA, 'original_gob_sha256': GOB_SHA,
              'original_readme_sha256': README_SHA, 'weapon_descriptors': WEAPONS,
              'proposed_helper_bins': HELPERS, 'scripts': rows,
              'limits': ['Not a runnable mod or accepted recipe.',
                         'Player, inventory, UI, template and dependency assembly remain pending.',
                         'No syntax compiler, native host, rendering or multiplayer peer result.']}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    if args.export_scripts:
        args.export_scripts.mkdir(parents=True)
        for row in rows:
            original = archive.read(row['path']).decode('cp1252').replace('\r\n', '\n')
            target = args.export_scripts / row['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(apply(original, row['edits']).replace('\n', '\r\n').encode('cp1252'))
    print(json.dumps({'scripts': len(rows), 'operations': sum(x['operations'] for x in rows),
                      'report': str(args.report), 'status': report['status']}))


if __name__ == '__main__':
    main()
