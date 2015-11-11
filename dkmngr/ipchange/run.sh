sh cleanup.sh
sh runtest.sh 2>&1 | tee /tmp/kvtest_ipchange.log
python checkfail.py /tmp/kvtest_ipchange.log
sh cleanup.sh
