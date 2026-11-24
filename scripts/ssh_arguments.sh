#!/bin/bash
# Quote each argument for the remote login shell; keep the remote body static.
shell_quote() {
  local value="$1"
  local quote="'"
  local escaped_quote="'\\''"
  printf "'%s'" "${value//"$quote"/"$escaped_quote"}"
}

ssh_command() {
  local value
  printf "%s" "sudo bash -s --"
  for value in "$@"; do
    printf " %s" "$(shell_quote "$value")"
  done
}
