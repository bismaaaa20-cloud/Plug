"""Metadata entrypoint for video-storyboard."""
SKILL_NAME = "video-storyboard"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
