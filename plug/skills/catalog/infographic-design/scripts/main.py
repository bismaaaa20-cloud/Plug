"""Metadata entrypoint for infographic-design."""
SKILL_NAME = "infographic-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
