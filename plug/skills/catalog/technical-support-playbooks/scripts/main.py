"""Metadata entrypoint for technical-support-playbooks."""
SKILL_NAME = "technical-support-playbooks"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
