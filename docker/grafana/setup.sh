#!/bin/bash -e
GRAFANA_SERVICE_ID=`curl -s -X POST \
-H "Accept: application/json" \
-H "Content-Type: application/json" \
-H "Authorization: Basic YWRtaW46YWRtaW4=" \
-d '{"name":"test", "role": "Editor"}' \
http://admin:admin@${MY_IP}:3000/api/serviceaccounts | jq -r .id`

export GRAFANA_SERVICE_ID
echo "export GRAFANA_SERVICE_ID=${GRAFANA_SERVICE_ID}" >> ~/.grafana_profile 

GRAFANA_API_KEY=`curl -s -X POST \
-H "Accept: application/json" \
-H "Content-Type: application/json" \
-H "Authorization: Basic YWRtaW46YWRtaW4=" \
-d '{"name":"test"}' \
http://admin:admin@${MY_IP}:3000/api/serviceaccounts/${GRAFANA_SERVICE_ID}/tokens | jq -r .key`

export GRAFANA_API_KEY
echo "export GRAFANA_API_KEY=${GRAFANA_API_KEY}" >> ~/.grafana_profile 

curl -s -X POST \
-H "Accept: application/json" \
-H "Content-Type: application/json" \
-H "Authorization: Basic YWRtaW46YWRtaW4=" \
-H "${GRAFANA_API_KEY}" \
-d '{"name":"yamcs-ds1", "type":"yamcs-yamcs-datasource", "url":"http://yamcs:8090", "access":"proxy", "basicAuth":false, "jsonData":{"instance":"scsat1"}}' \
http://admin:admin@${MY_IP}:3000/api/datasources


