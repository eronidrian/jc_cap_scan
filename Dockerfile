FROM ubuntu:22.04

# Install utilities and Java 8 (OpenJDK)
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        openjdk-8-jdk-headless \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Verify installation (optional)
RUN java -version
RUN apt-get update
RUN apt-get -y install ant



