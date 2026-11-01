"""Metadata entrypoint for incident-postmortem."""
SKILL_NAME = "incident-postmortem"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
