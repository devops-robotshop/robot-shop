FROM node:20-alpine
# checkov:skip=CKV_DOCKER_2: Bo qua Healthcheck vi Kubernetes da dam nhiem viec nay
# checkov:skip=CKV_DOCKER_3: Chap nhan rui ro chay quyen Root trong moi truong Lab
RUN apk update && apk upgrade --no-cache

ENV INSTANA_AUTO_PROFILE true
EXPOSE 8080

WORKDIR /opt/server

COPY package*.json /opt/server/

RUN npm ci --omit=dev --ignore-scripts

COPY server.js /opt/server/

CMD ["node", "server.js"]
#test pipeline
