#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# EVA Comply nginx entrypoint
#   - Builds an htpasswd file from env vars (no secrets baked into the image)
#   - Enables site-wide HTTP Basic Auth unless BASIC_AUTH_DISABLED=true
#   - Renders nginx.conf from a template, substituting only our own variables
#     (so nginx's own $host / $remote_addr etc. are left untouched)
#   - Supports Render's injected $PORT
#
# Env vars:
#   BASIC_AUTH_USER       basic-auth username (required unless disabled)
#   BASIC_AUTH_PASSWORD   basic-auth password (required unless disabled)
#   BASIC_AUTH_DISABLED   "true" to run with NO auth (local dev only)
#   PORT                  port nginx listens on (Render sets this; default 80)
#   API_HOST              upstream API   host:port (default api:8000)
#   FRONTEND_HOST         upstream front host:port (default frontend:3000)
# ─────────────────────────────────────────────────────────────────────────────
set -eu

TEMPLATE=/etc/nginx/nginx.conf.template
CONF_OUT=/etc/nginx/nginx.conf
HTPASSWD=/etc/nginx/.htpasswd
AUTH_SNIPPET=/etc/nginx/auth_basic.conf

export NGINX_PORT="${PORT:-80}"
export API_HOST="${API_HOST:-api:8000}"
export FRONTEND_HOST="${FRONTEND_HOST:-frontend:3000}"

if [ "${BASIC_AUTH_DISABLED:-false}" = "true" ]; then
    echo "[eva-nginx] WARNING: BASIC_AUTH_DISABLED=true — running with NO basic auth"
    : > "$AUTH_SNIPPET"
else
    if [ -z "${BASIC_AUTH_USER:-}" ] || [ -z "${BASIC_AUTH_PASSWORD:-}" ]; then
        echo "[eva-nginx] FATAL: BASIC_AUTH_USER and BASIC_AUTH_PASSWORD must be set." >&2
        echo "[eva-nginx]        (Set BASIC_AUTH_DISABLED=true to intentionally run without auth.)" >&2
        exit 1
    fi
    # -b take password from CLI, -c create file, -B bcrypt
    htpasswd -cbB "$HTPASSWD" "$BASIC_AUTH_USER" "$BASIC_AUTH_PASSWORD" >/dev/null 2>&1
    cat > "$AUTH_SNIPPET" <<EOF
auth_basic "EVA Comply — restricted";
auth_basic_user_file $HTPASSWD;
EOF
    echo "[eva-nginx] basic auth ENABLED for user '$BASIC_AUTH_USER'"
fi

# Substitute ONLY our variables; leave nginx runtime vars ($host, etc.) intact.
envsubst '${NGINX_PORT} ${API_HOST} ${FRONTEND_HOST}' < "$TEMPLATE" > "$CONF_OUT"

echo "[eva-nginx] listening on ${NGINX_PORT}; api=${API_HOST} frontend=${FRONTEND_HOST}"
nginx -t -c "$CONF_OUT"
exec nginx -c "$CONF_OUT" -g 'daemon off;'
