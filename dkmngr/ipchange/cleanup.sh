docker stop kvtest_dns
docker rm kvtest_dns
for i in 0 1 2
do
    docker stop kvtest_server$i
    docker rm kvtest_server$i
done
docker stop kvtest_client
docker rm kvtest_client
