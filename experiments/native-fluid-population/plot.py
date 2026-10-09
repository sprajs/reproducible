"""Display restored native outputs; no model equations or numerical physics."""
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
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    refused = []
    def curve(ax, case, rows, metric, coordinate):
        xs, ys = [], []
        for row in rows:
            value = row['values'][metric]
            x = coordinate(row)
            if value['status']:
                refused.append({'case': case['id'], 'family': case['family'], 'metric': metric, 'coordinate': row['coordinate'], 'status': value['status']})
                xs.append(x); ys.append(float('nan'))
            else:
                xs.append(x); ys.append(value['value'])
        ax.plot(xs, ys, marker='.', label=json.dumps(case['parameters'], separators=(',', ':')) if case['family'] == 'chaplygin' else 'M=%g kg, b=%g m' % (case['parameters']['M_kg'], case['parameters']['b_m']))
    for case in report['cases']:
        if case['resolution'] != 'default':
            continue
        if case['family'] == 'chaplygin':
            for ax, metric in zip(axes[0], ('E', 'w_fluid', 'DC_Mpc')):
                curve(ax, case, case['rows'], metric, lambda row: row['coordinate'])
        else:
            for ax, metric in ((axes[1, 0], 'one_axis_variance_m2_s2'), (axes[1, 2], 'projected_los_variance_m2_s2')):
                curve(ax, case, case['radius_states'], metric, lambda row: row['coordinate'])
            selected = [row for row in case['rows'] if row['coordinate']['radius_over_scale'] == 1]
            curve(axes[1, 1], case, selected, 'speed_PDF_s_m', lambda row: row['coordinate']['speed_over_native_escape'])
    specs = [('Chaplygin expansion', 'a', 'E'), ('Chaplygin fluid equation of state', 'a', 'w_fluid'), ('Flat comoving distance', 'a', 'D_C [Mpc]'), ('Plummer one-axis variance', 'r/b', 'variance [m²/s²]'), ('Plummer local speed PDF at r/b=1', 'v / native escape speed', 'PDF [s/m]'), ('Plummer projected LOS variance', 'R/b', 'variance [m²/s²]')]
    for i, (ax, (title, x, y)) in enumerate(zip(axes.flat, specs)):
        ax.set(title=title, xlabel=x, ylabel=y); ax.grid(alpha=.25)
        if i < 3:
            ax.set_xscale('log')
        if i == 0:
            ax.set_yscale('log')
        if i in (3, 5):
            ax.set_yscale('log')
        if i < 3:
            handles, labels = ax.get_legend_handles_labels()
            labels = ['As=%g, alpha=%g' % (json.loads(label)['a_s'], json.loads(label)['alpha']) for label in labels]
            ax.legend(handles, labels, fontsize=6)
        else:
            ax.legend(fontsize=6)
    axes[1, 1].axvline(1, color='grey', linestyle=':', label='retained support boundary')
    fig.suptitle('Native synthetic fluid/population responses — ' + report['profile'] + '\nEmpirical numerical status: ' + manifest['numerical']['status'] + '; support boundary retained/unassessed', fontsize=12)
    fig.savefig(output / 'native-fluid-population.png', dpi=150)
    fig.savefig(output / 'native-fluid-population.svg')
    plt.close(fig)
    receipt = {'schema': 'native-fluid-population-plot/v1', 'native_sha256': hashlib.sha256(raw).hexdigest(), 'matplotlib': matplotlib.__version__, 'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'refused_displayed_values': refused, 'refusal_display': 'NaN line gap and retained support-boundary marker; raw native statuses unchanged', 'figures': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}}
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('attempt'); parser.add_argument('output')
    args = parser.parse_args(); render(args.attempt, args.output)
