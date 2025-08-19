#!/usr/bin/env bash
set -euo pipefail

# ========= 설정값 (환경변수로 오버라이드 가능) =========
ORG="${ORG:-kakao-tech-campus-2nd-step3}"  # Organization 이름
CSV_FILE="${1:-./members.csv}"             # 첫 번째 인자: CSV 경로
MAX_TEAM="${MAX_TEAM:-22}"                 # Team1 ~ Team${MAX_TEAM}
ADMIN_TEAM_NAME="${ADMIN_TEAM_NAME:-Admins}"  # 공용 Admin 팀 이름
DRY_RUN="${DRY_RUN:-false}"                # true면 실제 변경 없이 계획만 출력
# =====================================================

log()   { echo "[INFO] $*"; }
warn()  { echo "[WARN] $*" >&2; }
err()   { echo "[ERR ] $*"  >&2; }
die()   { err "$*"; exit 1; }

need()  { command -v "$1" >/dev/null 2>&1 || die "'$1' 가(이) 필요합니다."; }

# 의존 도구 체크
need gh
need awk
need tr
need sed
need jq

# gh 인증 체크
gh auth status -h github.com >/dev/null 2>&1 || die "먼저 'gh auth login' 해주세요. (Org Owner 권한 필요)"

# CSV 파일 체크
[[ -f "$CSV_FILE" ]] || die "CSV 파일을 찾을 수 없습니다: $CSV_FILE"

# CSV 로딩 (헤더 스킵, 공백 라인 제외)
mapfile -t ROWS < <(awk 'NR>1 && NF>0 {print}' "$CSV_FILE")
[[ "${#ROWS[@]}" -gt 0 ]] || die "CSV에 데이터가 없습니다. (헤더만 있거나 공백)"

# ---------- gh api 래퍼 (DRY_RUN 지원) ----------
call_api() {
  local method="$1"; shift
  local path="$1"; shift
  if [[ "$DRY_RUN" == "true" ]]; then
    log "[DRY-RUN] gh api -X $method $path $*"
    return 0
  fi
  gh api -X "$method" "$path" "$@"
}

# ---------- 팀 조회/생성 ----------
get_team_by_name() {
  local name="$1"
  gh api "/orgs/${ORG}/teams" --paginate --jq \
    ".[] | select(.name==\"${name}\") | {slug: .slug, id: .id}" 2>/dev/null || true
}

create_team_if_needed() {
  local name="$1"
  local found slug id

  found="$(get_team_by_name "$name")"
  if [[ -n "$found" ]]; then
    slug="$(jq -r '.slug' <<<"$found")"
    id="$(jq -r '.id'   <<<"$found")"
    log "팀 이미 존재: ${name} (slug=${slug}, id=${id})"
    echo "${slug},${id}"
    return 0
  fi

  log "팀 생성: ${name}"
  if [[ "$DRY_RUN" == "true" ]]; then
    local s="$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr -s ' ' '-' )"
    echo "${s},DUMMY_ID"
    return 0
  fi

  local created
  if ! created="$(gh api -X POST "/orgs/${ORG}/teams" -f "name=${name}" -f "privacy=closed")"; then
    warn "팀 생성 실패(이미 존재/권한 문제 가능): ${name}"
    found="$(get_team_by_name "$name")"
    [[ -n "$found" ]] || die "팀 정보를 확인할 수 없습니다: ${name}"
    slug="$(jq -r '.slug' <<<"$found")"
    id="$(jq -r '.id'   <<<"$found")"
    echo "${slug},${id}"
    return 0
  fi

  slug="$(jq -r '.slug' <<<"$created")"
  id="$(jq -r '.id'   <<<"$created")"
  log "팀 생성 완료: ${name} (slug=${slug}, id=${id})"
  echo "${slug},${id}"
}

# ---------- 레포 생성 ----------
create_repo_if_needed() {
  local repo_full="$1"   # ORG/RepoName
  if gh api "/repos/${repo_full}" >/dev/null 2>&1; then
    log "레포 이미 존재: ${repo_full}"
    return 0
  fi
  log "레포 생성(public): ${repo_full}"
  if [[ "$DRY_RUN" == "true" ]]; then
    log "[DRY-RUN] gh repo create ${repo_full} --public"
    return 0
  fi
  gh repo create "${repo_full}" --public >/dev/null
}

# ---------- 팀-레포 권한 부여 ----------
grant_team_repo_permission() {
  local team_slug="$1"    # team slug
  local repo_name="$2"    # RepoName (ORG/ 제외)
  local perm="${3:-push}" # 기본 push
  log "팀 권한 부여: team=${team_slug} -> repo=${ORG}/${repo_name} (${perm})"
  call_api PUT "/orgs/${ORG}/teams/${team_slug}/repos/${ORG}/${repo_name}" -f "permission=${perm}" >/dev/null
}

# ---------- 이메일 초대 (여러 팀 동시 배정) ----------
invite_email_with_teams() {
  local email="$1"; shift
  local team_ids=( "$@" )
  log "Org 초대(이메일): ${email} (team_ids=${team_ids[*]})"

  if [[ "$DRY_RUN" == "true" ]]; then
    log "[DRY-RUN] gh api -X POST /orgs/${ORG}/invitations -f email=${email} -f role=direct_member $(printf ' -F team_ids[]=%s' "${team_ids[@]}")"
    return 0
  fi

  local args=( -f "email=${email}" -f "role=direct_member" )
  for tid in "${team_ids[@]}"; do args+=( -F "team_ids[]=${tid}" ); done

  gh api -X POST "/orgs/${ORG}/invitations" "${args[@]}" >/dev/null || {
    # 이미 멤버/이미 초대됨 등으로 실패 가능 → 경고만
    warn "초대 실패/중복 가능: ${email}"
  }
}

# ========== 1) 팀 생성 (공용 Admin 팀 + Team1~N) ==========
log "== 1) 팀 생성 시작 (공용 Admin 팀 + Team1 ~ Team${MAX_TEAM}) =="
ADMIN_PAIR="$(create_team_if_needed "${ADMIN_TEAM_NAME}")"  # "slug,id"
ADMIN_TEAM_SLUG="${ADMIN_PAIR%%,*}"
ADMIN_TEAM_ID="${ADMIN_PAIR##*,}"
[[ -n "$ADMIN_TEAM_SLUG" && -n "$ADMIN_TEAM_ID" ]] || die "공용 Admin 팀 생성/조회 실패: ${ADMIN_TEAM_NAME}"
log "공용 Admin 팀 준비 완료: ${ADMIN_TEAM_NAME} (slug=${ADMIN_TEAM_SLUG}, id=${ADMIN_TEAM_ID})"

declare -A TEAM_SLUG_BY_NO
declare -A TEAM_ID_BY_NO

for ((i=1; i<=MAX_TEAM; i++)); do
  team_name="Team${i}"
  pair="$(create_team_if_needed "$team_name")"   # "slug,id"
  team_slug="${pair%%,*}"
  team_id="${pair##*,}"
  TEAM_SLUG_BY_NO["$i"]="$team_slug"
  TEAM_ID_BY_NO["$i"]="$team_id"
done
log "== 1) 완료 =="

# ========== 2) 이메일 Org 초대 + 기본팀 & Admin팀 동시 배정 ==========
log "== 2) 이메일 Org 초대 + 팀 자동 배정 시작 =="
for line in "${ROWS[@]}"; do
  clean="$(echo "$line" | tr -d '[:space:]')"
  IFS=',' read -r team_no email <<<"$clean"
  [[ -n "${team_no:-}" && -n "${email:-}" ]] || { warn "잘못된 행: $line"; continue; }

  if ! [[ "$team_no" =~ ^[0-9]+$ ]] || (( team_no < 1 || team_no > MAX_TEAM )); then
    warn "팀번호 범위 오류(1..${MAX_TEAM}): '$team_no' (행: $line)"
    continue
  fi

  tid="${TEAM_ID_BY_NO[$team_no]}"
  if [[ -z "$tid" || "$tid" == "DUMMY_ID" ]]; then
    warn "팀 ID 조회 실패(행: $line)"
    continue
  fi

  # 요구사항: 모든 이메일을 기본팀 + 공용 Admin 팀에 함께 배정
  invite_email_with_teams "$email" "$tid" "$ADMIN_TEAM_ID"
done
log "== 2) 완료 =="

# ========== 3) 레포 생성 (public) ==========
log "== 3) 레포 생성 시작 (public: TeamX_BE / TeamX_FE) =="
for ((i=1; i<=MAX_TEAM; i++)); do
  create_repo_if_needed "${ORG}/Team${i}_BE"
  create_repo_if_needed "${ORG}/Team${i}_FE"
done
log "== 3) 완료 =="

# ========== 4) 팀-레포 권한 연결 (기본팀=push, Admin팀=admin) ==========
log "== 4) 팀-레포 권한 연결 시작 (기본팀=push, Admin팀=admin) =="
for ((i=1; i<=MAX_TEAM; i++)); do
  slug="${TEAM_SLUG_BY_NO[$i]}"
  [[ -n "$slug" && "$slug" != "null" ]] || { warn "팀 slug 없음: Team${i}"; continue; }

  # 기본 팀 → push
  grant_team_repo_permission "$slug" "Team${i}_BE" "push"
  grant_team_repo_permission "$slug" "Team${i}_FE" "push"

  # 공용 Admin 팀 → admin (모든 레포)
  grant_team_repo_permission "$ADMIN_TEAM_SLUG" "Team${i}_BE" "admin"
  grant_team_repo_permission "$ADMIN_TEAM_SLUG" "Team${i}_FE" "admin"
done
log "== 4) 완료 =="

log "🎉 모든 작업이 완료되었습니다."
