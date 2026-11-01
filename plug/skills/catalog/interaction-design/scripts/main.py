"""Metadata entrypoint for interaction-design."""
SKILL_NAME = "interaction-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
