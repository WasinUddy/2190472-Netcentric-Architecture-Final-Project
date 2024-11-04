# Build React.JS Static Files
FROM node:16 AS build

WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker caching
COPY package.json package-lock.json ./

RUN npm install

# Copy the rest of the application code
COPY . .

# Build the React application
RUN npm run build

# Serve React.JS Static Files
FROM nginx:alpine

# Set working directory (this is not strictly necessary, as the next line will copy files to the nginx default directory)
WORKDIR /usr/share/nginx/html

# Copy built static files from the build stage
COPY --from=build /app/dist .

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy startup script
COPY start_up.sh /start_up.sh

# Make sure the startup script is executable
RUN chmod +x /start_up.sh

# Expose port 80
EXPOSE 80

# Run the startup script
CMD ["/bin/sh", "/start_up.sh"]
