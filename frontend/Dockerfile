FROM node:20-alpine

WORKDIR /app

# Copy package files if they exist
COPY package.json* package-lock.json* ./

# Install dependencies if package.json exists
RUN if [ -f package.json ]; then npm install; else echo "No package.json found, skipping dependency installation"; fi

# Copy application files
COPY . .

# Expose frontend port
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start the development server
CMD ["npm", "run", "dev"]
