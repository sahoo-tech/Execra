FROM node:20-alpine

WORKDIR /app

# Copy dependency configurations
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application source
COPY . .

# Expose Vite dev port
EXPOSE 5173

# Run Vite dev server bound to all interfaces for container access
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
