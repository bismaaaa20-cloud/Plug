"""Metadata entrypoint for board-reporting."""
SKILL_NAME = "board-reporting"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
