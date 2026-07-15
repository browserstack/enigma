#!/usr/bin/env bash
#
# Create local secret env files (secrets/*.env) from their committed
# *.env.sample templates. Idempotent: existing files are left untouched.
#
# Secrets are gitignored, so a fresh clone / CI runner has only the samples.
# Running `make dev` (or build/test) without the real files fails with
# "env file ... not found". This script bootstraps them for local dev.
#
# Coupling: MYSQL_ROOT_PASSWORD must be identical in ops_mysql_dev.env and
# ops_app_celery.env or the app/celery containers cannot auth to MySQL.
# We generate the password once and reuse it (and reuse an existing one if
# only some files are present) to keep them in sync.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_DIR="$(cd "${SCRIPT_DIR}/../secrets" && pwd)"

randstr() { LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c "$1"; }

# Extract a KEY=value from a file, or empty string if absent.
readval() {
  local key="$1" file="$2"
  [ -f "$file" ] && sed -n "s/^${key}=//p" "$file" | head -n1 || true
}

# Precedence: env override (CI/deterministic) > existing file (stay consistent
# with an already-initialised MySQL volume) > freshly generated random value.
PW="${MYSQL_ROOT_PASSWORD:-}"
[ -n "$PW" ] || PW="$(readval MYSQL_ROOT_PASSWORD "${SECRETS_DIR}/ops_mysql_dev.env")"
[ -n "$PW" ] || PW="$(readval MYSQL_ROOT_PASSWORD "${SECRETS_DIR}/ops_app_celery.env")"
[ -n "$PW" ] || PW="$(randstr 24)"

TOKEN="${APP_TOKEN:-}"
[ -n "$TOKEN" ] || TOKEN="$(readval TOKEN "${SECRETS_DIR}/ops_app_dev.env")"
[ -n "$TOKEN" ] || TOKEN="$(readval TOKEN "${SECRETS_DIR}/ops_app_test.env")"
[ -n "$TOKEN" ] || TOKEN="$(randstr 32)"

created=0
gen() {
  local out="$1"; shift
  if [ -f "${SECRETS_DIR}/${out}" ]; then
    return 0
  fi
  # Remaining args: sed substitution expressions.
  local sed_args=()
  for expr in "$@"; do sed_args+=(-e "$expr"); done
  sed "${sed_args[@]}" "${SECRETS_DIR}/${out}.sample" > "${SECRETS_DIR}/${out}"
  echo "  created secrets/${out}"
  created=1
}

gen ops_mysql_dev.env   "s|__CHANGE_ME__|${PW}|g"
gen ops_app_celery.env  "s|__CHANGE_ME__|${PW}|g"
gen ops_app_dev.env     "s|__CHANGE_ME__|${TOKEN}|g"
gen ops_app_test.env    "s|__CHANGE_ME__|${TOKEN}|g"

if [ "$created" -eq 1 ]; then
  echo "Local secret env files ready. These are gitignored — edit values as needed."
else
  echo "Secret env files already present — nothing to do."
fi
