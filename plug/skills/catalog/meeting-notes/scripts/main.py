"""Helper entrypoint for the meeting-notes skill."""

SKILL_NAME = "meeting-notes"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
