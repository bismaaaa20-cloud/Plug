"""Metadata entrypoint for user-feedback-triage."""
SKILL_NAME = "user-feedback-triage"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
