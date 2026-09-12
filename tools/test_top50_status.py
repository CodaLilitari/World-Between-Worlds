"""Synthetic ranking failures and current asset-free source-queue invariants."""
import copy
import json
import unittest

from top50_status import LANES, ROOT, validate_lane


class Top50StatusTests(unittest.TestCase):
    def sample(self):
        return {'ranking_url': 'https://www.massassi.net/levels/jkmp/?sortby=dl_count&num=50',
                'ranking_html_sha256': 'a' * 64,
                'entries': [dict(rank=i, massassi_id=i, title='Synthetic ' + str(i), author='Fixture',
                                 source_url=f'https://www.massassi.net/levels/files/{i}.shtml',
                                 downloads=1000-i, archive_sha256='b' * 64) for i in range(1, 51)]}

    def test_exactly_fifty_per_named_category_with_pinned_downloads(self):
        for lane in LANES:
            source = json.loads((ROOT / 'docs/top50' / (lane + '.json')).read_text(encoding='utf-8'))
            self.assertEqual(len(validate_lane(source, lane)), 50)

    def test_omitted_entry_or_duplicate_identity_is_not_a_top_fifty(self):
        data = self.sample()
        data['entries'].pop()
        with self.assertRaisesRegex(ValueError, 'exactly 50'):
            validate_lane(data, 'mp')
        data = self.sample()
        data['entries'][1]['massassi_id'] = 1
        with self.assertRaisesRegex(ValueError, 'ranked identity'):
            validate_lane(data, 'mp')

    def test_wrong_category_rank_order_or_missing_hash_is_rejected(self):
        for change in ('category', 'downloads', 'hash'):
            data = self.sample()
            if change == 'category':
                data['ranking_url'] = data['ranking_url'].replace('jkmp', 'jkctf')
            elif change == 'downloads':
                data['entries'][4]['downloads'] = 2000
            else:
                data['entries'][4]['archive_sha256'] = ''
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_lane(data, 'mp')

    def test_validation_does_not_promote_source_status_to_support(self):
        data = self.sample()
        data['entries'][0]['status'] = 'fully-compatible'
        before = copy.deepcopy(data)
        result = validate_lane(data, 'mp')
        self.assertEqual(data, before)
        self.assertNotIn('status', result[0])
        self.assertNotIn('conversion_supported', result[0])


if __name__ == '__main__':
    unittest.main()
