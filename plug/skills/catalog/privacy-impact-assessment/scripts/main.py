"""Metadata entrypoint for privacy-impact-assessment."""
SKILL_NAME = "privacy-impact-assessment"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
