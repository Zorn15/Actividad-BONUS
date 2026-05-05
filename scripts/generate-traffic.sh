#!/usr/bin/env bash
# Script de trafico sintetico - Bash
# Uso: ./generate-traffic.sh [BASE_URL] [DURATION_SECONDS]

BASE_URL="${1:-http://localhost:3000}"
DURATION="${2:-0}"

ENDPOINTS=(
  "GET /"
  "GET /api/datos"
  "GET /api/datos"
  "GET /api/lento"
  "GET /api/usuarios"
  "GET /api/usuarios"
  "GET /api/usuarios/1"
  "GET /api/usuarios/2"
  "GET /api/usuarios/999"
  "POST /api/usuarios"
  "GET /api/error"
  "GET /api/error"
  "GET /health"
)

echo "Generando trafico contra $BASE_URL"
echo "Duracion: $([ "$DURATION" -le 0 ] && echo 'infinita' || echo "${DURATION}s")"
echo "Detener con Ctrl+C"
echo

START=$(date +%s)
COUNT=0
while true; do
  if [ "$DURATION" -gt 0 ]; then
    NOW=$(date +%s)
    [ $((NOW - START)) -ge "$DURATION" ] && break
  fi

  IDX=$((RANDOM % ${#ENDPOINTS[@]}))
  IFS=' ' read -r METHOD PATH <<< "${ENDPOINTS[$IDX]}"
  COUNT=$((COUNT + 1))

  if [ "$METHOD" = "POST" ]; then
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" \
      -d "{\"name\":\"user-$RANDOM\",\"role\":\"user\"}" "$BASE_URL$PATH")
  else
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X "$METHOD" "$BASE_URL$PATH")
  fi

  printf "[%4d] %-4s %-25s -> %s\n" "$COUNT" "$METHOD" "$PATH" "$STATUS"

  SLEEP_MS=$((100 + RANDOM % 500))
  sleep "$(awk -v ms=$SLEEP_MS 'BEGIN{print ms/1000}')"
done

echo
echo "Total requests enviados: $COUNT"
