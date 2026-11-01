"""Metadata entrypoint for database-optimization."""
SKILL_NAME = "database-optimization"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
