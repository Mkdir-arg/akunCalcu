FROM n8nio/n8n:latest

USER root
COPY entrypoint.sh /docker-entrypoint-custom.sh
RUN chmod +x /docker-entrypoint-custom.sh

ENTRYPOINT ["/bin/sh", "/docker-entrypoint-custom.sh"]
CMD []
