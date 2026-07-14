#!/usr/bin/env python3
"""synthesize_sdd.py - build off/on .sdd fixture pairs for the #16 A/B harness.

Generates two sibling fixtures with BYTE-IDENTICAL .sdd bodies and config:
  fixtures/sdd-{scale}-off   marketplace plugin (no index support)
  fixtures/sdd-{scale}-on    local plugin with index support

Both fixtures have index: "on" in .sdd-config.json. The independent variable
is the plugin version (set via SDD_AB_PLUGIN_OFF/ON env vars in run_ab.sh).
The marketplace plugin ignores the index setting; the local plugin builds
the index at session-start.

  --scale small              copy repo .sdd (48 docs), .cache excluded
  --scale medium --factor 3  | --scale large --factor 8   amplify subtrees
"""

import argparse
import json
import os
import re
import shutil

REQ_ID_RE = re.compile(r"\b([A-Z]{2,3})([-_])(\d{3})((?:_\d{2})*)\b")


def repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", ".."))


def write_config(dest: str) -> None:
    cfg = {
        "root": ".sdd",
        "lang": "en",
        "directories": {"requirement": "requirement", "specification": "specification", "task": "task"},
        "index": "on",
    }
    with open(os.path.join(dest, ".sdd-config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def build_body(repo: str, target_sdd: str) -> None:
    """Copy the repo's .sdd (excluding .cache) into target_sdd fresh."""
    if os.path.isdir(target_sdd):
        shutil.rmtree(target_sdd)
    shutil.copytree(os.path.join(repo, ".sdd"), target_sdd,
                    ignore=shutil.ignore_patterns(".cache"))


def _offset_ids(text: str, offset: int) -> str:
    def repl(m):
        return f"{m.group(1)}{m.group(2)}{int(m.group(3)) + offset:03d}{m.group(4)}"
    return REQ_ID_RE.sub(repl, text)


def amplify(target_sdd: str, factor: int) -> None:
    for area in ("requirement", "specification"):
        base = os.path.join(target_sdd, area)
        if not os.path.isdir(base):
            continue
        for k in range(1, factor):
            offset = 100 * k
            for entry in sorted(os.listdir(base)):
                srcp = os.path.join(base, entry)
                stem, ext = os.path.splitext(entry)
                if os.path.isfile(srcp):
                    dstp = os.path.join(base, f"{stem}-dup{k:02d}{ext}")
                    if os.path.exists(dstp):
                        continue
                    with open(srcp, encoding="utf-8") as f:
                        content = f.read()
                    with open(dstp, "w", encoding="utf-8") as f:
                        f.write(_offset_ids(content, offset))
                else:
                    dstp = os.path.join(base, f"{entry}-dup{k:02d}")
                    if os.path.exists(dstp):
                        continue
                    shutil.copytree(srcp, dstp)
                    for dp, _d, fs in os.walk(dstp):
                        for fn in fs:
                            if not fn.endswith(".md"):
                                continue
                            p = os.path.join(dp, fn)
                            with open(p, encoding="utf-8") as f:
                                content = f.read()
                            with open(p, "w", encoding="utf-8") as f:
                                f.write(_offset_ids(content, offset))


def count_md(sdd_dir: str) -> int:
    return sum(1 for _dp, _d, fs in os.walk(sdd_dir) for f in fs if f.endswith(".md"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthesize off/on .sdd fixture pairs.")
    parser.add_argument("--scale", choices=["small", "medium", "large"], default="small")
    parser.add_argument("--factor", type=int, default=0, help="duplication factor for medium/large")
    args = parser.parse_args()

    repo = repo_root()
    factor = args.factor or (1 if args.scale == "small" else (3 if args.scale == "medium" else 8))

    fixtures = os.path.join(repo, ".claude", "tests", "fixtures")
    off_dest = os.path.join(fixtures, f"sdd-{args.scale}-off")
    on_dest = os.path.join(fixtures, f"sdd-{args.scale}-on")
    os.makedirs(off_dest, exist_ok=True)
    os.makedirs(on_dest, exist_ok=True)

    # Build the body ONCE into the off fixture, amplify, then mirror to on so
    # the two .sdd trees are byte-identical.
    off_sdd = os.path.join(off_dest, ".sdd")
    build_body(repo, off_sdd)
    if factor > 1:
        amplify(off_sdd, factor)

    on_sdd = os.path.join(on_dest, ".sdd")
    if os.path.isdir(on_sdd):
        shutil.rmtree(on_sdd)
    shutil.copytree(off_sdd, on_sdd)

    write_config(off_dest)
    write_config(on_dest)

    print(f"[synthesize_sdd] scale={args.scale} factor={factor}")
    print(f"  off: {off_dest} ({count_md(off_sdd)} .md, marketplace plugin)")
    print(f"  on:  {on_dest} ({count_md(on_sdd)} .md, local plugin with index)")


if __name__ == "__main__":
    main()
