"""Metadata entrypoint for video-captioning."""
SKILL_NAME = "video-captioning"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
