"""Plot saved predictions and conditional profiles; never rerun a solver."""
import argparse
import hashlib
import json
from pathlib import Path
import platform


def admitted(item, attempt, relative):
    logical = Path(relative)
    if logical.is_absolute() or ".." in logical.parts or not logical.parts:
        raise ValueError("invalid attempt-relative plotting product")
    path = attempt / logical
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError("symlink plotting product")
    raw = path.read_bytes()
    if len(raw) != item["bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
        raise ValueError("saved plotting product identity differs")
    return json.loads(raw)


def plot(attempt):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy
    attempt = Path(attempt).resolve(strict=True)
    record = json.loads((attempt / "manifest.json").read_text())
    if record["status"] != "completed":
        raise ValueError("plot requires completed observational attempt")
    output = attempt / "figures"
    output.mkdir()
    figures = []
    colors = {"lcdm": "#2856a8", "constant-w": "#b95020"}
    names = {"lcdm": "Flat ΛCDM", "constant-w": "Flat constant w = −0.9"}
    products = {model: admitted(row["products"], attempt, row["artifact_paths"]["products"])
                for model, row in record["models"].items()}
    predictions = {model: admitted(row["bao_predictions"], attempt, row["artifact_paths"]["bao_predictions"])
                   for model, row in record["models"].items()}
    def save(fig, name):
        fig.tight_layout()
        for extension in ("png", "svg"):
            path = output / (name + "." + extension)
            fig.savefig(path, dpi=140)
            raw = path.read_bytes()
            figures.append({"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    covariance = record["selection"]["covariance"]
    for model, row in record["models"].items():
        points = row["fit"]["points"]
        minimum = row["fit"]["best_evaluated"]["chi2"]
        axes[0].plot([p["H0"] for p in points], [p["chi2"] - minimum for p in points],
                     ".-", label=f"{names[model]}, H₀={row['fit']['best_evaluated']['H0']:.3f}",
                     color=colors[model])
        rows = predictions[model]["rows"]
        axes[1].plot(range(13), [r["residual"] / covariance[i][i] ** .5 for i, r in enumerate(rows)],
                     "o-", label=names[model], color=colors[model])
    axes[0].set(xlabel="H₀ [km s⁻¹ Mpc⁻¹]", ylabel="Conditional Δχ² within each model",
                title="DESI full13, all other coordinates fixed")
    axes[0].legend(fontsize=8)
    axes[1].axhline(0, color="gray", linewidth=.8)
    axes[1].set(xlabel="Released row index (final DH, DM order retained)",
                ylabel="(observed − predicted) / √Cᵢᵢ", title="Display scaling only; score uses full C")
    axes[1].legend(fontsize=8)
    save(fig, "desi-fit")
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for model, product in products.items():
        cmb = product["cmb"]
        for axis, kind in zip(axes.flat, ("tt", "ee", "te")):
            axis.plot(cmb["ell"], cmb["spectra"][kind]["Dl_uK2"], color=colors[model], label=names[model])
            axis.set(xlabel="ℓ", ylabel="Dℓ [µK²]", title=kind.upper() + " (lensed)")
        for spectrum, style in (("linear_matter", "-"), ("nonlinear_matter", "--")):
            curve = product[spectrum][0]
            axes[1, 1].loglog(curve["k_1_Mpc"], curve["P_Mpc3"], style, color=colors[model],
                              label=names[model] + (" linear" if style == "-" else " Halofit"))
    axes[1, 1].set(xlabel="k [Mpc⁻¹]", ylabel="P(k, z=0) [Mpc³]", title="Distinct linear and Halofit products")
    axes[0, 0].legend(fontsize=8)
    axes[1, 1].legend(fontsize=7)
    save(fig, "predictions")
    identity = {"schema": "observational-cosmology-figures/v1", "figures": figures,
                "manifest_sha256": hashlib.sha256((attempt / "manifest.json").read_bytes()).hexdigest(),
                "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "environment": {"python": platform.python_version(), "matplotlib": matplotlib.__version__,
                                "numpy": numpy.__version__}, "model_recomputed": False}
    with (output / "manifest.json").open("x") as stream:
        json.dump(identity, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return identity


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt", type=Path)
    print(json.dumps(plot(parser.parse_args().attempt), indent=2))
