"""Validate the frozen 150-entry queue; input/catalog matches are not gameplay passes."""
from pathlib import Path
import argparse
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
LANES = {'mp': 'jkmp', 'sp': 'jksp', 'mods': 'jkmod'}
HEX = re.compile(r'[0-9a-f]{64}\Z')
PAGE = re.compile(r'https://www\.massassi\.net/levels/files/(\d+)\.shtml\Z')


def validate_lane(data, lane):
    expected = f'https://www.massassi.net/levels/{LANES[lane]}/?sortby=dl_count&num=50'
    if data.get('ranking_url') != expected:
        raise ValueError('Unexpected category/ranking query: ' + lane)
    ranking_hash = next((data[k] for k in ('ranking_html_sha256', 'ranking_page_sha256', 'ranking_sha256') if k in data), '')
    if not HEX.fullmatch(ranking_hash):
        raise ValueError('Missing ranking snapshot hash: ' + lane)
    entries = data.get('entries')
    if not isinstance(entries, list) or len(entries) != 50:
        raise ValueError('Expected exactly 50 ranked entries: ' + lane)
    result, seen, previous = [], set(), None
    for position, row in enumerate(entries, 1):
        identity = row.get('massassi_id')
        downloads = row.get('downloads', row.get('downloads_at_audit'))
        url = row.get('source_url', row.get('page_url', ''))
        match = PAGE.fullmatch(url)
        source_hash = next((row[k] for k in ('archive_sha256', 'zip_sha256', 'source_sha256') if k in row), '')
        if (type(identity) is not int or identity in seen or row.get('rank') != position
                or not match or int(match[1]) != identity):
            raise ValueError('Duplicate, missing or mismatched ranked identity: ' + lane)
        if type(downloads) is not int or downloads < 0 or previous is not None and downloads > previous:
            raise ValueError('Download ranking is not descending: ' + lane)
        if not HEX.fullmatch(source_hash):
            raise ValueError('Original download hash missing: ' + str(identity))
        if not row.get('title') or not row.get('author'):
            raise ValueError('Source attribution missing: ' + str(identity))
        result.append(dict(rank=position, massassi_id=identity, title=row['title'],
                           author=row['author'], downloads=downloads, source_url=url,
                           original_sha256=source_hash))
        seen.add(identity)
        previous = downloads
    return result


def report(root=ROOT):
    import blackwing_catalog
    import blackwing_service
    catalog = blackwing_catalog.recipes()
    result = {'schema': 'wbw.top50-status.v1', 'scope': __doc__,
              'requested_entries': 150, 'categories': {}}
    for lane in LANES:
        path = Path(root) / 'docs/top50' / (lane + '.json')
        if path.stat().st_size > 4 * 1024**2:
            raise ValueError('Oversized metadata document')
        rows = validate_lane(json.loads(path.read_text(encoding='utf-8')), lane)
        for row in rows:
            matches = []
            for recipe in catalog:
                if recipe['source_url'] != row['source_url'] or not recipe['requires_archive']:
                    continue
                if row['original_sha256'] in blackwing_service.original_hashes(recipe['id']):
                    matches.append(dict(id=recipe['id'], status=recipe['status'], revision=recipe['revision'],
                                        runtime_test=recipe.get('runtime_test')))
            row['matching_catalog_recipes'] = matches
        count = sum(bool(row['matching_catalog_recipes']) for row in rows)
        selectable = sum(any(recipe['status'] in {'verified', 'supported', 'ready', 'available', 'prototype'}
                             for recipe in row['matching_catalog_recipes']) for row in rows)
        result['categories'][lane] = {'entries': rows, 'original_hashes_recorded': len(rows),
                                      'entries_with_exact_input_recipe': count,
                                      'entries_with_selectable_recipe': selectable,
                                      'entries_without_recipe': 50 - count}
    result['original_hashes_recorded'] = sum(value['original_hashes_recorded'] for value in result['categories'].values())
    result['entries_with_exact_input_recipe'] = sum(value['entries_with_exact_input_recipe'] for value in result['categories'].values())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Optional new asset-free JSON report; does not overwrite')
    options = parser.parse_args()
    data = report()
    if options.output:
        with options.output.open('x', encoding='utf-8') as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write('\n')
    print(json.dumps({lane: {key: value for key, value in details.items() if key != 'entries'}
                      for lane, details in data['categories'].items()}, indent=2))


if __name__ == '__main__':
    main()
