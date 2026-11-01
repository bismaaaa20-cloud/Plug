"""Metadata entrypoint for game-economy-design."""
SKILL_NAME = "game-economy-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
