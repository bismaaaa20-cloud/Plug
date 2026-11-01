"""Small metadata entrypoint for data-visualization skill."""
SKILL_NAME = "data-visualization"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
