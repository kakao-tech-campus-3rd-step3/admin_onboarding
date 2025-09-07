#!/usr/bin/env python3

import subprocess
import json
from datetime import datetime, timedelta
import sys

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