#!/bin/bash
file_name="scsat1_ini.json"
sed -i 's/\\/\\\\/g' ${file_name}
if [ -z "$GF_SECURITY_ADMIN_USER" ]; then
    GF_SECURITY_ADMIN_USER="admin"
fi
if [ -z "$GF_SECURITY_ADMIN_PASSWORD" ]; then
    GF_SECURITY_ADMIN_PASSWORD="admin"
fi
password=`echo -n "${GF_SECURITY_ADMIN_USER}:${GF_SECURITY_ADMIN_PASSWORD}" | base64`

while read LINE
do
    JSON_DATA=`echo ${LINE} | jq -r .dashboard.id=null`
    result_m=`curl -s -X POST \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Basic ${password}" \
    -H "${GRAFANA_API_KEY}" \
    -d "${JSON_DATA}" \
    http://admin:admin@${MY_IP}:3000/api/dashboards/db`

    if echo "$result_m" | jq -r .message | grep -q "folder not found"; then
        folder_data=`echo ${JSON_DATA} | jq -c -r '{"uid": .folderUid, "title": .folderTitle}'`
        curl -s -X POST \
        -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        -H "Authorization: Basic ${password}" \
        -H "${GRAFANA_API_KEY}" \
        -d "${folder_data}" \
        http://admin:admin@${MY_IP}:3000/api/folders

        curl -s -X POST \
        -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        -H "Authorization: Basic ${password}" \
        -H "${GRAFANA_API_KEY}" \
        -d "${JSON_DATA}" \
        http://admin:admin@${MY_IP}:3000/api/dashboards/db
    fi
done < ${file_name}
