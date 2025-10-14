FROM alpine

ENV PORT=8080

WORKDIR /app

COPY server.sh .

RUN chmod +x server.sh

EXPOSE ${PORT}

ENTRYPOINT ["sh", "server.sh"]