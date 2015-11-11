FROM ubuntu:14.04

ENV http_proxy http://www-proxy.us.oracle.com:80/
ENV https_proxy http://www-proxy.us.oracle.com:80/
RUN echo "Acquire::http::Proxy \"http://www-proxy.us.oracle.com:80/\";" > /etc/apt/apt.conf

RUN apt-get update && apt-get install -y bind9 openjdk-7-jdk host

COPY entrypoint.py /sbin/entrypoint.py

ENTRYPOINT ["python", "/sbin/entrypoint.py", "dns"]
