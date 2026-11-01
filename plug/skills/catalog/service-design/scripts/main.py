"""Metadata entrypoint for service-design."""
SKILL_NAME = "service-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
