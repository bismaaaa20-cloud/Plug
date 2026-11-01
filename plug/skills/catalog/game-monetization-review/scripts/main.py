"""Metadata entrypoint for game-monetization-review."""
SKILL_NAME = "game-monetization-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
