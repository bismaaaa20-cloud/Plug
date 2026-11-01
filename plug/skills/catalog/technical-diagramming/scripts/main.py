"""Metadata entrypoint for technical-diagramming."""
SKILL_NAME = "technical-diagramming"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
