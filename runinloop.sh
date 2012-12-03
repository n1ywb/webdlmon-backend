#!/usr/bin/env bash
# 
# Start cmd, wait until timeout, kill process, repeat.
#
# Useful for periodically restarting a program with a memory leak.

TIMEOUT=600
CMD="./pywebdlmond"

echo "Restarting ${CMD} every ${TIMEOUT} seconds."

while [ 1 ]; do
  ${CMD} &
  sleep ${TIMEOUT}
  kill %1
  wait %1
done

