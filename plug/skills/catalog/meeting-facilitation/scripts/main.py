"""Metadata entrypoint for meeting-facilitation."""
SKILL_NAME = "meeting-facilitation"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
