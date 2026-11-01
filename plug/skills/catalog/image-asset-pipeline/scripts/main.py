"""Metadata entrypoint for image-asset-pipeline."""
SKILL_NAME = "image-asset-pipeline"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
