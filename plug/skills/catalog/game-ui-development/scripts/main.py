"""Metadata entrypoint for game-ui-development."""
SKILL_NAME = "game-ui-development"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
