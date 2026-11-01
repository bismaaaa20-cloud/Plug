"""Metadata entrypoint for game-community-strategy."""
SKILL_NAME = "game-community-strategy"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
