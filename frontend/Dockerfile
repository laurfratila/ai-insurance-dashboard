FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
# dev server; compose overrides with the same command
CMD ["npm","run","dev","--","--host"]
