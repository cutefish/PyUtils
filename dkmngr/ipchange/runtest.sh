PROXY="http://www-proxy.us.oracle.com:80/"
KV_LIB=/home/xiaoy/myproj/kv-cluster/lib

# Update the script.
cp entrypoint.py dns/
cp entrypoint.py client/
cp entrypoint.py server/
python dockerfilegen.py dns $PROXY
python dockerfilegen.py client $PROXY
python dockerfilegen.py server $PROXY

# Build dns image
docker build -t oracle-kvtest/ipchange-dns dns

# Run dns
docker run -d -h dns.kv --cap-add=NET_ADMIN --cap-add=SYS_ADMIN --mac-address="22:44:66:88:01:00" --dns="127.0.0.1" --name=kvtest_dns oracle-kvtest/ipchange-dns

# Check dns
sleep 10
docker exec kvtest_dns ifconfig
docker exec kvtest_dns cat /etc/hosts
docker exec kvtest_dns host dns.kv
docker exec kvtest_dns host server0.kv

#docker exec kvtest_dns python /sbin/entrypoint.py flipdns server0
#docker exec kvtest_dns host server0.kv
#docker exec kvtest_dns python /sbin/entrypoint.py flipdns server0
#docker exec kvtest_dns host server0.kv

# Build servre image
docker build -t oracle-kvtest/ipchange-server server

# Run servers
for i in 0 1 2
do
    docker run -d -h server$i.kv -v $KV_LIB:/kvlib:ro --cap-add=NET_ADMIN --cap-add=SYS_ADMIN --mac-address="22:44:66:88:00:1$i" --dns="172.17.0.100" --name=kvtest_server$i oracle-kvtest/ipchange-server server $i 2 0
done

sleep 5
# Check server
for i in 0 1 2
do
    docker exec kvtest_server$i ifconfig
    docker exec kvtest_server$i cat /etc/hosts
    docker exec kvtest_server$i host server$i.kv
    docker exec kvtest_server$i jps
done

#docker exec kvtest_server0 python /sbin/entrypoint.py flipip server0
#docker exec kvtest_server0 ifconfig
#docker exec kvtest_server0 cat /etc/hosts

# Build client image
docker build -t oracle-kvtest/ipchange-client client

# Run client deploy
docker run -d -h client.kv -v $KV_LIB:/kvlib:ro --cap-add=NET_ADMIN --cap-add=SYS_ADMIN --mac-address="22:44:66:88:02:00" --dns="172.17.0.100" --name=kvtest_client oracle-kvtest/ipchange-client client deploy 3 false

# Run client test
sleep 60 # wait for deploy to complete
docker exec kvtest_client python /sbin/entrypoint.py test


# Change IP address
for i in 0 1 2
do
    docker exec kvtest_server$i python /sbin/entrypoint.py flipip server$i
    docker exec kvtest_dns python /sbin/entrypoint.py flipdns server$i
done

# Test again
sleep 60
docker exec kvtest_client python /sbin/entrypoint.py test
