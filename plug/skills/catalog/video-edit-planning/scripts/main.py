"""Metadata entrypoint for video-edit-planning."""
SKILL_NAME = "video-edit-planning"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
