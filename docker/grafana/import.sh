#!/bin/bash
FILE_NAME=$1
sed -i 's/\\/\\\\/g' my_dashboard.json
while read LINE
do
    JSON_DATA=`echo ${LINE} | jq -r .dashboard.id=null`
    result_m=`curl -s -X POST \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Basic YWRtaW46YWRtaW4=" \
    -H "${GRAFANA_API_KEY}" \
    -d "${JSON_DATA}" \
    http://admin:admin@${MY_IP}:3000/api/dashboards/db`

    if echo "$result_m" | jq -r .message | grep -q "folder not found"; then
        folder_data=`echo ${JSON_DATA} | jq -c -r '{"uid": .folderUid, "title": .folderTitle}'`
        curl -s -X POST \
        -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        -H "Authorization: Basic YWRtaW46YWRtaW4=" \
        -H "${GRAFANA_API_KEY}" \
        -d "${folder_data}" \
        http://admin:admin@${MY_IP}:3000/api/folders

        curl -s -X POST \
        -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        -H "Authorization: Basic YWRtaW46YWRtaW4=" \
        -H "${GRAFANA_API_KEY}" \
        -d "${JSON_DATA}" \
        http://admin:admin@${MY_IP}:3000/api/dashboards/db
    fi
done < ${FILE_NAME}
