"""Metadata entrypoint for game-performance-review."""
SKILL_NAME = "game-performance-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
