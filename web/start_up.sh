#!/bin/sh

# Replace the placeholder WS_URL in the index.html with the environment variable WS_URL
sed -i "s|window.WS_URL = \"ws://localhost:1000\";|window.WS_URL = \"${WS_URL}\";|" /usr/share/nginx/html/index.html

# Start Nginx
nginx -g 'daemon off;'
