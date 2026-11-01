"""Metadata entrypoint for database-backup-planning."""
SKILL_NAME = "database-backup-planning"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
