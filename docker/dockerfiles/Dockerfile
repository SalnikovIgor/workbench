FROM ${BASE_IMAGE}

# rewrite BASE_IMAGE SHELL
# too much output for us with -x option
SHELL ["/bin/bash", "+x", "-c"]

USER root

ENV OPENVINO_IMAGE ${BASE_IMAGE}

ENV DEBIAN_FRONTEND noninteractive
ENV ACCURACY_CHECKER_LOG_LEVEL ERROR

ARG db_password
ARG rabbitmq_password
ARG google_analytics_id
ARG PACKAGE_LINK
ARG WHEELS_LINK
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ARG CI_USER

ENV PACKAGE_LINK ${PACKAGE_LINK}
ENV DB_PASSWORD $db_password
ENV DB_USER workbench
ENV DB_NAME workbench
ENV GOOGLE_ANALYTICS_ID ${google_analytics_id}

ENV RABBITMQ_PASSWORD $rabbitmq_password


ENV USER_NAME ${CI_USER}
ENV TEMP_DIR /tmp/${USER_NAME}_installer
ENV NVM_DIR /home/${USER_NAME}/.nvm

ENV http_proxy ${HTTP_PROXY}
ENV https_proxy ${HTTPS_PROXY}
ENV no_proxy ${NO_PROXY}

ENV OPENVINO_WORKBENCH_ROOT ${INTEL_OPENVINO_DIR}/tools/workbench
ENV WHEELS_PATH ${OPENVINO_WORKBENCH_ROOT}/wheels
ENV WORKBENCH_FE_DIR ${OPENVINO_WORKBENCH_ROOT}/client
ENV OPENVINO_WORKBENCH_DATA_PATH ${OPENVINO_WORKBENCH_ROOT}/wb/data

ENV TZ Europe/Helsinki

ENV PYTHONPATH ${PYTHONPATH}:\
${OPENVINO_WORKBENCH_ROOT}:\
${OPENVINO_WORKBENCH_ROOT}/model_analyzer:\
${INTEL_OPENVINO_DIR}/tools/benchmark_tool

ENV NOTEBOOKS_VENV /tmp/jupyter_env

RUN useradd -ms /bin/bash -u 28895 ${USER_NAME} && \
    chown ${USER_NAME} -R /home/${USER_NAME}

# CREATE DIRECTORY FOR PUBLIC WORKBENCH ARTIFACTS
ENV WORKBENCH_PUBLIC_DIR /home/${USER_NAME}/.workbench
RUN mkdir -m 777 -p ${WORKBENCH_PUBLIC_DIR} && chown -R ${USER_NAME} ${WORKBENCH_PUBLIC_DIR}

RUN apt update && \
    apt install -y --no-install-recommends \
    unzip \
    erlang-nox \
    default-jre \
    rabbitmq-server \
    firefox \
    software-properties-common \
    python3 \
    python3-pip \
    python3-setuptools \
    python3-dev \
    nginx \
    libsm6 \
    # for envsubst
    gettext-base \
    libboost-filesystem-dev \
    libboost-thread-dev \
    libjson-c4 \
    libxxf86vm-dev \
    # For free sockets searching (ss tool)
    iproute2 \
    # For E2E in non-headless mode
    xvfb \
    gnupg2 \
    build-essential && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# For postgresql-10
RUN curl -L https://www.postgresql.org/media/keys/ACCC4CF8.asc -s | apt-key add - && \
    echo "deb [arch=amd64] http://apt.postgresql.org/pub/repos/apt/ focal-pgdg main" | tee /etc/apt/sources.list.d/postgresql.list
# For E2E with Google Chrome
RUN curl -L  https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" | tee -a /etc/apt/sources.list.d/google-chrome.list

RUN apt update && \
    apt install -y --no-install-recommends \
    postgresql-10 \
    google-chrome-stable && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install pip==19.3.1

USER postgres

RUN service postgresql start && \
    psql --command "CREATE USER ${DB_USER}  WITH SUPERUSER PASSWORD '${DB_PASSWORD}';" && \
    service postgresql stop

USER root

# Add the ${USER_NAME} user to groups:
# 1. Add ${USER_NAME} to groups of rabbitmq and postgres for running
#    this services without sudo
# 2. Add ${USER_NAME} to adm group for run Nginx as ${USER_NAME} user
RUN gpasswd -a ${USER_NAME} ssl-cert && \
    for g in $(id -nG postgres); do gpasswd -a ${USER_NAME} ${g}; done && \
    for g in $(id -nG rabbitmq); do gpasswd -a ${USER_NAME} ${g}; done && \
    gpasswd -a ${USER_NAME} users && \
    gpasswd -a ${USER_NAME} video && \
    gpasswd -a ${USER_NAME} adm

RUN rm -rf /etc/nginx/sites-enabled/default && \
    touch /var/run/nginx.pid

RUN chown -R ${USER_NAME} /var/lib/postgresql /var/run/postgresql /etc/postgresql \
                          /var/lib/rabbitmq /var/log/rabbitmq /var/log/rabbitmq \
                          /var/log/nginx /var/lib/nginx /var/run/nginx.pid \
                          /etc/nginx/sites-enabled /etc/nginx/snippets

RUN mkdir -p ${NVM_DIR} && \
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.37.0/install.sh | bash && \
    chown ${USER_NAME} -R ${NVM_DIR} && \
    . ${NVM_DIR}/nvm.sh && \
    nvm install v14 && \
    nvm use v14 && \
    npm install -g npm@7.22.0 && \
    npm config set proxy ${http_proxy} && \
    npm config set https-proxy ${https_proxy}

# install jenkins jnlp agent for kubernetes
ARG VERSION=3.36

RUN curl --create-dirs -sSLo /usr/share/jenkins/agent.jar https://repo.jenkins-ci.org/public/org/jenkins-ci/main/remoting/${VERSION}/remoting-${VERSION}.jar && \
    chmod 755 /usr/share/jenkins && \
    chmod 644 /usr/share/jenkins/agent.jar && \
    ln -sf /usr/share/jenkins/agent.jar /usr/share/jenkins/slave.jar && \
    curl --create-dirs -sSLo /tools/jenkins-agent https://raw.githubusercontent.com/jenkinsci/docker-jnlp-slave/3.35-5/jenkins-agent && \
    chmod +x /tools/jenkins-agent && \
    mkdir -p /home/${USER_NAME}/.jenkins/cache/jars && \
    chmod 775 -R /home/${USER_NAME} && \
    chown ${USER_NAME} -R /home/${USER_NAME} && \
    chown ${USER_NAME} -R /tools

# Install internal Intel SHA and SHA2 SSL certificates chain
COPY tools /tools/
RUN /tools/install_internal_ssl_chain.sh && \
    echo "NTP=corp.intel.com" >> /etc/systemd/timesyncd.conf

# Add internal Intel SSL certificates to Java chain
RUN find /usr/local/share/ca-certificates/ -exec sh -c 'keytool -import -alias $(basename $1) -keystore \
     /usr/lib/jvm/java-8-openjdk-amd64/jre/lib/security/cacerts \
     -storepass changeit  \
     -noprompt \
     -trustcacerts -file $1' _ {} \;

RUN rm -rf ${OPENVINO_WORKBENCH_ROOT}/*

RUN rm -rf ${OPENVINO_WORKBENCH_ROOT} && \
    mkdir -p ${OPENVINO_WORKBENCH_ROOT}/model_analyzer && \
    mkdir -p ${OPENVINO_WORKBENCH_ROOT}/client && \
    mkdir -p ${OPENVINO_WORKBENCH_DATA_PATH} && \
    mkdir -p ${OPENVINO_WORKBENCH_DATA_PATH}/artifacts

# Copy only files with requirements and install them before copying all code for speed up the docker build process
COPY --chown=${USER_NAME} requirements/requirements.txt ${OPENVINO_WORKBENCH_ROOT}/requirements/
COPY --chown=${USER_NAME} requirements/requirements_jupyter.txt ${OPENVINO_WORKBENCH_ROOT}/requirements/
COPY --chown=${USER_NAME} requirements/requirements_dev.txt ${OPENVINO_WORKBENCH_ROOT}/requirements/
COPY --chown=${USER_NAME} model_analyzer/requirements.txt ${OPENVINO_WORKBENCH_ROOT}/model_analyzer/
COPY --chown=${USER_NAME} client/package.json ${OPENVINO_WORKBENCH_ROOT}/client/
COPY --chown=${USER_NAME} client/package-lock.json ${OPENVINO_WORKBENCH_ROOT}/client/
COPY --chown=root nginx/nginx.conf /etc/nginx/nginx.conf

RUN python3 -m pip install --no-cache-dir --proxy=${https_proxy} -r ${OPENVINO_WORKBENCH_ROOT}/requirements/requirements.txt && \
    python3 -m pip install --no-cache-dir --proxy=${https_proxy} -r ${OPENVINO_WORKBENCH_ROOT}/requirements/requirements_jupyter.txt && \
    python3 -m pip install --no-cache-dir --proxy=${https_proxy} -r ${OPENVINO_WORKBENCH_ROOT}/requirements/requirements_dev.txt && \
    python3 -m pip install --no-cache-dir --proxy=${https_proxy} -r ${OPENVINO_WORKBENCH_ROOT}/model_analyzer/requirements.txt

RUN chown -R ${USER_NAME} ${OPENVINO_WORKBENCH_ROOT}

USER ${USER_NAME}

WORKDIR ${OPENVINO_WORKBENCH_ROOT}/client

RUN . ${NVM_DIR}/nvm.sh && \
    npm install

COPY --chown=${USER_NAME} . ${OPENVINO_WORKBENCH_ROOT}/

RUN . ${NVM_DIR}/nvm.sh && \
    npm run init-netron && \
    DL_PROFILER_BACKEND_STATIC_PATH=${OPENVINO_WORKBENCH_ROOT}/static/ npm run pack

WORKDIR ${OPENVINO_WORKBENCH_ROOT}

RUN python3 ${OPENVINO_WORKBENCH_ROOT}/wb/main/utils/bundle_creator/bundle_downloader.py \
                        --link "${PACKAGE_LINK}" \
                        -os ubuntu18 ubuntu20 \
                        --output-path "${OPENVINO_WORKBENCH_ROOT}/bundles" \
                        --targets cpu gpu hddl opencv python3.6 python3.7 python3.8 vpu

RUN python3 ${OPENVINO_WORKBENCH_ROOT}/wb/main/utils/wheel_downloader.py \
                        --link ${WHEELS_LINK} \
                        --output-path ${WHEELS_PATH}

# install jenkins jnlp agent

ENTRYPOINT ["/tools/jenkins-agent"]
