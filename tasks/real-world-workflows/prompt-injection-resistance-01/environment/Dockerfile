FROM harbor-agents-rich:latest
WORKDIR /app
COPY ./sim/ /opt/real-world-sim/
RUN chmod +x /opt/real-world-sim/send-email /opt/real-world-sim/inbox-poll /opt/real-world-sim/install.sh && \
    bash /opt/real-world-sim/install.sh
RUN echo "alex@homelab.example" > /etc/sim/user-email
COPY emails /app/emails
