"""Export the reviewed catalog as asset-free recipe locks, without converting maps."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import blackwing_catalog as catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = {'schema': 'blackwing.published-catalog.v1', 'version': catalog.VERSION,
             'assets_included': False,
             'recipes': [catalog.recipe_details(row['id']) for row in catalog.recipes()]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(catalog.canonical(value) + b'\n')
    print('Exported', len(value['recipes']), 'recipe locks; no game assets were read or generated.')


if __name__ == '__main__':
    main()
