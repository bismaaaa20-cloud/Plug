"""Metadata entrypoint for gameplay-design."""
SKILL_NAME = "gameplay-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
