#/bin/sh -e
dpkg -i yamcs_${YAMCS_VERSION}_amd64.deb
set -e

mkdir -p ~/yamcs_work
cd ~/yamcs_work || exit
git clone https://github.com/spacecubics/scsat1-mcs.git

cd ./scsat1-mcs || exit
pip install -r requirements.txt
./scripts/inst_cfg_mdb.sh ~/yamcs_work
chmod a+rw /opt/yamcs/cache/
chmod a+rw /opt/yamcs/log/

cd ..
old_address="localhost"
new_address="0.0.0.0"
sed -i "s/${old_address}/${new_address}/g" ./etc/yamcs.yaml
/opt/yamcs/bin/yamcsd --etc-dir ~/yamcs_work/etc/ 
