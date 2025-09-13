ff_auth_header() {
  local f="/opt/feature-factory/secrets/ops_basic_auth.b64"
  if [ -f "$f" ]; then
    echo "Authorization: Basic $(cat "$f")"
  elif [ -n "$BASIC_AUTH_USER" ] && [ -n "$BASIC_AUTH_PASS" ]; then
    echo "Authorization: Basic $(printf '%s:%s' "$BASIC_AUTH_USER" "$BASIC_AUTH_PASS" | base64)"
  else
    echo ""; return 1
  fi
}
ff_find_context_file() {
  for p in \
    "/opt/feature-factory/cortex/runtime/ff-context.json" \
    "/opt/feature-factory/.well-known/ff-context.json"; do
    [ -f "$p" ] && echo "$p" && return 0
  done
  return 1
}
ff_bootstrap() {
  local file; file=$(ff_find_context_file) || true
  if [ -n "$file" ]; then
    FF_PUBLIC_BASE=$(jq -r '.public_base // .envs.test.public_base // empty' "$file")
    FF_API_BASE=$(jq -r '.api_base // .envs.test.api_base // empty' "$file")
  fi
  [ -z "$FF_PUBLIC_BASE" ] && FF_PUBLIC_BASE=${FF_PUBLIC_BASE:-"https://etl-tst.chococraft.ru"}
  [ -z "$FF_API_BASE" ]   && FF_API_BASE=${FF_API_BASE:-"https://etl-tst.chococraft.ru/api/v1"}
  export FF_PUBLIC_BASE FF_API_BASE
}
