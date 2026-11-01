"""Metadata entrypoint for operations-playbook."""
SKILL_NAME = "operations-playbook"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
