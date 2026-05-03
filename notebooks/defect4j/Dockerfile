FROM ubuntu:20.04

MAINTAINER ngocpq <phungquangngoc@gmail.com>

#############################################################################
# Requirements
#############################################################################

RUN \
  apt-get update -y && \
  apt-get install software-properties-common -y && \
  apt-get update -y && \
  apt-get install -y openjdk-11-jdk \
                maven \
                git \
                build-essential \
                subversion \
                perl \
                curl \
                unzip \
                cpanminus \
                make \
                && \
  rm -rf /var/lib/apt/lists/*

# Detect the installed JDK path at build time (works on both amd64 and arm64)
# and write JAVA_HOME to the system profile so that every `bash -lc` invocation
# (including Defects4J's exec wrapper) inherits the correct value automatically.
RUN JAVA_HOME=$(find /usr/lib/jvm -maxdepth 1 -name "java-11-openjdk-*" -type d \
                | sort | head -1) && \
    echo "export JAVA_HOME=${JAVA_HOME}"         >  /etc/profile.d/java_home.sh && \
    echo 'export PATH="${JAVA_HOME}/bin:${PATH}"' >> /etc/profile.d/java_home.sh && \
    chmod +x /etc/profile.d/java_home.sh

# Timezone
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#############################################################################
# PIT standalone CLI
# Version must match `pit_version` in defect4j/generators/base.py → PITConfig
#############################################################################

ARG PIT_VERSION=1.17.0

# Resolve ALL transitive dependencies of pitest-command-line and pitest-entry
# All transitive deps (ASM, etc.) are included automatically.
RUN . /etc/profile.d/java_home.sh && \
    mkdir -p /tmp/pit-dl /opt/pit-cli && \
    { echo '<?xml version="1.0"?>'; \
      echo "<project><modelVersion>4.0.0</modelVersion>"; \
      echo "<groupId>dl</groupId><artifactId>pit-dl</artifactId><version>1</version>"; \
      echo "<dependencies>"; \
      echo "  <dependency><groupId>org.pitest</groupId>"; \
      echo "    <artifactId>pitest-command-line</artifactId>"; \
      echo "    <version>${PIT_VERSION}</version></dependency>"; \
      echo "  <dependency><groupId>org.pitest</groupId>"; \
      echo "    <artifactId>pitest-entry</artifactId>"; \
      echo "    <version>${PIT_VERSION}</version></dependency>"; \
      echo "</dependencies></project>"; \
    } > /tmp/pit-dl/pom.xml && \
    cd /tmp/pit-dl && \
    mvn -q dependency:copy-dependencies -DoutputDirectory=/opt/pit-cli && \
    rm -rf /tmp/pit-dl

# Pre-compute the PIT CLI classpath string and store it in the profile.
# This avoids runtime shell glob expansion issues and makes the classpath
# immediately available as $PIT_CLI_CP in any bash -lc invocation.
RUN PIT_CP=$(ls /opt/pit-cli/*.jar | tr '\n' ':' | sed 's/:$//') && \
    echo "export PIT_CLI_CP=${PIT_CP}" >> /etc/profile.d/java_home.sh

#############################################################################
# Setup Defects4J
#############################################################################

# ----------- Step 1. Clone defects4j from github --------------
WORKDIR /
RUN git clone https://github.com/rjust/defects4j.git defects4j

# ----------- Step 2. Initialize Defects4J ---------------------
WORKDIR /defects4j
RUN cpanm --installdeps .
RUN ./init.sh

# ----------- Step 3. Add Defects4J's executables to PATH ------
ENV PATH="/defects4j/framework/bin:${PATH}"
