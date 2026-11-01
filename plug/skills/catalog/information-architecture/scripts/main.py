"""Metadata entrypoint for information-architecture."""
SKILL_NAME = "information-architecture"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
