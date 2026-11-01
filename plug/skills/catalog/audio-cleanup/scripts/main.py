"""Metadata entrypoint for audio-cleanup."""
SKILL_NAME = "audio-cleanup"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
