#!/bin/bash -e
if [ -z "$GF_SECURITY_ADMIN_USER" ]; then
    GF_SECURITY_ADMIN_USER="admin"
fi
if [ -z "$GF_SECURITY_ADMIN_PASSWORD" ]; then
    GF_SECURITY_ADMIN_PASSWORD="admin"
fi
password=`echo -n "${GF_SECURITY_ADMIN_USER}:${GF_SECURITY_ADMIN_PASSWORD}" | base64`

GRAFANA_SERVICE_ID=`curl -s -X POST \
-H "Accept: application/json" \
-H "Content-Type: application/json" \
-H "Authorization: Basic ${password}" \
-d '{"name":"test", "role": "Editor"}' \
http://admin:admin@${MY_IP}:3000/api/serviceaccounts | jq -r .id`

# Export service account to enable continued API execution in the same shell
export GRAFANA_SERVICE_ID
# Save the service account to grafana_profile for reuse when re-entering the container
echo "export GRAFANA_SERVICE_ID=${GRAFANA_SERVICE_ID}" >> ~/.grafana_profile 

GRAFANA_API_KEY=`curl -s -X POST \
-H "Accept: application/json" \
-H "Content-Type: application/json" \
-H "Authorization: Basic ${password}" \
-d '{"name":"test"}' \
http://admin:admin@${MY_IP}:3000/api/serviceaccounts/${GRAFANA_SERVICE_ID}/tokens | jq -r .key`

# Export token to enable continued API execution in the same shell
export GRAFANA_API_KEY
# Save the token to grafana_profile for reuse when re-entering the container
echo "export GRAFANA_API_KEY=${GRAFANA_API_KEY}" >> ~/.grafana_profile 

curl -s -X POST \
-H "Accept: application/json" \
-H "Content-Type: application/json" \
-H "Authorization: Basic ${password}" \
-H "${GRAFANA_API_KEY}" \
-d '{"name":"yamcs-ds1", "type":"yamcs-yamcs-datasource", "url":"http://yamcs:8090", "access":"proxy", "basicAuth":false, "jsonData":{"instance":"scsat1"}}' \
http://admin:admin@${MY_IP}:3000/api/datasources
