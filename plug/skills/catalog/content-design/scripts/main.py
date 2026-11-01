"""Metadata entrypoint for content-design."""
SKILL_NAME = "content-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
