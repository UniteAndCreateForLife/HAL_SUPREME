FROM node:22-alpine

WORKDIR /app

COPY --chown=node:node package.json ./
RUN npm install --omit=dev --ignore-scripts && npm cache clean --force

COPY --chown=node:node . .

ENV NODE_ENV=production
ENV PORT=8787

USER node
EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD wget -qO- "http://127.0.0.1:${PORT}/api/health" | grep -q '"ok":true' || exit 1

CMD ["npm", "start"]
