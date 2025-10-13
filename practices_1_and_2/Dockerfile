FROM alpine

WORKDIR /app

COPY menu.sh .

RUN chmod +x menu.sh

ENTRYPOINT ["sh", "menu.sh"]