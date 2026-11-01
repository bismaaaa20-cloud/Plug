"""Metadata entrypoint for game-publishing."""
SKILL_NAME = "game-publishing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
