# Multi-stage build for React Native Mobile App
FROM node:18-alpine as base

# Install dependencies
RUN apk add --no-cache git

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Install Expo CLI globally
RUN npm install -g @expo/cli

# Expose port
EXPOSE 19000 19001 19002

# Start the development server
CMD ["npx", "expo", "start", "--host", "lan"]
