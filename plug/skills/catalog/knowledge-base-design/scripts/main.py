"""Metadata entrypoint for knowledge-base-design."""
SKILL_NAME = "knowledge-base-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
