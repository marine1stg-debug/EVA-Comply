# nginx reverse proxy with env-driven HTTP Basic Auth + no-index headers.
# 1.30.x receives current security fixes; the bare ":alpine" tag floats, so pin.
FROM nginx:1.30-alpine

# Patch Alpine OS packages (clears base-layer CVEs), then add:
#   apache2-utils → htpasswd ;  gettext → envsubst
RUN apk update && apk upgrade --no-cache \
    && apk add --no-cache apache2-utils gettext

COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY docker-entrypoint-eva.sh /docker-entrypoint-eva.sh
RUN chmod +x /docker-entrypoint-eva.sh

# Default for local docker-compose; Render injects its own $PORT.
EXPOSE 80

ENTRYPOINT ["/docker-entrypoint-eva.sh"]
