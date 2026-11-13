# %%
"""Tests for the model card: the example fills every placeholder and keeps the template's blocks.

    uv run --with numpy,pandas,pytest pytest tests
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "skills/launching-models/templates/MODEL_CARD.html"
EXAMPLE = ROOT / "examples/delivery-eta/MODEL_CARD.html"


def runs(html: str) -> dict:
    block = re.search(r'<script type="application/json" id="runs">(.*?)</script>', html, re.S)
    return json.loads(block.group(1))


def text(html: str) -> str:
    """The page without its comments, style and scripts: what a reader sees."""
    for pattern in (r"<!--.*?-->", r"<style>.*?</style>", r"<script.*?</script>"):
        html = re.sub(pattern, "", html, flags=re.S)
    return html


def blocks(html: str) -> list[str]:
    """Block headings and component labels, in order."""
    return re.findall(r'<div class="bh[^"]*"><b>(.*?)</b>|<div class="comp"><b>(.*?)</b>', html)


# %%
def test_template_runs_parse_with_one_chosen_run():
    data = runs(TEMPLATE.read_text())
    assert [r["chosen"] for r in data["runs"] if r.get("chosen")] == [True]


def test_example_fills_every_placeholder():
    html = EXAMPLE.read_text()
    assert re.findall(r"\{[a-z][^{}\"]*\}", text(html)) == []
    data = runs(html)
    assert "{" not in data["caption"]
    assert all("{" not in r["label"] and r["value"] > 0 for r in data["runs"])
    assert sum(bool(r.get("chosen")) for r in data["runs"]) == 1


def test_example_keeps_the_templates_blocks():
    assert blocks(EXAMPLE.read_text()) == blocks(TEMPLATE.read_text())


def test_card_id_matches_model_md():
    model_md = (ROOT / "examples/delivery-eta/MODEL.md").read_text()
    row = re.search(r"^\| (\S+/\S+) \| live \|", model_md, re.M)
    card = re.search(r'<span class="id"[^>]*>(.*?)<span class="ver">@(\w+)</span>', EXAMPLE.read_text())
    assert row and card and card.group(1) == row.group(1)
