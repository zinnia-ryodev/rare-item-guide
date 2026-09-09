#!/usr/bin/env bash
# ./build.sh                  regenerate index.html from src/ + data/
# ./build.sh --refresh-wiki   re-download the 3 wiki source pages first
# ./build.sh --verify         also run the data-regression check (build/data.lock)
set -euo pipefail
cd "$(dirname "$0")"

REFRESH=0; VERIFY=0
for a in "$@"; do
  case "$a" in
    --refresh-wiki) REFRESH=1 ;;
    --verify)       VERIFY=1 ;;
    *) echo "unknown flag: $a" >&2; exit 2 ;;
  esac
done

if [[ $REFRESH == 1 ]]; then
  UA="Mozilla/5.0"; base="https://wikiwiki.jp/guildmono2"
  curl -sL --max-time 30 -A "$UA" "$base/%E3%81%8A%E3%81%99%E3%81%99%E3%82%81%E3%83%91%E3%83%BC%E3%83%86%E3%82%A3%E7%B7%A8%E6%88%90" -o data/wiki/party-formations.html
  curl -sL --max-time 30 -A "$UA" "$base/%E3%83%88%E3%83%AC%E3%83%8F%E3%83%B3%E3%83%BB%E9%87%91%E7%AD%96%E3%83%91%E3%83%BC%E3%83%86%E3%82%A3%E3%83%BC" -o data/wiki/treasure-hunt.html
  curl -sL --max-time 30 -A "$UA" "$base/%E3%83%89%E3%83%AD%E3%83%83%E3%83%97%E3%82%A2%E3%82%A4%E3%83%86%E3%83%A0" -o data/wiki/drop-item.html
  curl -sL --max-time 30 -A "$UA" "$base/%E3%83%A2%E3%83%B3%E3%82%B9%E3%82%BF%E3%83%BC%E5%9B%B3%E9%91%91" -o data/wiki/monster-encyclopedia.html
  date -u +"%Y-%m-%dT%H:%MZ" > data/wiki/FETCHED_AT.txt
  echo "wiki refreshed: $(cat data/wiki/FETCHED_AT.txt)"
fi

python3 build/build.py
[[ $VERIFY == 1 ]] && python3 build/verify.py || true
