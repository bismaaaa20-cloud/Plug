"""Small metadata entrypoint for image-creation skill."""
SKILL_NAME = "image-creation"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
