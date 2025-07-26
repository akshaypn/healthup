FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application with error checking
RUN npm run build || (echo "Build failed! Check for TypeScript errors." && exit 1)

# Verify dist directory exists
RUN ls -la dist/ || (echo "dist directory not found after build!" && exit 1)

# Copy PWA assets to dist directory (only if they exist)
RUN if [ -f /app/public/icon-192.png ]; then \
        cp /app/public/icon-192.png /app/dist/ && echo "Copied icon-192.png"; \
    else \
        echo "Warning: icon-192.png not found in public directory"; \
    fi && \
    if [ -f /app/public/icon-512.png ]; then \
        cp /app/public/icon-512.png /app/dist/ && echo "Copied icon-512.png"; \
    else \
        echo "Warning: icon-512.png not found in public directory"; \
    fi

# Install serve for production
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Start the application
CMD ["serve", "-s", "dist", "-l", "3000"] 