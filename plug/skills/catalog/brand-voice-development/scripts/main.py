"""Metadata entrypoint for brand-voice-development."""
SKILL_NAME = "brand-voice-development"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
