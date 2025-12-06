
FROM ubuntu:24.04

RUN apt update && apt install -yyq socat

WORKDIR /var/archive

COPY archive entrypoint.sh ./

RUN mkdir libraries secrets

RUN chmod +x archive entrypoint.sh \
    && chown nobody:nogroup libraries secrets

USER nobody

ENTRYPOINT [ "./entrypoint.sh" ]
