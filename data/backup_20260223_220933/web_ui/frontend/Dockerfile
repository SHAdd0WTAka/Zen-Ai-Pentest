FROM node:20-alpine

WORKDIR /app

# Accept build argument for API URL
ARG REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Install dependencies first (better caching)
COPY package*.json ./
RUN npm ci --legacy-peer-deps

# Install serve for production
RUN npm install -g serve

# Copy app source
COPY . .

# Build the app with API URL
RUN npm run build

# Expose port
EXPOSE 3000

# Start production server
CMD ["serve", "-s", "build", "-l", "3000"]
