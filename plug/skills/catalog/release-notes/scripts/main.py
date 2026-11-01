"""Metadata entrypoint for release-notes."""
SKILL_NAME = "release-notes"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
