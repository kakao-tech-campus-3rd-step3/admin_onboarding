# GitHub Organization 온보딩 자동화 스크립트

GitHub Organization에서 팀 생성, 멤버 초대, 레포지토리 생성 및 권한 설정을 자동화하는 Bash 스크립트입니다.

## 주요 기능

1. **팀 생성**: CSV 파일 기반으로 필요한 팀들 자동 생성 (Team5, Team6, ...)
2. **멤버 초대**: 이메일로 Organization 멤버 초대 및 해당 팀에 배정
3. **레포지토리 생성**: 각 팀별로 백엔드/프론트엔드 레포 생성 (TeamX_BE, TeamX_FE)
4. **권한 설정**: 팀과 레포지토리 간 권한 연결 (팀=push, Admin팀=admin)
5. **Admin 팀 관리**: 모든 멤버를 Admin 팀에도 동시 배정하여 전체 레포 관리 권한 부여
6. **자동 권한 관리**: GitHub CLI 인증 상태 및 Organization 관리 권한 자동 확인 및 갱신

## 필요한 프로그램

스크립트는 실행 시 자동으로 필요한 프로그램들을 체크하고, 미설치 시 상세한 설치 가이드를 제공합니다.

### 필수 프로그램
- **GitHub CLI (gh)**: GitHub API 호출용
  - macOS: `brew install gh`
  - Ubuntu/Debian: `sudo apt install gh`
  - 기타: https://cli.github.com/

- **jq**: JSON 파싱용
  - macOS: `brew install jq`
  - Ubuntu/Debian: `sudo apt install jq`
  - 기타: https://jqlang.github.io/jq/

- **기본 유틸리티**: `awk`, `tr`, `sed` (대부분 시스템에 기본 설치됨)

## 사전 준비

### 1. GitHub CLI 인증
```bash
gh auth login
```

**중요**: 스크립트는 Organization 관리 권한(`admin:org`)이 필요한지 자동으로 확인하고, 필요시 다음 명령을 자동 실행합니다:
```bash
gh auth refresh -h github.com -s admin:org
```

- Organization Owner 권한이 필요합니다
- 권한이 부족한 경우 스크립트가 자동으로 권한 갱신을 시도합니다
- 자동 갱신 실패 시 수동 해결 방법을 안내합니다

### 2. CSV 파일 준비 (`members.csv`)
```csv
team_no,email
5,user1@example.com
6,user2@example.com
7,user3@example.com
```

## 사용법

### 기본 실행
```bash
./onboard_admin.sh
```
- 현재 디렉토리의 `members.csv` 파일을 사용합니다.
- 자동으로 필요한 프로그램과 권한을 체크합니다.

### CSV 파일 경로 지정
```bash
./onboard_admin.sh /path/to/your/members.csv
```

### 드라이런 모드 (실제 변경 없이 계획만 확인)
```bash
DRY_RUN=true ./onboard_admin.sh
```

### 환경변수 설정
```bash
ORG="your-org-name" ADMIN_TEAM_NAME="Administrators" ./onboard_admin.sh
```

## 환경변수 옵션

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `ORG` | `kakao-tech-campus-3rd-step3` | GitHub Organization 이름 |
| `ADMIN_TEAM_NAME` | `Admins` | 관리자 팀 이름 |
| `DRY_RUN` | `false` | `true`시 실제 변경 없이 계획만 출력 |

## 실행 과정

스크립트는 다음과 같은 단계로 진행됩니다:

### 사전 체크 단계
- **필수 프로그램 확인**: gh, jq, awk, tr, sed 설치 상태 확인
- **GitHub CLI 인증 확인**: 로그인 상태 및 API 접근 권한 확인
- **Organization 접근 권한 확인**: 대상 Organization에 대한 관리 권한 확인
- **자동 권한 갱신**: 필요시 `admin:org` 스코프로 권한 자동 갱신
- **CSV 파일 검증**: 파일 존재 및 유효한 데이터 확인

### 1단계: 팀 생성
- CSV에서 발견된 팀 번호를 기반으로 팀 생성 (예: Team5, Team6, Team7...)
- 공용 Admin 팀 생성 (기본: "Admins")

### 2단계: 멤버 초대
- CSV의 각 이메일을 Organization에 초대
- 해당 팀과 Admin 팀에 동시 배정 (admin 권한으로)

### 3단계: 레포지토리 생성
- 각 팀별로 백엔드/프론트엔드 레포 생성
- 형식: `TeamX_BE`, `TeamX_FE` (public 레포)

### 4단계: 권한 설정
- 각 팀 → 해당 레포에 push 권한
- Admin 팀 → 모든 레포에 admin 권한

## CSV 파일 형식

```csv
team_no,email
5,developer1@example.com
6,developer2@example.com
7,developer3@example.com
```

**주의사항:**
- 첫 번째 줄은 헤더로 처리됩니다
- 팀 번호는 숫자만 가능합니다
- 이메일 주소는 유효한 형식이어야 합니다
- CSV에 있는 팀 번호만 생성됩니다 (고정 범위 없음)

## 생성되는 리소스

### 팀 (Teams)
- `Team5`, `Team6`, `Team7`... (CSV 기반)
- `Admins` (모든 멤버 포함)

### 레포지토리 (Repositories)
- `kakao-tech-campus-3rd-step3/Team5_BE`
- `kakao-tech-campus-3rd-step3/Team5_FE`
- `kakao-tech-campus-3rd-step3/Team6_BE`
- `kakao-tech-campus-3rd-step3/Team6_FE`
- ...

### 권한 (Permissions)
- 각 팀: 해당 팀의 BE/FE 레포에 **push** 권한
- Admin 팀: 모든 레포에 **admin** 권한
- 모든 멤버: Organization **admin** 권한

## 오류 해결

### 권한 관련 오류

1. **"GitHub CLI 인증이 필요합니다"**
   - 해결: `gh auth login` 실행

2. **"Organization 관리 권한이 없습니다"**
   - 스크립트가 자동으로 `gh auth refresh -h github.com -s admin:org` 실행
   - 자동 갱신 실패 시 수동 실행 가이드 제공

3. **"Organization Owner 권한이 필요합니다"**
   - GitHub 웹사이트에서 Organization Owner 권한 확인 필요
   - Organization 설정에서 멤버 권한 확인

### 일반적인 오류들

1. **"필수 프로그램이 설치되지 않았습니다"**
   - 스크립트가 자동으로 설치 가이드 출력
   - 플랫폼별 설치 명령어 제공

2. **초대 실패**
   - 이미 멤버이거나 초대가 중복된 경우
   - 경고로 처리되며 스크립트 계속 진행

3. **CSV 파일 오류**
   - 파일 경로, 형식, 데이터 유효성 자동 확인
   - 상세한 오류 메시지 제공

### 로그 확인
스크립트는 상세한 로그를 출력하므로 오류 발생 시 해당 단계를 확인할 수 있습니다:
- `[INFO]`: 정상 진행 정보
- `[WARN]`: 경고 (스크립트 계속 진행)
- `[ERR ]`: 오류 (스크립트 중단)

## 주의사항

1. **백업**: 실행 전 중요한 설정 백업 권장
2. **권한 확인**: Organization Owner 권한 필수
3. **테스트**: 첫 실행 시 `DRY_RUN=true`로 테스트 권장
4. **멱등성**: 스크립트는 여러 번 실행해도 안전함 (이미 존재하는 리소스는 건너뜀)
5. **CSV 검증**: 잘못된 형식의 데이터는 경고 후 건너뜀
6. **자동 권한 관리**: 스크립트가 필요한 권한을 자동으로 확인하고 갱신 시도

## 실행 예시

```bash
# 기본 실행
./onboard_admin.sh

# 출력 예시:
[INFO] GitHub CLI 인증 상태 확인 중...
[INFO] Organization 관리 권한 확인 중...
[INFO] Organization 'kakao-tech-campus-3rd-step3' 접근 권한 확인 중...
[INFO] GitHub CLI 인증 및 권한 확인 완료
[INFO] CSV에서 발견된 팀 번호: 5 6 7 8 9 10 11 12 13 14
[INFO] == 1) 팀 생성 시작 ==
[INFO] 팀 생성: Admins
[INFO] 팀 생성 완료: Admins (slug=admins, id=12345)
...
```

## 라이선스

MIT License
