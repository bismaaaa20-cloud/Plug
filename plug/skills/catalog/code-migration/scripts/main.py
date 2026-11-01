"""Metadata entrypoint for code-migration."""
SKILL_NAME = "code-migration"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
