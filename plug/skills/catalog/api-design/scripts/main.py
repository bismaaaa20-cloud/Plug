"""Metadata entrypoint for api-design."""
SKILL_NAME = "api-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
