"""Plot retained native predictions; no physical equations are evaluated here."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def render(attempt, output):
    attempt, output = Path(attempt), Path(output)
    manifest = json.loads((attempt / 'manifest.json').read_text())
    raw = (attempt / 'native.stdout').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == manifest['execution']['stdout']['sha256']
    report = json.loads(raw)
    output.mkdir(parents=True, exist_ok=False)
    specs = [('quintessence', 'w_phi', 'a', 'w_phi'), ('dgp', 'f', 'a', 'growth rate f'),
             ('nfw', 'Delta_Sigma_Msun_Mpc2', 'R [Mpc]', 'Delta Sigma [Msun/Mpc²]'),
             ('decaying-matter', 'Omega_parent', 'a', 'parent fraction'),
             ('curved-flrw', 'DM_Mpc', 'z', 'D_M [Mpc]'),
             ('hernquist', 'mass_enclosed_kg', 'r [m]', 'enclosed mass [kg]')]
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    refusals = []
    for ax, (family, metric, xlabel, ylabel) in zip(axes.flat, specs):
        for case in report['cases']:
            if case['family'] != family or case['resolution'] != 'default':
                continue
            xs, ys = [], []
            for row in case['rows']:
                item = row['values'][metric]
                if item['status']:
                    refusals.append({'case': case['id'], 'metric': metric, 'coordinate': row['coordinate'], 'status': item['status']})
                    continue
                xs.append(row['coordinate']); ys.append(item['value'])
            ax.plot(xs, ys, marker='.', label=case['id'])
        ax.set(title=family, xlabel=xlabel, ylabel=ylabel)
        ax.grid(alpha=.25)
        if family in ('nfw', 'hernquist'):
            ax.set_xscale('log'); ax.set_yscale('log')
        ax.legend(fontsize=6)
    fig.suptitle('Native SDK synthetic responses — ' + report['profile'] + '\nExecution completed; empirical refinement qualification: ' + manifest['numerical']['status'], fontsize=13)
    fig.savefig(output / 'native-responses.png', dpi=150)
    fig.savefig(output / 'native-responses.svg')
    plt.close(fig)
    receipt = {'schema': 'native-campaign-plot/v1', 'native_sha256': hashlib.sha256(raw).hexdigest(),
               'matplotlib': matplotlib.__version__, 'refusals_in_displayed_metrics': refusals,
               'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'figures': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}}
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('attempt'); p.add_argument('output')
    args = p.parse_args(); render(args.attempt, args.output)
