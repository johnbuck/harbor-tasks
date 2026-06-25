FROM harbor-agents-rich:latest
WORKDIR /app
RUN pip install --no-cache-dir pytest==8.4.1

# Seed a sample text file (with punctuation) the agent can use while developing.
RUN printf '%s\n' \
    'The quick brown fox, the lazy dog.' \
    'The fox! The fox? the DOG; the dog.' \
    "don't stop the dog, the fox." > /app/sample.txt
