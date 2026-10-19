# %%
"""Draws the saffml map as a standard flowchart, in a light and a dark SVG.

    python docs/map.py

The main path runs down one column: a start terminator, a box per stage, a diamond per
decision, and an end terminator. Exits leave to the right; loops back are dashed and run
in lanes beside the column, nested so that no two lines cross. Every coordinate is set
here rather than by an automatic layout, which is what keeps the column straight.
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent

# blue is the ground of the painting in assets/ (its median pixel); line is a lighter shade of it for the dark page.
# frame and ink are the neutrals for boxes, arrows and text: black on the light page, near white on the dark one
THEMES = {
    "light": dict(page="#ffffff", frame="#1f1f1f", blue="#556b9d", on_blue="#ffffff", line="#556b9d", ink="#1f1f1f", fill="#ffffff", decision="#edf0f6", muted="#5f5f5f", loop="#8a8a8a"),
    "dark": dict(page="#0d1117", frame="#e6e6e6", blue="#556b9d", on_blue="#ffffff", line="#8b9bc6", ink="#e6e6e6", fill="#0d1117", decision="#1c2333", muted="#a6a6a6", loop="#7d7d7d"),
}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# %% The main path, top to bottom: (id, shape, first line, second line)
PATH = [
    ("start", "terminator", "Request for a model", None),
    ("frame", "process", "Frame", "framing-models"),
    ("worth", "decision", "Worth a", "model?"),
    ("design", "process", "Design", "writing-design-docs"),
    ("data", "process", "Data", "building-datasets"),
    ("train", "process", "Train", "training-models"),
    ("evaluate", "process", "Evaluate", "evaluating-models"),
    ("launch", "process", "Launch", "launching-models"),
    ("monitor", "process", "Monitor", "monitoring-models"),
    ("paying", "decision", "Still", "paying?"),
    ("retire", "terminator", "Retire to the rule", None),
]

X = 280  # the column's centre
BOX_W, BOX_H = 220, 54
DEC_W, DEC_H = 168, 92
END_W, END_H = 220, 42
GAP = 30  # arrow length between shapes on the main path
TOP = 24
LANE = 112  # from a box's edge to the inner lane; the outer lane is 30 further out
EXIT_W = 160  # width of a side exit's terminator

SIZE = {"terminator": (END_W, END_H), "process": (BOX_W, BOX_H), "decision": (DEC_W, DEC_H)}

# %% Positions
cy = {}
y = TOP
for node, shape, *_ in PATH:
    h = SIZE[shape][1]
    cy[node] = y + h / 2
    y += h + GAP
HEIGHT = round(y - GAP + TOP)
LEFT_IN, LEFT_OUT = X - BOX_W / 2 - LANE, X - BOX_W / 2 - LANE - 30
RIGHT_IN, RIGHT_OUT = X + BOX_W / 2 + LANE, X + BOX_W / 2 + LANE + 30
EXIT_X = X + DEC_W / 2 + 52  # left edge of the "Ship the rule" terminator
WIDTH = round(max(RIGHT_OUT, EXIT_X + EXIT_W) + 24)


# %% Drawing
def text(x, y, s, size=15, weight="normal", fill="ink", family=SANS, anchor="middle"):
    return f'<text x="{x:g}" y="{y:g}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{{{fill}}}" text-anchor="{anchor}">{s}</text>'


def shape(node, kind, line1, line2, x=X, w=None):
    c = cy[node]
    w = w or SIZE[kind][0]
    h = SIZE[kind][1]
    if kind == "terminator":
        return [
            f'<rect x="{x - w / 2:g}" y="{c - h / 2:g}" width="{w:g}" height="{h:g}" rx="{h / 2:g}" fill="{{blue}}"/>',
            text(x, c + 5, line1, weight="600", fill="on_blue"),
        ]
    if kind == "process":
        return [
            f'<rect x="{x - w / 2:g}" y="{c - h / 2:g}" width="{w:g}" height="{h:g}" rx="4" fill="{{fill}}" stroke="{{frame}}" stroke-width="1.5"/>',
            text(x, c - 3, line1, weight="600"),
            text(x, c + 16, line2, size=13, fill="muted", family=MONO),
        ]
    points = f"{x:g},{c - h / 2:g} {x + w / 2:g},{c:g} {x:g},{c + h / 2:g} {x - w / 2:g},{c:g}"
    return [
        f'<polygon points="{points}" fill="{{decision}}" stroke="{{line}}" stroke-width="1.5"/>',
        text(x, c - 3, line1, size=14),
        text(x, c + 15, line2, size=14),
    ]


def arrow(points, loop=False):
    d = "M" + " L".join(f"{px:g},{py:g}" for px, py in points)
    style = 'stroke="{loop}" stroke-dasharray="5 4" marker-end="url(#loop)"' if loop else 'stroke="{frame}" marker-end="url(#main)"'
    return f'<path d="{d}" fill="none" stroke-width="1.5" {style}/>'


def bottom(node):
    return cy[node] + SIZE[dict((n, s) for n, s, *_ in PATH)[node]][1] / 2


def top(node):
    return cy[node] - SIZE[dict((n, s) for n, s, *_ in PATH)[node]][1] / 2


left, right = X - BOX_W / 2, X + BOX_W / 2
parts = []

# The main path
for (a, *_), (b, *_) in zip(PATH, PATH[1:]):
    parts.append(arrow([(X, bottom(a)), (X, top(b))]))
parts.append(text(X + 10, bottom("worth") + 20, "yes", size=13, fill="muted", anchor="start"))
parts.append(text(X + 10, bottom("paying") + 20, "no", size=13, fill="muted", anchor="start"))

# The early exit: the rule ships
parts.append(arrow([(X + DEC_W / 2, cy["worth"]), (EXIT_X, cy["worth"])]))
parts.append(text((X + DEC_W / 2 + EXIT_X) / 2, cy["worth"] - 8, "no", size=13, fill="muted"))
parts += shape("worth", "terminator", "Ship the rule", None, x=EXIT_X + EXIT_W / 2, w=EXIT_W)

# Loops back on the left: rejected design, a model that loses, a lost online test, a model still paying
loops_left = [
    ("design", "frame", LEFT_IN, 0, 8, "rejected"),
    ("evaluate", "data", LEFT_IN, 0, 0, "loses to the rule"),
    ("launch", "frame", LEFT_OUT, 0, -8, "online test lost"),
]
for src, dst, lane, dy_out, dy_in, label in loops_left:
    y0, y1 = cy[src] + dy_out, cy[dst] + dy_in
    parts.append(arrow([(left, y0), (lane, y0), (lane, y1), (left, y1)], loop=True))
    parts.append(text(left - 8, y0 - 7, label, size=12.5, fill="muted", anchor="end"))
paying_left = X - DEC_W / 2
parts.append(arrow([(paying_left, cy["paying"]), (LEFT_IN, cy["paying"]), (LEFT_IN, cy["monitor"]), (left, cy["monitor"])], loop=True))
parts.append(text(paying_left - 8, cy["paying"] - 7, "yes", size=12.5, fill="muted", anchor="end"))

# Loops back on the right, from the live model: the world moved, or an input broke
y_world, y_input = cy["monitor"] - 12, cy["monitor"] + 12
parts.append(arrow([(right, y_world), (RIGHT_IN, y_world), (RIGHT_IN, cy["train"]), (right, cy["train"])], loop=True))
parts.append(text(right + 8, y_world - 7, "world moved", size=12.5, fill="muted", anchor="start"))
parts.append(arrow([(right, y_input), (RIGHT_OUT, y_input), (RIGHT_OUT, cy["data"]), (right, cy["data"])], loop=True))
parts.append(text(right + 8, y_input + 17, "input broke", size=12.5, fill="muted", anchor="start"))

# The shapes go last, over the lines
for node, kind, line1, line2 in PATH:
    parts += shape(node, kind, line1, line2)

DEFS = """<defs>
  <marker id="main" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{frame}"/></marker>
  <marker id="loop" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{loop}"/></marker>
</defs>"""

DESC = (
    "A flowchart. It starts at a request for a model, which is framed, then a decision: is a model worth it? "
    "If not, the rule ships. If so, the work goes through design, data, train, evaluate, launch and monitor, "
    "then a decision: is the model still paying? If not, it is retired to the rule; if so, monitoring continues. "
    "Dashed arrows loop back: a rejected design and a lost online test return to framing, a model that loses to "
    "the rule returns to data, and a live model returns to training when the world moves and to data when an input breaks."
)

# %% Write both themes
for name, colors in THEMES.items():
    body = "\n".join(parts)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="img" aria-labelledby="title desc">\n'
        f'<title id="title">The saffml map</title>\n<desc id="desc">{DESC}</desc>\n'
        f'{DEFS}\n<rect width="100%" height="100%" fill="{{page}}"/>\n{body}\n</svg>\n'
    )
    (OUT / f"map-{name}.svg").write_text(svg.format(**colors))
    print(OUT / f"map-{name}.svg", WIDTH, HEIGHT)
