"""Metadata entrypoint for game-content-planning."""
SKILL_NAME = "game-content-planning"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
