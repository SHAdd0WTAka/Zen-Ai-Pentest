FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy application
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host"]
