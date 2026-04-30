FROM node:20-alpine

RUN apk update && apk upgrade --no-cache

ENV INSTANA_AUTO_PROFILE true
EXPOSE 8080
WORKDIR /opt/server

RUN chown -R node:node /opt/server

COPY --chown=node:node package*.json /opt/server/

RUN npm ci --omit=dev --ignore-scripts

COPY --chown=node:node server.js /opt/server/

USER node

HEALTHCHECK --interval=30s --timeout=3s CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

CMD ["node", "server.js"]
#test