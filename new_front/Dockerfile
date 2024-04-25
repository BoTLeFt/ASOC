FROM node:21-alpine as builder
WORKDIR /app
ADD new_front /app
RUN npm install
CMD ["npm", "start"]