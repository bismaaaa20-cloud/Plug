"""Metadata entrypoint for data-migration."""
SKILL_NAME = "data-migration"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
