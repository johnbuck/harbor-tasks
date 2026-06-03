FROM harbor-agents-rich:latest

# Write-persistence probe: nothing to stage. The agent must create
# /app/answer.md itself; the verifier reads it from the same /app. workdir is
# /app by default in the rich image; declared here for clarity.
WORKDIR /app
