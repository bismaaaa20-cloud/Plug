"""Metadata entrypoint for release-coordination."""
SKILL_NAME = "release-coordination"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
