"""Metadata entrypoint for social-media-strategy."""
SKILL_NAME = "social-media-strategy"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
