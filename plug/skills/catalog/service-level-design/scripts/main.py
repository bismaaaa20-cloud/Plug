"""Metadata entrypoint for service-level-design."""
SKILL_NAME = "service-level-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
