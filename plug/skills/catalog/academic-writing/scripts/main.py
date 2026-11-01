"""Metadata entrypoint for academic-writing."""
SKILL_NAME = "academic-writing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
