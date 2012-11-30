#!/usr/bin/env bash

TIMEOUT=600
CMD="./pywebdlmond"

echo "Restarting ${CMD} every ${TIMEOUT} seconds."

while [ 1 ]; do
  ${CMD} &
  sleep ${TIMEOUT}
  kill %1
  wait %1
done

