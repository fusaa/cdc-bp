#!/bin/bash

if [ -z "$1" ]; then
  echo "Use: $0 <debezium-host>"
  exit 1
fi

HOSTNAME=$1

curl -X PUT "http://$HOSTNAME:8083/connectors/fin-db-transactions/config" \
  -H "Content-Type: application/json" \
  -d '{
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "topic.prefix": "cdc",
    "database.user": "postgres",
    "database.dbname": "fin_db",
    "database.hostname": "postgres",
    "database.password": "postgres",
    "plugin.name": "pgoutput",
    "decimal.handling.mode": "string"
  }'
