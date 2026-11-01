"""Metadata entrypoint for ci-cd."""
SKILL_NAME = "ci-cd"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
