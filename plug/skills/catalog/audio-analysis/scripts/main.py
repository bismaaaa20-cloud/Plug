"""Metadata entrypoint for audio-analysis."""
SKILL_NAME = "audio-analysis"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
