"""Merge verified local platform fragments into wbw-release.json."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import blackwing_update as update


def merge(paths, out):
    result, targets, filenames = None, set(), set()
    for path in paths:
        path = Path(path)
        value = update.parse_json(path.read_bytes())
        if value.get("schema") != 1 or value.get("repository") != update.REPOSITORY:
            raise update.UpdateError("Invalid release fragment")
        update.Version(value.get("version"))
        if result is None:
            result = {"schema": 1, "repository": update.REPOSITORY, "version": value["version"], "packages": []}
        if result["version"] != value["version"]:
            raise update.UpdateError("Release fragment versions differ")
        for package in value["packages"]:
            target = update._package_fields(package)
            if target in targets or package["filename"] in filenames:
                raise update.UpdateError("Duplicate release target or filename")
            update.asset_url(value["version"], package["filename"])
            payload = (path.parent / package["filename"]).read_bytes()
            update.inspect_archive(payload, {**package, "version": value["version"]})
            targets.add(target); filenames.add(package["filename"])
            result["packages"].append(package)
    if result is None:
        raise update.UpdateError("No release fragments supplied")
    result["packages"].sort(key=lambda p: (p["kind"], p["platform"], p["arch"]))
    Path(out).write_bytes(update.json_bytes(result))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fragments", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    merge(args.fragments, args.out)
