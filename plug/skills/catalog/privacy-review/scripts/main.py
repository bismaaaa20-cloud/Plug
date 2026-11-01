"""Helper entrypoint for the privacy-review skill."""

SKILL_NAME = "privacy-review"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
