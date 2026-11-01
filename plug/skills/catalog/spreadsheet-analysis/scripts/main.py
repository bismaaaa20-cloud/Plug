"""Helper entrypoint for the spreadsheet-analysis skill."""

SKILL_NAME = "spreadsheet-analysis"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
