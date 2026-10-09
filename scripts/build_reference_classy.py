"""Build a distinct serial CLASS Python owner from the frozen source archive.

Uses the existing reviewed bootstrap admission/build utilities. Never changes
the historical CLI runtime. Dependencies must already be installed in the
selected isolated interpreter; this script installs nothing.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys

import bootstrap_cosmology as bootstrap


def build(archive, root):
    root = Path(root).absolute()
    repo = Path(__file__).resolve().parents[1]
    if root.exists() or not root.is_relative_to(repo / ".work"):
        raise ValueError("fresh ignored runtime root required")
    if any(p.is_symlink() for p in root.parents):
        raise ValueError("runtime root symlink ancestor")
    archive_pin = bootstrap.pin(archive)
    if archive_pin["sha256"] != bootstrap.CLASS_ARCHIVE[1]:
        raise ValueError("frozen CLASS archive digest differs")
    dependencies = {name: importlib.metadata.version(name)
                    for name in ("numpy", "Cython", "setuptools")}
    root.mkdir(parents=True)
    receipt = {"schema": "planck-primary-classy-build/v1", "status": "failed",
               "builder": bootstrap.pin(__file__), "bootstrap": bootstrap.pin(bootstrap.__file__),
               "archive": archive_pin, "dependencies": dependencies,
               "python": bootstrap.pin(Path(sys.executable).resolve()),
               "scientific_qualification": None}
    builder = bootstrap.Builder(root)
    # The executor Python was configured with clang; only the verified local
    # GNU toolchain is present here. This is a recorded new build policy.
    builder.env.update(CC=bootstrap.executable("gcc"), CXX=bootstrap.executable("g++"))
    receipt["extension_compilers"] = [bootstrap.pin(builder.env[name]) for name in ("CC", "CXX")]
    try:
        bootstrap.extract(archive, root / "source")
        source = root / "source" / ("class_public-" + bootstrap.CLASS_REVISION)
        receipt["source_manifest"] = bootstrap.source_manifest(
            source, bootstrap.CLASS_REVISION, root / "source-manifest.json")
        builder.run([bootstrap.executable("make"), "-j1", "libclass.a"], cwd=source)
        builder.run([sys.executable, "setup.py", "build_ext", "--inplace"], cwd=source / "python")
        extensions = list((source / "python").glob("classy*.so"))
        if len(extensions) != 1:
            raise ValueError("exactly one official compiled extension required")
        extension = bootstrap.pin(extensions[0])
        libraries = bootstrap.dynamic_dependencies(extensions[0])
        receipt.update(status="completed", extension=extension, source_root=str(source),
                       dynamic_dependencies=libraries,
                       build_receipt=builder.receipt("classy", [receipt["source_manifest"]],
                                                     [extension, *libraries]))
    except BaseException as exc:
        receipt["error"] = {"kind": type(exc).__name__, "message": str(exc)[:4096]}
        receipt["commands"] = builder.commands
        raise
    finally:
        bootstrap.write(root / "runtime.json", receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    result = build(args.archive, args.root)
    print(json.dumps({"status": result["status"], "extension": result["extension"]}))
