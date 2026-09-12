"""Maintainer-only, asset-free MotS archive comparison; never mounts or converts files.

python tools/archive_audit.py --native JKMRES.GOO --episode map.goo --startup mod.goo
Repeated --episode arguments describe separate profiles; startup arguments apply to all.
--plan accepts {"archives": [{"path": "...", "role": "episode", "profile": "map-a"}]}.
Native archives are global; startup profile omitted means global. Explicit episode
profiles must be unique. No loose files, caches, discovery order, COG execution,
dependency closure, engine checksums or gameplay are certified. Exit 1 means review
findings; exit 2 means incomplete/invalid input. Only names, sizes and hashes leave
the input archives. Output files must be new and use the .json suffix.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gob import ArchiveError, Gob
from blackwing_revisions import MARKER_NAME, _decode_marker

LIMITS = {"archives": 16, "archive_bytes": 512 * 1024**2,
          "total_bytes": 2 * 1024**3, "entries_per_archive": 16384,
          "entry_bytes": 128 * 1024**2, "findings": 50000}


def inspect_archive(path, limits):
    """Read one explicitly selected archive, rejecting counts before Gob allocation."""
    path = Path(path).resolve(strict=True)
    with path.open("rb") as source:
        data = source.read(limits["archive_bytes"] + 1)
    if len(data) > limits["archive_bytes"]:
        raise ArchiveError("Archive byte limit exceeded")
    if len(data) < 16:
        raise ArchiveError("Truncated GOB header")
    magic, version, table = struct.unpack_from("<4sII", data)
    if magic != b"GOB " or version != 20 or table < 12 or table + 4 > len(data):
        raise ArchiveError("Invalid GOB header or directory offset")
    count = struct.unpack_from("<I", data, table)[0]
    if count > limits["entries_per_archive"]:
        raise ArchiveError("Archive entry count limit exceeded")
    if table + 4 + count * 136 > len(data):
        raise ArchiveError("Truncated GOB directory")
    if any(struct.unpack_from("<I", data, table + 8 + i * 136)[0]
           > limits["entry_bytes"] for i in range(count)):
        raise ArchiveError("Archive entry byte limit exceeded")
    archive = Gob(data, path)
    metadata = []
    if MARKER_NAME in archive.entries:
        try:
            _decode_marker(archive.read(MARKER_NAME))
            metadata.append(MARKER_NAME)
        except ArchiveError:
            pass  # Invalid markers receive no metadata exception.
    return {"path": str(path), "bytes": len(data), "sha256": archive.sha256,
            "recognized_metadata_paths": metadata,
            "entries": [{"path": name, "bytes": entry.size,
                         "sha256": hashlib.sha256(archive.read(name)).hexdigest()}
                        for name, entry in sorted(archive.entries.items())]}


def audit(specs, limits=None):
    limits = dict(LIMITS if limits is None else limits)
    if not isinstance(specs, list) or not 1 <= len(specs) <= limits["archives"]:
        raise ValueError("Select between 1 and the archive limit explicitly")
    normalized, episode_profiles, profiles = [], set(), set()
    for index, item in enumerate(specs):
        if not isinstance(item, dict) or set(item) - {"path", "role", "profile"}:
            raise ValueError("Each archive needs path, role and optional profile only")
        if not isinstance(item.get("role"), str) or item["role"] not in {"native", "episode", "startup"}:
            raise ValueError("Unknown archive role")
        if not isinstance(item.get("path"), str) or not item["path"]:
            raise ValueError("Archive path must be a nonempty string")
        profile = item.get("profile")
        if profile is not None and (not isinstance(profile, str) or not profile.strip()
                                    or len(profile) > 80):
            raise ValueError("Profile must be a nonempty name of at most 80 characters")
        if item["role"] == "native" and profile is not None:
            raise ValueError("Native archives apply to all profiles")
        if item["role"] == "episode":
            profile = profile or f"episode-{index + 1}"
            if profile in episode_profiles:
                raise ValueError("A profile may select only one episode archive")
            episode_profiles.add(profile)
        if profile is not None:
            profiles.add(profile)
        normalized.append({**item, "profile": profile})
    profiles = profiles or {"default"}
    report = {"schema": 1, "scope": "Explicit archive-only profiles; no mount simulation",
              "limitations": ["Full normalized virtual paths are compared, not basenames.",
                              "Engine material directory fallback and leafname caches may alias distinct paths.",
                              "Loose files, mount priority and cached startup resources are not modeled.",
                              "No dependency closure, checksum, marker payload integrity or gameplay certification."],
              "limits": limits, "profiles": sorted(profiles), "archives": [],
              "findings": [], "errors": [], "complete": True}

    def finding(value):
        if len(report["findings"]) < limits["findings"]:
            report["findings"].append(value)
        else:
            report["complete"] = False

    total = 0
    for item in normalized:
        try:
            size = Path(item["path"]).stat().st_size
            if size > limits["archive_bytes"] or total + size > limits["total_bytes"]:
                raise ArchiveError("Archive or cumulative byte limit exceeded")
            inventory = inspect_archive(item["path"], limits)
            total += inventory["bytes"]
            if total > limits["total_bytes"]:
                raise ArchiveError("Cumulative byte limit exceeded while reading")
            inventory.update(role=item["role"], profile=item["profile"],
                             active_profiles=sorted({item["profile"]} if item["profile"] else profiles))
            inventory["id"] = len(report["archives"])
            report["archives"].append(inventory)
            if item["role"] != "native" and Path(item["path"]).suffix.lower() != ".goo":
                finding({"kind": "mots_discovery_extension", "archive": inventory["id"],
                         "expected": ".goo", "actual": Path(item["path"]).suffix,
                         "note": "MotS automatic archive discovery requires .goo"})
        except (OSError, ValueError, struct.error) as exc:
            report["errors"].append({"path": item["path"], "error": str(exc)})
            report["complete"] = False
    providers = {}
    for archive in report["archives"]:
        for entry in archive["entries"]:
            providers.setdefault(entry["path"], []).append((archive, entry))
    for path, entries in sorted(providers.items()):
        for (left, le), (right, re) in itertools.combinations(entries, 2):
            same = le["sha256"] == re["sha256"]
            native_count = (left["role"] == "native") + (right["role"] == "native")
            if native_count == 2:
                if not same:
                    finding({"kind": "native_provider_difference", "path": path,
                             "archives": [left["id"], right["id"]]})
                continue
            active = sorted(set(left["active_profiles"]) & set(right["active_profiles"]))
            if path in left["recognized_metadata_paths"] and path in right["recognized_metadata_paths"]:
                kind = "wbw_tracking_metadata_difference"
                if same:
                    continue
            elif native_count:
                kind = "native_same_byte_copy" if same else "native_different_byte_override"
            elif same:
                continue
            else:
                kind = ("concurrent_output_collision" if active else "isolated_episode_overlap"
                        if left["role"] == right["role"] == "episode" else "isolated_profile_overlap")
            finding({"kind": kind, "path": path, "archives": [left["id"], right["id"]],
                     "active_profiles": active, "same_bytes": same,
                     "note": "WBW tracking records differ; payload integrity is not checked here"
                     if kind == "wbw_tracking_metadata_difference" else
                     "Archive comparison only; load precedence and caches are not modeled"})
    report["review_required"] = any(item["kind"] not in {
        "native_same_byte_copy", "isolated_episode_overlap", "isolated_profile_overlap",
        "wbw_tracking_metadata_difference"} for item in report["findings"])
    if not report["complete"] and not report["errors"]:
        report["errors"].append({"error": "Finding limit exceeded; comparison is incomplete"})
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="append", default=[], metavar="ARCHIVE")
    parser.add_argument("--episode", action="append", default=[], metavar="ARCHIVE")
    parser.add_argument("--startup", action="append", default=[], metavar="ARCHIVE")
    parser.add_argument("--plan", type=Path, help="Explicit JSON archive/profile plan")
    parser.add_argument("--output", type=Path, help="New .json output; otherwise stdout")
    args = parser.parse_args(argv)
    try:
        if args.plan:
            if args.native or args.episode or args.startup:
                raise ValueError("Use --plan or explicit archive flags, not both")
            with args.plan.open("rb") as source:
                raw = source.read(1024**2 + 1)
            if len(raw) > 1024**2:
                raise ValueError("Plan exceeds 1 MiB")
            plan = json.loads(raw)
            if not isinstance(plan, dict) or set(plan) != {"archives"}:
                raise ValueError("Plan must contain only an archives list")
            specs = plan["archives"]
        else:
            specs = [{"role": role, "path": path} for role in ("native", "episode", "startup")
                     for path in getattr(args, role)]
        report = audit(specs)
        output = json.dumps(report, indent=2) + "\n"
        if args.output:
            if args.output.suffix.lower() != ".json":
                raise ValueError("Output must be a new .json file")
            with args.output.open("x", encoding="utf-8") as target:
                target.write(output)
        else:
            print(output, end="")
        return 2 if not report["complete"] else int(report["review_required"])
    except (OSError, ValueError, RecursionError) as exc:
        print(json.dumps({"complete": False, "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
