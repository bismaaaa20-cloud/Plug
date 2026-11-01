"""Metadata entrypoint for copyediting."""
SKILL_NAME = "copyediting"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
