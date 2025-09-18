# Multi-stage build for Flutter web app
FROM ubuntu:20.04 as base

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    xz-utils \
    zip \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Install Flutter
ENV FLUTTER_VERSION=3.16.0
RUN git clone https://github.com/flutter/flutter.git -b stable /flutter
ENV PATH="/flutter/bin:/flutter/bin/cache/dart-sdk/bin:${PATH}"

# Enable Flutter web
RUN flutter config --enable-web

# Set working directory
WORKDIR /app

# Copy pubspec files
COPY pubspec.yaml ./

# Get dependencies
RUN flutter pub get

# Copy source code
COPY . .

# Build for web
RUN flutter build web --release

# Production stage
FROM nginx:alpine

# Copy built app to nginx
COPY --from=base /app/build/web /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
