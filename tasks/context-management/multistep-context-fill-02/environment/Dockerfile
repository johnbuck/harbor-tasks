FROM harbor-agents-prebaked:latest
WORKDIR /app
COPY gen_chunks.py /tmp/gen_chunks.py
RUN python3 /tmp/gen_chunks.py && rm /tmp/gen_chunks.py
