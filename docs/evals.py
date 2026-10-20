# %%
"""Draws the README's eval scores as paired bars, in a light and a dark SVG, and renders each
to a PNG at twice the size for the README, since the GitHub mobile app shows no SVG.

    python docs/evals.py    # needs rsvg-convert (brew install librsvg)

One panel per model and one row per case: a blue bar for the score with bluML over an empty
frame for the score without, in the map's palette (docs/map.py). Grey bands split the cases
where bluML helps from those both arms already get right. The scores are the table in
evals/README.md; when the evals run again, update SCORES and run this.
"""

import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent

# The map's palette: blue is the ground of the painting in assets/; frame and ink are the neutrals
THEMES = {
    "light": dict(page="#ffffff", band="#f4f4f4", frame="#1f1f1f", blue="#556b9d", ink="#1f1f1f", fill="#ffffff", muted="#5f5f5f", grid="#dedede"),
    "dark": dict(page="#0d1117", band="#161b22", frame="#e6e6e6", blue="#556b9d", ink="#e6e6e6", fill="#0d1117", muted="#a6a6a6", grid="#2d333b"),
}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# %% The scores: the weighted share of criteria met, averaged over three runs per arm (evals/README.md, Results)
MODELS = ("Sonnet", "Opus")
SCORES = {  # case: (Sonnet with, without, Opus with, without)
    "design-doc": (1.00, 0.59, 1.00, 0.93),
    "rule-first": (0.58, 0.25, 0.83, 0.50),
    "churn-leak": (1.00, 0.92, 1.00, 1.00),
    "fraud-threshold": (1.00, 0.52, 0.96, 0.63),
    "ranker-clicks": (0.92, 0.96, 1.00, 1.00),
    "ship-it": (1.00, 0.88, 1.00, 0.96),
    "ctr-drop": (0.96, 0.58, 0.96, 0.88),
}


def score(model, case, arm):
    if case == "mean":
        return sum(score(model, c, arm) for c in SCORES) / len(SCORES)
    return SCORES[case][2 * MODELS.index(model) + (arm == "without")]


def gain(case):
    return sum(score(m, case, "with") - score(m, case, "without") for m in MODELS)


# Cases both models already get mostly right without bluML (0.88 or more) leave little room to show a gain (evals/README.md); each group is sorted by gain
ceiling = [c for c in SCORES if all(score(m, c, "without") >= 0.88 for m in MODELS)]
GROUPS = [
    ("Where it helps", sorted((c for c in SCORES if c not in ceiling), key=gain, reverse=True)),
    ("Caught without it", sorted(ceiling, key=gain, reverse=True)),
]

W = 816  # the map's width, so the two line up in the README
LABEL_X = 24
PANEL_X = (176, 500)  # left edge of each model's bars
PLOT_W = 256  # from a score of 0 to 1; the number after a bar takes the rest of the panel
RH = 30  # row height
TOP = 56  # where the first band starts
TICKS = (0, 0.25, 0.5, 0.75, 1)


# %% Drawing
def text(x, y, s, size=13, weight="normal", fill="ink", family=SANS, anchor="start", extra=""):
    return f'<text x="{x:g}" y="{y:g}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{{{fill}}}" text-anchor="{anchor}"{extra}>{s}</text>'


def bar(x0, x1, y, kind):
    style = 'fill="{blue}"' if kind == "with" else 'fill="{fill}" stroke="{frame}" stroke-width="1"'
    return f'<rect x="{x0:g}" y="{y - 5:g}" width="{x1 - x0:g}" height="10" {style}/>'


def x(i, v):
    return PANEL_X[i] + v * PLOT_W


def row(i, model, case, y, bold=False):
    out = []
    for arm, dy in (("with", -6), ("without", 6)):
        v = score(model, case, arm)
        out.append(bar(x(i, 0), x(i, v), y + dy, arm))
        out.append(text(x(i, v) + 5, y + dy + 4, f"{v:.2f}", size=11.5, weight="600" if bold else "normal", fill="ink" if arm == "with" else "muted", family=MONO))
    return out


# %% Layout
bands, y = [], TOP
for name, cases in GROUPS:
    rows = [(c, y + 30 + RH * (k + 0.5)) for k, c in enumerate(cases)]
    bands.append((name, y, y + 30 + RH * len(cases) + 8, rows))
    y = bands[-1][2] + 10
RULE = y + 2
MEAN_Y = RULE + RH / 2 + 4
TICK_Y = MEAN_Y + RH / 2 + 16
NOTE_Y = TICK_Y + 30
HEIGHT = round(NOTE_Y + 18)

parts = []
for name, y0, y1, _ in bands:
    parts.append(f'<rect x="8" y="{y0:g}" width="{W - 16:g}" height="{y1 - y0:g}" rx="6" fill="{{band}}"/>')
    parts.append(text(LABEL_X, y0 + 20, name.upper(), size=11.5, weight="600", fill="muted", extra=' letter-spacing="1.4"'))

# The grid runs through the rows only, so it never crosses a band's label
spans = [(y0 + 30, y1 - 6) for _, y0, y1, _ in bands] + [(RULE, MEAN_Y + RH / 2)]
for i in range(len(MODELS)):
    for t in TICKS:
        for a, b in spans:
            parts.append(f'<line x1="{x(i, t):g}" y1="{a:g}" x2="{x(i, t):g}" y2="{b:g}" stroke="{{{"frame" if t == 0 else "grid"}}}" stroke-width="1"/>')
        parts.append(text(x(i, t), TICK_Y, f"{t:g}", size=11.5, fill="muted", anchor="middle"))
parts.append(f'<line x1="8" y1="{RULE:g}" x2="{W - 8:g}" y2="{RULE:g}" stroke="{{frame}}" stroke-width="1"/>')

for i, model in enumerate(MODELS):
    parts.append(text(PANEL_X[i], 34, model, size=15, weight="600"))
    for _, _, _, rows in bands:
        for case, cy in rows:
            parts += row(i, model, case, cy)
    parts += row(i, model, "mean", MEAN_Y, bold=True)
for _, _, _, rows in bands:
    for case, cy in rows:
        parts.append(text(LABEL_X, cy + 4.5, case, family=MONO))
parts.append(text(LABEL_X, MEAN_Y + 5, "Mean", size=14, weight="600"))

# The legend, in the corner above the case names
for k, (arm, label) in enumerate((("with", "with bluML"), ("without", "without"))):
    parts += [bar(LABEL_X, LABEL_X + 14, 23 + 20 * k, arm), text(LABEL_X + 20, 27.5 + 20 * k, label)]
parts.append(text(LABEL_X, NOTE_Y, "Each score is the share of criteria met, averaged over three runs per arm.", size=12, fill="muted"))

DESC = "Paired bars of the eval scores with bluML and without it, for Sonnet and Opus. " + " ".join(
    f"{name}: " + "; ".join(
        f"{case}, " + ", ".join(f"{m} {score(m, case, 'without'):.2f} without and {score(m, case, 'with'):.2f} with" for m in MODELS)
        for case in cases
    ) + "."
    for name, cases in GROUPS
) + " Mean: " + ", ".join(f"{m} {score(m, 'mean', 'without'):.2f} without and {score(m, 'mean', 'with'):.2f} with" for m in MODELS) + "."

# %% Write both themes
for name, colors in THEMES.items():
    body = "\n".join(parts)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {HEIGHT}" width="{W}" height="{HEIGHT}" role="img" aria-labelledby="title desc">\n'
        f'<title id="title">Does bluML help?</title>\n<desc id="desc">{DESC}</desc>\n'
        f'<rect width="100%" height="100%" fill="{{page}}"/>\n{body}\n</svg>\n'
    )
    path = OUT / f"evals-{name}.svg"
    path.write_text(svg.format(**colors))
    subprocess.run(["rsvg-convert", "--zoom", "2", str(path), "-o", str(path.with_suffix(".png"))], check=True)
    print(path, W, HEIGHT)
