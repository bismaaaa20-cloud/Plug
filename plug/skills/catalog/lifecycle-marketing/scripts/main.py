"""Metadata entrypoint for lifecycle-marketing."""
SKILL_NAME = "lifecycle-marketing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
