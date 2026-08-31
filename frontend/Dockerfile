FROM node:16.20.2-alpine3.18 AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.29.1-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/ffe-opening-coach-ui /usr/share/nginx/html
EXPOSE 80
