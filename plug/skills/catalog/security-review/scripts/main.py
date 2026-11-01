"""Helper entrypoint for the security-review skill."""

SKILL_NAME = "security-review"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
