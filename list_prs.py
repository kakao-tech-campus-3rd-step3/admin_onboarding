#!/usr/bin/env python3
"""
카카오테크캠퍼스 3기 Step3 PR 현황 조회 스크립트

이 스크립트는 카카오테크캠퍼스 3기 Step3의 모든 팀 레포지토리에서 
main 브랜치로 향하는 PR들을 조회하여 현황을 보여줍니다.

주요 기능:
- 실행 시점의 직전 금요일부터 현재까지의 PR 조회
- OPEN 상태와 MERGED 상태 PR 구분 표시
- 프론트엔드(FE)와 백엔드(BE) 레포지토리 분리 표시
- 머지 방향 표시 (main ← source_branch)
- 총 개수 요약 제공

사용법:
    python3 list_prs.py
    또는
    ./list_prs.py

요구사항:
- GitHub CLI (gh) 설치 및 로그인 필요
- Python 3.6 이상
- kakao-tech-campus-3rd-step3 조직의 레포지토리 접근 권한

날짜 계산 로직:
- 오늘이 금요일 오전 9시 이전 → 지난주 금요일부터
- 그 외의 경우 → 가장 최근 금요일부터

예시:
- 2025-09-07 (일요일) 실행 → 2025-09-05 (금요일)부터
- 2025-09-13 (토요일) 실행 → 2025-09-12 (금요일)부터
"""

import subprocess
import json
from datetime import datetime, timedelta
import sys

def check_gh_auth():
    """GitHub CLI 설치 및 인증 상태 확인"""
    try:
        # gh 명령어 존재 여부 확인
        subprocess.run(['gh', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ GitHub CLI (gh)가 설치되어 있지 않습니다.")
        print("\n설치 방법:")
        print("  macOS: brew install gh")
        print("  Linux: https://github.com/cli/cli/blob/trunk/docs/install_linux.md")
        print("  Windows: https://github.com/cli/cli/releases")
        sys.exit(1)
    
    try:
        # 인증 상태 확인
        result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ GitHub CLI에 로그인되어 있지 않습니다.")
            print("\n로그인 방법:")
            print("  gh auth login")
            print("\n또는 토큰을 사용한 로그인:")
            print("  gh auth login --with-token")
            sys.exit(1)
    except subprocess.CalledProcessError:
        print("❌ GitHub CLI 인증 상태를 확인할 수 없습니다.")
        print("\n다음 명령어로 로그인해주세요:")
        print("  gh auth login")
        sys.exit(1)
    
    # kakao-tech-campus-3rd-step3 조직 접근 권한 확인
    try:
        result = subprocess.run([
            'gh', 'repo', 'list', 'kakao-tech-campus-3rd-step3', '--limit', '1'
        ], capture_output=True, text=True, check=True)
        
        if not result.stdout.strip():
            print("❌ kakao-tech-campus-3rd-step3 조직의 레포지토리에 접근할 수 없습니다.")
            print("\n다음을 확인해주세요:")
            print("  1. 조직에 초대되었는지 확인")
            print("  2. 조직 멤버십이 public으로 설정되었는지 확인")
            print("  3. GitHub CLI에 올바른 계정으로 로그인되었는지 확인")
            sys.exit(1)
    except subprocess.CalledProcessError:
        print("❌ kakao-tech-campus-3rd-step3 조직에 접근할 수 없습니다.")
        print("\n권한을 확인해주세요.")
        sys.exit(1)
    
    print("✅ GitHub CLI 설정이 완료되었습니다.")

def get_last_friday():
    """현재 시점에서 가장 최근 금요일 날짜를 반환"""
    today = datetime.now()
    # 금요일은 weekday() == 4
    days_since_friday = (today.weekday() - 4) % 7
    if days_since_friday == 0 and today.hour < 9:  # 금요일 오전 9시 이전이면 지난주 금요일
        days_since_friday = 7
    
    last_friday = today - timedelta(days=days_since_friday)
    return last_friday.strftime('%Y-%m-%d')

def run_gh_command(repo, state='open'):
    """GitHub CLI로 PR 목록 조회"""
    try:
        cmd = ['gh', 'pr', 'list', '-R', repo, '--base', 'main', '--state', state, '--limit', '50', '--json', 'number,title,headRefName,state,updatedAt']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError:
        return []
    except json.JSONDecodeError:
        return []

def is_after_date(pr_date, cutoff_date):
    """PR 날짜가 기준 날짜 이후인지 확인"""
    pr_datetime = datetime.fromisoformat(pr_date.replace('Z', '+00:00'))
    cutoff_datetime = datetime.strptime(cutoff_date, '%Y-%m-%d')
    return pr_datetime.date() >= cutoff_datetime.date()

def get_team_repos():
    """팀 레포지토리 목록 생성"""
    repos = []
    
    # FE 레포지토리들
    for i in range(1, 23):
        if i == 17:
            repos.append(('TEAM17_FE', 'FE'))
        else:
            repos.append((f'Team{i}_FE', 'FE'))
    
    # BE 레포지토리들
    for i in range(1, 23):
        if i == 17:
            repos.append(('TEAM17_BE', 'BE'))
        else:
            repos.append((f'Team{i}_BE', 'BE'))
    
    return repos

def main():
    # GitHub CLI 설정 확인
    check_gh_auth()
    print()  # 빈 줄 추가
    
    last_friday = get_last_friday()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("=" * 60)
    print("카카오테크캠퍼스 3기 Step3 PR 현황 (main 브랜치)")
    print(f"조회 기간: {last_friday} ~ {current_time}")
    print("=" * 60)
    print()
    
    open_count = 0
    merged_count = 0
    
    # OPEN 상태 PR 조회
    print("🔵 OPEN 상태 PR")
    print("-" * 50)
    
    print("### 프론트엔드 (FE)")
    for repo_name, repo_type in get_team_repos():
        if repo_type != 'FE':
            continue
            
        full_repo = f"kakao-tech-campus-3rd-step3/{repo_name}"
        prs = run_gh_command(full_repo, 'open')
        
        for pr in prs:
            if is_after_date(pr['updatedAt'], last_friday):
                print(f"  {repo_name} - #{pr['number']}: {pr['title']} (main ← {pr['headRefName']}) [OPEN]")
                open_count += 1
    
    print("\n### 백엔드 (BE)")
    for repo_name, repo_type in get_team_repos():
        if repo_type != 'BE':
            continue
            
        full_repo = f"kakao-tech-campus-3rd-step3/{repo_name}"
        prs = run_gh_command(full_repo, 'open')
        
        for pr in prs:
            if is_after_date(pr['updatedAt'], last_friday):
                print(f"  {repo_name} - #{pr['number']}: {pr['title']} (main ← {pr['headRefName']}) [OPEN]")
                open_count += 1
    
    # MERGED 상태 PR 조회
    print(f"\n🟢 MERGED 상태 PR ({last_friday} 이후)")
    print("-" * 50)
    
    print("### 프론트엔드 (FE)")
    for repo_name, repo_type in get_team_repos():
        if repo_type != 'FE':
            continue
            
        full_repo = f"kakao-tech-campus-3rd-step3/{repo_name}"
        prs = run_gh_command(full_repo, 'merged')
        
        for pr in prs:
            if is_after_date(pr['updatedAt'], last_friday):
                merge_date = datetime.fromisoformat(pr['updatedAt'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
                print(f"  {repo_name} - #{pr['number']}: {pr['title']} (main ← {pr['headRefName']}) ✅ MERGED ({merge_date})")
                merged_count += 1
    
    print("\n### 백엔드 (BE)")
    for repo_name, repo_type in get_team_repos():
        if repo_type != 'BE':
            continue
            
        full_repo = f"kakao-tech-campus-3rd-step3/{repo_name}"
        prs = run_gh_command(full_repo, 'merged')
        
        for pr in prs:
            if is_after_date(pr['updatedAt'], last_friday):
                merge_date = datetime.fromisoformat(pr['updatedAt'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
                print(f"  {repo_name} - #{pr['number']}: {pr['title']} (main ← {pr['headRefName']}) ✅ MERGED ({merge_date})")
                merged_count += 1
    
    # 요약
    print()
    print("=" * 60)
    print("📊 요약")
    print("-" * 50)
    print(f"OPEN 상태 PR: {open_count}개")
    print(f"MERGED 상태 PR: {merged_count}개")
    print(f"총 PR: {open_count + merged_count}개")
    print("=" * 60)

if __name__ == "__main__":
    main()