#!/bin/sh
# Watchdog de n8n: chequea /healthz/readiness y si falla reinicia el servicio via API de Railway.
# Corre como cron service en Railway (cada 5 min). Ver docs/team/decisions.md.
set -u

URL="${N8N_HEALTH_URL:?Falta N8N_HEALTH_URL}"
SERVICE_ID="${N8N_SERVICE_ID:?Falta N8N_SERVICE_ID}"
ENV_ID="${RAILWAY_ENVIRONMENT_ID:?Falta RAILWAY_ENVIRONMENT_ID}"

# 3 intentos separados por 15s para no reiniciar por un fallo transitorio
OK=0
i=1
while [ "$i" -le 3 ]; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 "$URL" || echo 000)
  if [ "$CODE" = "200" ]; then
    OK=1
    break
  fi
  echo "intento $i: readiness respondio HTTP $CODE"
  i=$((i + 1))
  [ "$i" -le 3 ] && sleep 15
done

if [ "$OK" = "1" ]; then
  echo "n8n sano (readiness 200)"
  exit 0
fi

echo "n8n NO responde readiness tras 3 intentos -> disparando redeploy"

QUERY="{\"query\":\"mutation { serviceInstanceRedeploy(environmentId: \\\"$ENV_ID\\\", serviceId: \\\"$SERVICE_ID\\\") }\"}"

if [ -n "${RAILWAY_PROJECT_TOKEN:-}" ]; then
  AUTH_HEADER="Project-Access-Token: $RAILWAY_PROJECT_TOKEN"
elif [ -n "${RAILWAY_ACCOUNT_TOKEN:-}" ]; then
  AUTH_HEADER="Authorization: Bearer $RAILWAY_ACCOUNT_TOKEN"
else
  echo "ERROR: falta RAILWAY_PROJECT_TOKEN o RAILWAY_ACCOUNT_TOKEN, no puedo reiniciar"
  exit 1
fi

RESP=$(curl -s --max-time 30 https://backboard.railway.com/graphql/v2 \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "$QUERY")
echo "respuesta API: $RESP"

case "$RESP" in
  *'"serviceInstanceRedeploy":true'*) RESULTADO="n8n fue reiniciado automaticamente" ;;
  *) RESULTADO="n8n esta caido y el reinicio automatico FALLO (revisar watchdog)" ;;
esac
echo "$RESULTADO"

# Alerta opcional por Telegram
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
  curl -s --max-time 20 "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d chat_id="${TELEGRAM_CHAT_ID}" \
    --data-urlencode text="⚠️ Watchdog: $RESULTADO" >/dev/null || true
fi

case "$RESULTADO" in
  *FALLO*) exit 1 ;;
esac
exit 0
