# Base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy project files
COPY . .

# Expose port
EXPOSE 8080

# Run the development server
CMD ["npm", "run", "dev", "--", "--host"]
