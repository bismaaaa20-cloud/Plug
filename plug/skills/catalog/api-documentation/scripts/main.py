"""Metadata entrypoint for api-documentation."""
SKILL_NAME = "api-documentation"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
