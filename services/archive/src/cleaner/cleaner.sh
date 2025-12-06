#!/bin/sh

while true; do
    date -uR

    find "/var/archive/libraries/" \
        -type f \
        -and -not -newermt "-1800 seconds" \
        -delete

    find "/var/archive/secrets/" \
        -type f \
        -and -not -newermt "-1800 seconds" \
        -delete

    sleep 60
done
