"""Render vector circuit schematics and verify their component/node coverage.

Values are read from the committed netlists. Expected node connections encode
the drawing layout; a topology change therefore requires an explicit update.
"""
from pathlib import Path
import hashlib
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, Polygon, Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from snspdtool.core import deck, selected

INK = "#263445"
BLUE = "#176b91"
MUTED = "#63758a"
LIGHT = "#f1f6fa"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "svg.fonttype": "none", "pdf.fonttype": 42})


def components():
    result = {}
    for name in ["bias_tee_and_load.inc", "amplifier_chain.inc"]:
        for line in (ROOT / "circuits" / name).read_text().splitlines():
            if not line.strip() or line.startswith("*"):
                continue
            fields = line.split()
            count = 4 if fields[0].startswith("E") else 3 if fields[0].startswith("X") else 2
            result[fields[0]] = {"nodes": fields[1:count + 1],
                                  "value": " ".join(fields[count + 1:]),
                                  "source": "circuits/" + name}
    return result


NET = components()
DRAWN = {}


def use(name, nodes):
    item = NET[name]
    actual = item["nodes"]
    same = actual == list(nodes)
    if name[0] in "RCL":
        same = same or actual == list(reversed(nodes))
    if not same:
        raise ValueError(f"Drawing topology mismatch: {name}: {nodes} != {actual}")
    if name in DRAWN:
        raise ValueError("Duplicate component in detailed schematic: " + name)
    DRAWN[name] = item
    return item["value"]


def display(value):
    return {"10k": "10 kΩ", "50": "50 Ω", "20": "20 Ω", "1k": "1 kΩ",
            "100k": "100 kΩ", "15.2k": "15.2 kΩ", "123.5k": "123.5 kΩ",
            "10": "10 Ω", "52.88p": "52.88 pF", "1.59p": "1.59 pF",
            "{Rextra}": "50 Ω*", "{Cshunt}": "30 pF*",
            "7.957n Rser=1": "7.957 nF", "19894n Cpar=1p": "19.894 µH"}.get(value, value)


def wire(ax, points, **kwargs):
    xy = np.array(points)
    ax.plot(xy[:, 0], xy[:, 1], color=INK, lw=1.45, solid_capstyle="round", **kwargs)


def label(ax, x, y, text, size=10, color=INK, ha="center", va="center", **kwargs):
    ax.text(x, y, text, fontsize=size, color=color, ha=ha, va=va, **kwargs)


def dot(ax, x, y, name=None, dx=0, dy=.28, ha="center"):
    ax.plot(x, y, "o", color=INK, ms=3.5)
    if name:
        label(ax, x + dx, y + dy, name, size=8.5, color=BLUE, ha=ha)


def ground(ax, x, y):
    wire(ax, [(x, y), (x, y - .14)])
    for i, width in enumerate([.42, .27, .12]):
        wire(ax, [(x - width / 2, y - .14 - .11 * i), (x + width / 2, y - .14 - .11 * i)])


def element(ax, a, b, kind, text="", label_xy=None, size=9):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    u = (b - a) / np.linalg.norm(b - a)
    v = np.array([-u[1], u[0]])
    mid = (a + b) / 2
    length = min(.86, np.linalg.norm(b - a) * .72)
    left, right = mid - u * length / 2, mid + u * length / 2
    wire(ax, [a, left])
    wire(ax, [right, b])
    if kind == "R":
        x = np.linspace(-length / 2, length / 2, 9)
        y = np.array([0, .12, -.12, .12, -.12, .12, -.12, .12, 0])
        wire(ax, [mid + u * i + v * j for i, j in zip(x, y)])
    elif kind == "C":
        gap = .075
        wire(ax, [left, mid - u * gap])
        wire(ax, [mid + u * gap, right])
        for s in [-1, 1]:
            wire(ax, [mid + u * gap * s - v * .25, mid + u * gap * s + v * .25])
    elif kind == "L":
        points = []
        for j in range(4):
            theta = np.linspace(np.pi, 0, 25)
            radius = length / 8
            center = -length / 2 + radius + j * 2 * radius
            points.extend(mid + u * (center + radius * np.cos(t)) + v * .23 * np.sin(t) for t in theta)
        wire(ax, points)
    if text:
        xy = np.array(label_xy) if label_xy is not None else mid + v * .42
        label(ax, *xy, text, size=size)


def part(ax, name, nodes, a, b, label_xy=None, text=None):
    value = use(name, nodes)
    element(ax, a, b, name[0], text or f"{name}\n{display(value)}", label_xy)


def source(ax, x, y, name, current=False, value=""):
    ax.add_patch(Circle((x, y), .36, fill=False, ec=INK, lw=1.45))
    if current:
        ax.annotate("", (x, y + .23), (x, y - .23), arrowprops={"arrowstyle": "->", "color": INK, "lw": 1.3})
    else:
        label(ax, x, y + .15, "+", 12)
        label(ax, x, y - .15, "−", 12)
    label(ax, x - .55, y, name + ("\n" + value if value else ""), size=10, ha="right")


def axes(fig, bounds, xlim, ylim):
    ax = fig.add_axes(bounds)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    return ax


def overview():
    fig = plt.figure(figsize=(16, 9.8), facecolor="white")
    fig.text(.04, .955, "Detector, bias tee, and RF readout", fontsize=21, weight="bold", color=INK)
    fig.text(.04, .918, "Shared circuit for both operating regimes · Default c30 configuration", fontsize=11, color=MUTED)
    ax = axes(fig, [.03, .19, .94, .69], (0, 19), (0, 8.4))

    source(ax, 1.5, 5.9, "V1", value="DC bias")
    wire(ax, [(1.5, 6.26), (1.5, 7.2), (2.3, 7.2)])
    wire(ax, [(1.5, 5.54), (1.5, 4.9)])
    ground(ax, 1.5, 4.9)
    dot(ax, 2.3, 7.2, "N001")
    part(ax, "R1", ["N001", "N008"], (2.3, 7.2), (5, 7.2), (3.6, 7.75))
    dot(ax, 5, 7.2, "N008", dy=-.32)
    part(ax, "L1", ["N008", "N012"], (5, 7.2), (8.1, 7.2), (6.55, 6.66))
    wire(ax, [(5, 7.2), (5, 8.05), (5.6, 8.05)])
    element(ax, (5.6, 8.05), (7.5, 8.05), "C", "L1 Cpar = 1 pF", (6.55, 8.38), size=8.5)
    wire(ax, [(7.5, 8.05), (8.1, 8.05), (8.1, 7.2)])
    dot(ax, 8.1, 7.2, "N012", dx=.13, dy=.35, ha="left")

    # C1 series resistance is an explicit drawing of the netlist Rser attribute.
    use("C1", ["N013", "N012"])
    element(ax, (8.1, 7.2), (10.1, 7.2), "C", "C1\n7.957 nF", (9.2, 7.85))
    element(ax, (10.1, 7.2), (11.7, 7.2), "R", "C1 Rser\n1 Ω", (10.9, 7.85))
    wire(ax, [(11.7, 7.2), (18.2, 7.2)])
    dot(ax, 12.2, 7.2, "N013", dy=.36)
    ax.annotate("", (18.65, 7.2), (18.15, 7.2), arrowprops={"arrowstyle": "->", "color": INK, "lw": 1.45})
    label(ax, 17.65, 7.8, "Amplifier input", 10)
    label(ax, 17.65, 6.75, "N013 → XU2\nSee amplifier-stage schematic", 8.5, MUTED)
    for x, name in [(12.2, "R20"), (14.4, "R2"), (16.6, "C12")]:
        dot(ax, x, 7.2)
        wire(ax, [(x, 7.2), (x, 5.7)])
        part(ax, name, ["N013", "0"], (x, 5.7), (x, 3.8), (x + .55, 4.7))
        wire(ax, [(x, 3.8), (x, 3.2)])
        ground(ax, x, 3.2)
    label(ax, 14.3, 2.36, "R20 and R2 are parallel RF shunts.\nDefault resistive parallel value: 25 Ω.", 10, MUTED)

    box = Rectangle((6.65, 3.0), 3.0, 3.2, facecolor=LIGHT, edgecolor=MUTED, lw=1, linestyle="--", zorder=0)
    ax.add_patch(box)
    wire(ax, [(8.1, 7.2), (8.1, 6.2)])
    element(ax, (8.1, 6.2), (8.1, 4.9), "L", "Lk\n38 nH", (8.9, 5.6))
    element(ax, (8.1, 4.9), (8.1, 3.0), "R", "Rwire(t)", (8.9, 4.05))
    label(ax, 6.82, 3.22, "Xwire", 10, ha="left", weight="bold")
    dot(ax, 8.1, 3.0, "N024", dx=.1, dy=-.25, ha="left")
    part(ax, "R3", ["N024", "0"], (8.1, 3.0), (8.1, .9), (8.8, 1.9))
    ground(ax, 8.1, .9)
    label(ax, 9.5, .55, "Series return", 9, MUTED)

    source(ax, 3.7, 4.0, "I1", current=True)
    wire(ax, [(3.7, 3.64), (3.7, 3.1)])
    ground(ax, 3.7, 3.1)
    wire(ax, [(3.7, 4.36), (3.7, 5.15), (6.65, 5.15)])
    dot(ax, 3.7, 5.15, "N020", dy=.3)
    label(ax, 6.8, 5.15, "gate", 8.5, BLUE, ha="left")
    label(ax, 3.7, 2.3, "Optical-control current\n1 µA pulse; 5 ps equivalent width", 9, MUTED)
    label(ax, 6.8, 4.35, "gate return\n= ground", 8, MUTED, ha="left")
    label(ax, 2.8, .7, "All ground symbols denote node 0.", 9, MUTED)

    fig.text(.04, .137, "Readout variants", fontsize=11, weight="bold", color=INK)
    rows = [["c30 (shown)", "30 pF", "50 Ω", "50 Ω"],
            ["c120", "120 pF", "50 Ω", "50 Ω"],
            ["asc120", "120 pF", "100 MΩ", "50 Ω"]]
    table_ax = fig.add_axes([.04, .043, .47, .08])
    table_ax.axis("off")
    tab = table_ax.table(cellText=rows, colLabels=["Variant", "C12*", "R20*", "R2"], loc="center", cellLoc="left")
    tab.auto_set_font_size(False)
    tab.set_fontsize(8.5)
    tab.scale(1, 1.15)
    for (r, _), cell in tab.get_celld().items():
        cell.set_edgecolor("#c9d4df")
        if r == 0:
            cell.set_facecolor(LIGHT)
            cell.set_text_props(weight="bold")
    fig.text(.55, .137, "Representation", fontsize=11, weight="bold", color=INK)
    fig.text(.55, .047, "The detector is shown as its electrical equivalent.\nThermal-state circuits and ideal current sensors are omitted.\nIts 10 µΩ numerical series resistance is omitted from this view.\nV1 and optical input are set by the selected case.", fontsize=9, linespacing=1.5, color=MUTED)
    return fig


def amplifier_panel(ax, stage):
    index, title, inp, middle, plus, minus, out, series, feedback, shunt, div, gain = stage
    label(ax, .25, 7.45, title, 13, ha="left", weight="bold")
    # Input path to the non-inverting terminal.
    part(ax, series[0], [inp, middle], (.5, 5.2), (3.0, 5.2), (1.75, 5.8))
    part(ax, series[1], [middle, plus], (3.0, 5.2), (5.3, 5.2), (4.15, 5.8))
    wire(ax, [(5.3, 5.2), (6.35, 5.2)])
    dot(ax, .5, 5.2, inp, dx=-.1, dy=-.35, ha="left")
    dot(ax, 3.0, 5.2, middle, dy=-.35)
    dot(ax, 5.3, 5.2, plus, dy=.27)
    part(ax, shunt, [plus, "0"], (5.3, 5.2), (5.3, 2.65), (4.72, 3.7))
    ground(ax, 5.3, 2.65)

    triangle = Polygon([(6.35, 5.85), (6.35, 3.2), (8.45, 4.5)], closed=True,
                       facecolor=LIGHT, edgecolor=INK, lw=1.45)
    ax.add_patch(triangle)
    label(ax, 6.58, 5.2, "+", 13)
    label(ax, 6.58, 3.8, "−", 13)
    label(ax, 7.16, 4.52, index, 10, weight="bold")
    use(index, [minus, plus, out])
    wire(ax, [(8.45, 4.5), (9.2, 4.5)])
    dot(ax, 9.2, 4.5, out, dy=.3)

    # Frequency-selective feedback from output to the series-element midpoint.
    wire(ax, [(3.0, 5.2), (3.0, 6.4), (4.0, 6.4)])
    part(ax, feedback, [middle, out], (4.0, 6.4), (8.2, 6.4), (6.1, 7.0))
    wire(ax, [(8.2, 6.4), (9.2, 6.4), (9.2, 4.5)])

    # Resistive negative-feedback divider.
    wire(ax, [(9.2, 4.5), (9.2, 2.0)])
    part(ax, div[0], [out, minus], (9.2, 2.0), (7.0, 2.0), (8.1, 2.55))
    dot(ax, 7.0, 2.0, minus, dx=-.2, dy=-.27, ha="right")
    wire(ax, [(7.0, 2.0), (6.0, 2.0), (6.0, 3.8), (6.35, 3.8)])
    part(ax, div[1], [minus, "0"], (7.0, 2.0), (7.0, .55), (7.8, .95))
    ground(ax, 7.0, .55)

    if gain:
        name, output = gain
        value = use(name, [output, "0", out, "0"])
        x, y = 11.0, 3.1
        ax.add_patch(Polygon([(x, y + .55), (x + .42, y), (x, y - .55), (x - .42, y)],
                             closed=True, fill=False, edgecolor=INK, lw=1.45))
        label(ax, x, y + .2, "+", 11)
        label(ax, x, y - .2, "−", 11)
        wire(ax, [(x, y + .55), (x, 4.5), (12, 4.5)])
        dot(ax, 11, 4.5, output, dy=.3)
        wire(ax, [(x, y - .55), (x, 2.15)])
        ground(ax, x, 2.15)
        ax.plot([9.2, 9.8, 9.8, 10.58], [4.5, 4.5, 3.1, 3.1], ls="--", lw=1.1, color=BLUE)
        expression = value.strip("{}").replace("*", " × ")
        label(ax, 11, 5.65, f"{name}: V({output}) =\n{expression}\n× V({out})", size=8, color=BLUE)
        label(ax, x, 1.25, name + "\nIdeal VCVS", 9)
    else:
        wire(ax, [(9.2, 4.5), (11.4, 4.5)])
        ax.annotate("", (11.8, 4.5), (11.4, 4.5), arrowprops={"arrowstyle": "->", "color": INK, "lw": 1.45})
        label(ax, 10.45, 3.9, "To next stage", 9, MUTED)


def amplifier():
    fig = plt.figure(figsize=(18, 12.6), facecolor="white")
    fig.text(.035, .96, "Amplifier-stage connections", fontsize=21, weight="bold", color=INK)
    fig.text(.035, .926, "Signal order: XU2 → XU3 → E1 → XU4 → XU5 → E2   |   Identical node labels denote the same net", fontsize=11, color=MUTED)
    stages = [
        ("XU2", "1 · Capacitive-input stage", "N013", "N006", "N014", "N018", "N007", ["C3", "C4"], "R4", "R5", ["R6", "R7"], None),
        ("XU3", "2 · Capacitive-input stage and E1", "N007", "N009", "N015", "N021", "N010", ["C5", "C6"], "R8", "R9", ["R10", "R11"], ("E1", "N016")),
        ("XU4", "3 · Resistive-input stage", "N016", "N002", "N017", "N022", "N003", ["R12", "R13"], "C7", "C8", ["R14", "R15"], None),
        ("XU5", "4 · Resistive-input stage and E2", "N003", "N004", "N019", "N023", "N005", ["R16", "R17"], "C9", "C10", ["R18", "R19"], ("E2", "N011")),
    ]
    for i, stage in enumerate(stages):
        x = .025 + (i % 2) * .49
        y = .51 if i < 2 else .08
        ax = axes(fig, [x, y, .47, .40], (0, 12.5), (0, 7.9))
        amplifier_panel(ax, stage)
    fig.text(.035, .037, "Op-amp pins: 1 = −, 2 = +, 3 = output. All stages: Aol = 100k; GBW = 10000Meg. Ground = node 0.", fontsize=9, color=MUTED)
    fig.text(.035, .016, "Dashed blue lines indicate voltage control, not conducting connections. AmpGainCal is specified per case. N011 is the unloaded output probe.", fontsize=9, color=MUTED)
    return fig


def main():
    out = ROOT / "docs" / "figures"
    out.mkdir(exist_ok=True)
    # Confirm source polarities and detector ports against the actual deck generator.
    reference_case = selected(["geiger_c30_high_dt005"])[0]
    generated = deck(reference_case, Path("opamp.sub"))
    assert "Xwire N020 0 N012 N024 nanowireElectrothermal_NbN_v5c" in generated
    assert "I1 0 N020 PULSE(0 1u 5n 1p 1p 4p 4000n)" in generated
    assert "V1 N001 0 {I_bias*(10000+20)}" in generated
    assert "Lind=38n" in (ROOT / "models/snspd_nbn_v5c.lib").read_text()
    # Expanded parasitic symbols and the default-value table use these values.
    assert NET["L1"]["value"] == "19894n Cpar=1p"
    assert NET["C1"]["value"] == "7.957n Rser=1"
    assert NET["R2"]["value"] == "50"
    assert NET["R20"]["value"] == "{Rextra}"
    assert NET["C12"]["value"] == "{Cshunt}"
    for variant, capacitance, shunt in [("c30", 30, 50), ("c120", 120, 50), ("asc120", 120, 100000000)]:
        case = selected([f"calorimetric_{variant}_b90_n10"])[0]
        assert (case["C_pF"], case["R20_ohm"]) == (capacitance, shunt)
    for name in ["XU2", "XU3", "XU4", "XU5"]:
        assert NET[name]["value"] == "opamp Aol=100K GBW=10000Meg"
    figures = [("circuit_overview", overview()), ("amplifier_stages", amplifier())]
    if set(DRAWN) != set(NET):
        raise ValueError("Unrepresented external components: " + str(set(NET) - set(DRAWN)))
    with PdfPages(out / "circuit_schematics.pdf") as pdf:
        for name, fig in figures:
            fig.savefig(out / (name + ".svg"))
            fig.savefig(out / (name + ".png"), dpi=180)
            pdf.savefig(fig)
            plt.close(fig)
    sources = ["circuits/bias_tee_and_load.inc", "circuits/amplifier_chain.inc", "snspdtool/core.py", "models/snspd_nbn_v5c.lib"]
    manifest = {"external_components_checked": len(NET), "components": DRAWN,
                "additional_ports_checked": {"Xwire": ["N020", "0", "N012", "N024"], "I1": ["0", "N020"], "V1": ["N001", "0"]},
                "omitted_detector_details": ["thermal-state auxiliaries", "ideal current sensors", "10 microohm numerical series resistance"],
                "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}}
    (ROOT / "provenance/circuit_diagram_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Rendered two schematics; checked all {len(NET)} external components and three generated-deck elements.")


if __name__ == "__main__":
    main()
