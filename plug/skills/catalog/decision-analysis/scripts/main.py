"""Helper entrypoint for the decision-analysis skill."""

SKILL_NAME = "decision-analysis"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
