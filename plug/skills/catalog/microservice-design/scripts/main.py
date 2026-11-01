"""Metadata entrypoint for microservice-design."""
SKILL_NAME = "microservice-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
