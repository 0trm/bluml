# %%
"""Tests for the owner notebooks: each section asks the owner before the agent answers.

    uv run --with numpy,pandas,pytest pytest tests
"""

import json
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parent.parent / "skills"
TEMPLATES = [
    "exploring-data/templates/eda.ipynb",
    "building-datasets/templates/data.ipynb",
    "training-models/templates/train.ipynb",
    "evaluating-models/templates/eval.ipynb",
]


def load(rel: str) -> dict:
    return json.loads((SKILLS / rel).read_text())


def tag(cell: dict) -> str:
    return cell["metadata"]["tags"][0]


def sections(cells: list[dict]) -> list[list[dict]]:
    out = []
    for c in cells:
        if tag(c) == "question":
            out.append([c])
        elif out and tag(c) != "footer":
            out[-1].append(c)
    return out


# %%
@pytest.mark.parametrize("rel", TEMPLATES)
def test_each_section_takes_the_owners_pick_before_the_agents_recommendation(rel):
    secs = sections(load(rel)["cells"])
    assert secs
    for sec in secs:
        tags = [tag(c) for c in sec]
        owner, agent = tags.index("owner-reading"), tags.index("agent-reading")
        assert 0 < owner < agent, tags
        assert tags[1:owner] and set(tags[1:owner]) <= {"chart", "cards", "groups"}, tags
        assert sec[agent]["metadata"]["jupyter"]["source_hidden"] is True
        reading = "".join(sec[agent]["source"])
        if "**Decision:**" in "".join(sec[0]["source"]):
            assert tags[agent + 1:] == ["decision"], tags
            assert "### Recommendation" in reading
            assert "pick" in "".join(sec[owner]["source"])
        else:
            assert "decision" not in tags and "Recommendation" not in reading, tags


@pytest.mark.parametrize("rel", TEMPLATES)
def test_code_is_folded_empty_of_outputs_and_compiles(rel):
    cells = load(rel)["cells"]
    assert len({c["id"] for c in cells}) == len(cells)
    for c in cells:
        if c["cell_type"] == "code":
            assert c["metadata"]["jupyter"]["source_hidden"] is True
            assert c["outputs"] == [] and c["execution_count"] is None
            compile("".join(c["source"]), c["id"], "exec")


def test_each_skill_points_at_its_notebook():
    for rel in TEMPLATES:
        skill = (SKILLS / rel.split("/")[0] / "SKILL.md").read_text()
        assert f"(templates/{Path(rel).name})" in skill, rel


def test_skill_descriptions_fit_the_1024_character_limit():
    # Agent Skills specification: https://agentskills.io/specification
    for skill in sorted(SKILLS.glob("*/SKILL.md")):
        front = skill.read_text().split("---")[1]
        desc = next(line for line in front.splitlines() if line.startswith("description:"))
        desc = desc.removeprefix("description:").strip().strip('"')
        assert 0 < len(desc) <= 1024, (skill.parent.name, len(desc))
