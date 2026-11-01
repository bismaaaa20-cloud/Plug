"""Helper entrypoint for the code-review skill."""

SKILL_NAME = "code-review"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
