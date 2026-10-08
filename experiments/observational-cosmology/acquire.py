"""Acquire the exact released DESI DR2 compression, preserving changed files."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("observational_acquisition_controller", Path(__file__).with_name("controller.py"))
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)
bao = controller.bao


def acquire(root, opener=urllib.request.urlopen):
    root = Path(root).resolve()
    identities = []
    for pin in bao.INPUTS:
        target = root / pin["relative_path"]
        url = ("https://raw.githubusercontent.com/" + bao.RELEASE["repository"] + "/"
               + bao.RELEASE["revision"] + "/" + bao.RELEASE["directory"] + "/" + target.name)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
                path = Path(temporary.name)
                try:
                    with opener(url, timeout=60) as response:
                        raw = response.read(pin["bytes"] + 1)
                    if len(raw) != pin["bytes"] or hashlib.sha256(raw).hexdigest() != pin["sha256"]:
                        raise ValueError("released download identity differs; original target not replaced")
                    temporary.write(raw)
                    temporary.flush()
                    target.hardlink_to(path)
                finally:
                    path.unlink(missing_ok=True)
        _, identity = bao.read_pinned(target, pin)
        identities.append({**identity, "url": url, "release": bao.RELEASE,
                           "redistribution": "not granted by acquisition"})
    bao.read_data(str(root))
    return {"schema": "desi-dr2-acquisition/v1", "inputs": identities}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(acquire(args.root), indent=2, sort_keys=True))
