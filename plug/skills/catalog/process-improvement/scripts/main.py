"""Metadata entrypoint for process-improvement."""
SKILL_NAME = "process-improvement"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
