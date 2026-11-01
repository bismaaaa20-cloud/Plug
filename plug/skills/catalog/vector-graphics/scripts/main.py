"""Metadata entrypoint for vector-graphics."""
SKILL_NAME = "vector-graphics"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
