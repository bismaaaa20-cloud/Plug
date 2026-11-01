"""Create a portable Agent Skill scaffold without overwriting files."""

from pathlib import Path
import re


def create_skill(root: str | Path, name: str, *, description: str, triggers: tuple[str, ...] = ()) -> Path:
    skill_name = name.strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_name):
        raise ValueError("skill name must be lowercase kebab-case")
    if not description.strip():
        raise ValueError("description must not be empty")
    target = Path(root) / skill_name
    target.mkdir(parents=True, exist_ok=False)
    trigger_text = ", ".join(item.replace(",", " ") for item in triggers)
    (target / "SKILL.md").write_text(
        f"---\nname: {skill_name}\ndescription: {description.strip()}\ntriggers: {trigger_text}\n---\n\n"
        "# Instructions\n\nDescribe the steps this skill should follow. Keep external actions behind explicit permissions.\n",
        encoding="utf-8",
    )
    scripts = target / "scripts"
    scripts.mkdir()
    (scripts / "main.py").write_text(
        '"""Optional helper script for this skill; review before execution."""\n\n'
        'def run(arguments):\n'
        '    return {"received": arguments}\n', encoding="utf-8"
    )
    return target
