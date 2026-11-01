"""Metadata entrypoint for data-pipeline-design."""
SKILL_NAME = "data-pipeline-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
