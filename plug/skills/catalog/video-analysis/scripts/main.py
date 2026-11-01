"""Small metadata entrypoint for video-analysis skill."""
SKILL_NAME = "video-analysis"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
