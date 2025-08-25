FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with memory optimization
RUN npm ci --only=production --silent

# Copy source code
COPY . .

# Accept build arguments for environment variables
ARG REACT_APP_API_URL
ARG REACT_APP_WS_URL

# Set environment variables for the build
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_WS_URL=$REACT_APP_WS_URL
ENV NODE_OPTIONS="--max-old-space-size=256"
ENV GENERATE_SOURCEMAP=false

# Build the application with memory optimization
RUN npm run build

# Remove development dependencies and source files to save space
RUN rm -rf src public node_modules package*.json && \
    npm cache clean --force

# Install serve to run the production build
RUN npm install -g serve@14

# Expose port
EXPOSE 3000

# Start the application
CMD ["serve", "-s", "build", "-l", "3000", "--no-clipboard"]
