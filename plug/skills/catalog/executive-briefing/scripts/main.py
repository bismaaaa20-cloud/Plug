"""Metadata entrypoint for executive-briefing."""
SKILL_NAME = "executive-briefing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
