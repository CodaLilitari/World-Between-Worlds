"""Synthetic-only maintainer audit tests: python -m unittest discover -s tools."""
import contextlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

from archive_audit import LIMITS, STARTUP_TABLES, audit, main
from gob import build_gob


class ArchiveAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def archive(self, name, entries, role="episode", profile=None):
        path = self.root / name
        path.write_bytes(build_gob(entries))
        result = {"path": str(path), "role": role}
        if profile is not None:
            result["profile"] = profile
        return result

    def kinds(self, result):
        return {item["kind"] for item in result["findings"]}

    def test_episode_overlaps_are_isolated_and_hashes_retained(self):
        a = self.archive("a.goo", {"cog/shared.cog": b"synthetic A"})
        b = self.archive("b.goo", {"COG\\SHARED.COG": b"synthetic B"})
        result = audit([a, b])
        self.assertEqual(self.kinds(result), {"isolated_episode_overlap"})
        self.assertFalse(result["review_required"])
        self.assertEqual(result["findings"][0]["active_profiles"], [])
        self.assertEqual(result["archives"][0]["entries"][0]["path"], "cog/shared.cog")
        self.assertEqual(len(result["archives"][0]["sha256"]), 64)

    def test_same_basename_different_directories_is_not_a_collision(self):
        a = self.archive("a.goo", {"cog/example.cog": b"A"})
        b = self.archive("b.goo", {"misc/example.cog": b"B"}, "startup")
        self.assertEqual(audit([a, b])["findings"], [])

    def test_lone_episode_startup_tables_require_review_without_other_providers(self):
        entries = {path: b"original synthetic table" for path in STARTUP_TABLES}
        item = self.archive("episode.goo", entries, profile="menu-test")
        before = Path(item["path"]).read_bytes()
        result = audit([item])
        self.assertTrue(result["complete"])
        self.assertTrue(result["review_required"])
        self.assertEqual(self.kinds(result), {"episode_startup_table"})
        self.assertEqual({x["path"] for x in result["findings"]}, set(entries))
        self.assertEqual(len(result["startup_contracts"]), 3)
        self.assertTrue(all(x["active_profiles"] == ["menu-test"]
                            for x in result["startup_contracts"]))
        self.assertTrue(all(x["assessment"] == "episode_placement_requires_review"
                            for x in result["startup_contracts"]))
        self.assertEqual(Path(item["path"]).read_bytes(), before)

    def test_declared_startup_table_is_informational_and_hash_bound(self):
        item = self.archive("startup.goo", {"MISC\\ITEMS.DAT": b"synthetic items"}, "startup", "one")
        # The writer canonicalizes names; change the actual directory spelling
        # so this checks the auditor's reader path, not only the writer.
        raw = bytearray(Path(item["path"]).read_bytes())
        raw[24:152] = b"MISC\\ITEMS.DAT".ljust(128, b"\0")
        Path(item["path"]).write_bytes(raw)
        result = audit([item])
        self.assertEqual(result["findings"], [])
        self.assertFalse(result["review_required"])
        contract, = result["startup_contracts"]
        entry, = result["archives"][0]["entries"]
        self.assertEqual(contract["path"], "misc/items.dat")
        self.assertEqual(contract["sha256"], entry["sha256"])
        self.assertEqual(contract["bytes"], len(b"synthetic items"))
        self.assertEqual(contract["active_profiles"], ["one"])
        self.assertEqual(contract["assessment"], "declared_startup_scope")
        self.assertIn("not implicitly merged", contract["replacement_unit"])
        self.assertIn("SM Sith Lord", result["startup_contract_basis"]["credit"])

    def test_native_and_unrelated_table_basenames_do_not_get_startup_findings(self):
        native = self.archive("native.goo", {path: b"synthetic native" for path in STARTUP_TABLES}, "native")
        other = self.archive("episode.goo", {"docs/items.dat": b"notes", "static.jkl": b"notes",
                                             "misc/jkstrings.uni": b"notes"})
        result = audit([native, other])
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["startup_contracts"], [])

    def test_startup_classification_does_not_hide_whole_table_conflicts(self):
        a = self.archive("a.goo", {"ui/jkstrings.uni": b"synthetic A"}, "startup", "a")
        b = self.archive("b.goo", {"ui/jkstrings.uni": b"synthetic B"}, "startup", "b")
        isolated = audit([a, b])
        self.assertEqual(self.kinds(isolated), {"isolated_profile_overlap"})
        self.assertFalse(isolated["review_required"])
        self.assertEqual([x["active_profiles"] for x in isolated["startup_contracts"]], [["a"], ["b"]])
        concurrent = audit([a, {**b, "profile": "a"}])
        self.assertEqual(self.kinds(concurrent), {"concurrent_output_collision"})
        self.assertTrue(concurrent["review_required"])
        native = self.archive("native.goo", {"ui/jkstrings.uni": b"synthetic native"}, "native")
        self.assertIn("native_different_byte_override", self.kinds(audit([native, a])))

    def test_startup_report_is_repeatable_and_respects_finding_budget(self):
        item = self.archive("episode.goo", {"jkl/static.jkl": b"synthetic static"})
        self.assertEqual(json.dumps(audit([item]), sort_keys=True),
                         json.dumps(audit([item]), sort_keys=True))
        limited = audit([item], {**LIMITS, "findings": 0})
        self.assertFalse(limited["complete"])
        self.assertEqual(limited["findings"], [])
        self.assertEqual(len(limited["startup_contracts"]), 1)
        self.assertTrue(limited["errors"])

    def test_material_directory_fallback_remains_a_declared_limit(self):
        a = self.archive("a.goo", {"mat/example.mat": b"A"})
        b = self.archive("b.goo", {"3do/mat/example.mat": b"B"}, "startup")
        result = audit([a, b])
        self.assertEqual(result["findings"], [])
        self.assertTrue(any("fallback" in item for item in result["limitations"]))

    def test_valid_tracking_metadata_is_informational_invalid_marker_is_not(self):
        marker = {"schema": 1, "id": "fixture", "revision": 1, "appversion": "test",
                  "role": "primary", "payload_sha256": "0" * 64}
        a = self.archive("a.goo", {"wbw/recipe.json": json.dumps(marker).encode()})
        marker["role"] = "startup"
        b = self.archive("b.goo", {"wbw/recipe.json": json.dumps(marker).encode()}, "startup")
        result = audit([a, b])
        self.assertEqual(self.kinds(result), {"wbw_tracking_metadata_difference"})
        self.assertFalse(result["review_required"])
        bad = self.archive("bad.goo", {"wbw/recipe.json": b"not a valid marker"}, "startup")
        self.assertTrue(audit([a, bad])["review_required"])

    def test_global_startup_can_collide_with_each_selected_episode(self):
        specs = [self.archive("a.goo", {"cog/shared.cog": b"A"}),
                 self.archive("b.goo", {"cog/shared.cog": b"B"}),
                 self.archive("start.goo", {"cog/shared.cog": b"C"}, "startup")]
        result = audit(specs)
        active = [x for x in result["findings"] if x["kind"] == "concurrent_output_collision"]
        self.assertEqual(len(active), 2)
        self.assertTrue(all(len(x["active_profiles"]) == 1 for x in active))
        self.assertTrue(result["review_required"])

    def test_scoped_startup_stays_in_explicit_cohort(self):
        a = self.archive("a.goo", {"cog/s.cog": b"A"}, profile="a")
        b = self.archive("b.goo", {"cog/s.cog": b"B"}, profile="b")
        startup = self.archive("start.goo", {"cog/s.cog": b"C"}, "startup", "a")
        active = [x for x in audit([a, b, startup])["findings"]
                  if x["kind"] == "concurrent_output_collision"]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["active_profiles"], ["a"])

    def test_native_same_bytes_and_differing_overrides_are_distinct(self):
        native = self.archive("retail.goo", {"cog/a.cog": b"A", "cog/b.cog": b"B"}, "native")
        episode = self.archive("level.goo", {"cog/a.cog": b"A", "cog/b.cog": b"changed"})
        result = audit([native, episode])
        self.assertEqual(self.kinds(result), {"native_same_byte_copy", "native_different_byte_override"})
        self.assertTrue(result["review_required"])

    def test_native_differing_providers_require_review(self):
        a = self.archive("a.goo", {"mat/a.mat": b"A"}, "native")
        b = self.archive("b.goo", {"mat/a.mat": b"B"}, "native")
        self.assertIn("native_provider_difference", self.kinds(audit([a, b])))

    def test_wrong_mots_suffix_flagged_in_episode_and_startup(self):
        for role in ("episode", "startup"):
            item = self.archive(role + ".gob", {"cog/a.cog": b"A"}, role)
            self.assertIn("mots_discovery_extension", self.kinds(audit([item])))

    def test_duplicate_episode_profile_is_rejected(self):
        a = self.archive("a.goo", {}, profile="same")
        b = self.archive("b.goo", {}, profile="same")
        with self.assertRaises(ValueError):
            audit([a, b])
        with self.assertRaises(ValueError):
            audit([{"path": a["path"], "role": []}])

    def test_malformed_entry_bounds_and_case_collision_are_incomplete(self):
        item = self.archive("bad.goo", {"cog/a.cog": b"A", "cog/b.cog": b"B"})
        original = Path(item["path"]).read_bytes()
        data = bytearray(original)
        struct.pack_into("<I", data, 16, len(data) + 100)
        Path(item["path"]).write_bytes(data)
        self.assertFalse(audit([item])["complete"])
        data = bytearray(original)
        data[160:288] = b"COG\\A.COG".ljust(128, b"\0")
        Path(item["path"]).write_bytes(data)
        self.assertFalse(audit([item])["complete"])

    def test_explicit_count_byte_and_findings_limits(self):
        item = self.archive("a.goo", {"cog/a.cog": b"123"})
        for key, value in (("entries_per_archive", 0), ("entry_bytes", 2),
                           ("archive_bytes", 16), ("total_bytes", 16)):
            with self.subTest(key=key):
                self.assertFalse(audit([item], {**LIMITS, key: value})["complete"])
        startup = self.archive("start.goo", {"cog/a.cog": b"different"}, "startup")
        self.assertFalse(audit([item, startup], {**LIMITS, "findings": 0})["complete"])

    def test_cli_plan_is_explicit_and_output_cannot_overwrite(self):
        item = self.archive("a.goo", {"cog/a.cog": b"A"})
        plan, output = self.root / "plan.json", self.root / "report.json"
        plan.write_text(json.dumps({"archives": [item]}), encoding="utf-8")
        self.assertEqual(main(["--plan", str(plan), "--output", str(output)]), 0)
        before = output.read_bytes()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--plan", str(plan), "--output", str(output)]), 2)
        self.assertEqual(output.read_bytes(), before)
        self.assertTrue(json.loads(before)["complete"])


if __name__ == "__main__":
    unittest.main()
