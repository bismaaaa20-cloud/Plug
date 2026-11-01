"""Metadata entrypoint for multimedia-production."""
SKILL_NAME = "multimedia-production"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
