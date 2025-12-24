#!/usr/bin/env python3
"""
Git Code Ownership Analyzer
Analyzes git history to identify files where a team has significant contributions.
"""

import sys
import subprocess
import json
import argparse
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def run_git_command(args, cwd='.'):
    """Execute a git command and return output."""
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e.stderr}")
        return None


def get_all_tracked_files(repo_path='.'):
    """Get list of all tracked files in the repository."""
    output = run_git_command(['ls-files'], cwd=repo_path)
    if output:
        return [line.strip() for line in output.split('\n') if line.strip()]
    return []


def analyze_file_ownership(file_path, team_members, since_date, repo_path='.'):
    """
    Analyze ownership of a specific file.
    Returns dict with author statistics.
    """
    # Get commit history for the file
    git_args = [
        'log',
        '--format=%ae|%ad|%H',
        '--date=iso',
        '--numstat',
        f'--since={since_date}',
        '--',
        file_path
    ]
    
    output = run_git_command(git_args, cwd=repo_path)
    if not output:
        return None
    
    authors = defaultdict(lambda: {'commits': 0, 'additions': 0, 'deletions': 0, 'net_lines': 0})
    
    lines = output.split('\n')
    current_author = None
    current_date = None
    
    for line in lines:
        if '|' in line and '@' in line:
            # Commit header line
            parts = line.split('|')
            if len(parts) >= 2:
                current_author = parts[0].strip()
                current_date = parts[1].strip()
                authors[current_author]['commits'] += 1
        elif line.strip() and current_author:
            # Numstat line
            parts = line.split('\t')
            if len(parts) >= 2:
                try:
                    additions = int(parts[0]) if parts[0] != '-' else 0
                    deletions = int(parts[1]) if parts[1] != '-' else 0
                    authors[current_author]['additions'] += additions
                    authors[current_author]['deletions'] += deletions
                    authors[current_author]['net_lines'] += (additions - deletions)
                except ValueError:
                    pass
    
    if not authors:
        return None
    
    # Calculate team statistics
    team_stats = {
        'commits': 0,
        'additions': 0,
        'deletions': 0,
        'net_lines': 0
    }
    
    total_stats = {
        'commits': 0,
        'additions': 0,
        'deletions': 0,
        'net_lines': 0
    }
    
    for author, stats in authors.items():
        total_stats['commits'] += stats['commits']
        total_stats['additions'] += stats['additions']
        total_stats['deletions'] += stats['deletions']
        total_stats['net_lines'] += stats['net_lines']
        
        if author in team_members:
            team_stats['commits'] += stats['commits']
            team_stats['additions'] += stats['additions']
            team_stats['deletions'] += stats['deletions']
            team_stats['net_lines'] += stats['net_lines']
    
    # Calculate percentages
    if total_stats['commits'] == 0:
        return None
    
    return {
        'file': file_path,
        'team_commits': team_stats['commits'],
        'total_commits': total_stats['commits'],
        'team_commit_percentage': (team_stats['commits'] / total_stats['commits'] * 100),
        'team_additions': team_stats['additions'],
        'total_additions': total_stats['additions'],
        'team_addition_percentage': (team_stats['additions'] / total_stats['additions'] * 100) if total_stats['additions'] > 0 else 0,
        'all_authors': list(authors.keys()),
        'team_authors': [a for a in authors.keys() if a in team_members]
    }


def main():
    parser = argparse.ArgumentParser(
        description='Analyze git repository to identify team code ownership'
    )
    parser.add_argument(
        '--team-members',
        required=True,
        help='Comma-separated list of team member email addresses'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=30.0,
        help='Minimum percentage of commits to consider ownership (default: 30.0)'
    )
    parser.add_argument(
        '--since',
        default='6 months ago',
        help='Analyze commits since this date (default: "6 months ago")'
    )
    parser.add_argument(
        '--repo-path',
        default='.',
        help='Path to git repository (default: current directory)'
    )
    parser.add_argument(
        '--output',
        default='ownership_report.json',
        help='Output file for results (default: ownership_report.json)'
    )
    parser.add_argument(
        '--min-commits',
        type=int,
        default=3,
        help='Minimum total commits for a file to be considered (default: 3)'
    )
    parser.add_argument(
        '--exclude-patterns',
        help='Comma-separated patterns to exclude (e.g., "*.md,*.txt")'
    )
    
    args = parser.parse_args()
    
    # Parse team members
    team_members = set(email.strip() for email in args.team_members.split(','))

    if len(team_members) < 1:
        print("Please specify at least one team member")
        sys.exit(2)
    
    # Parse exclude patterns
    exclude_patterns = []
    if args.exclude_patterns:
        exclude_patterns = [p.strip() for p in args.exclude_patterns.split(',')]
    
    print(f"Analyzing repository: {args.repo_path}")
    print(f"Team members: {', '.join(team_members)}")
    print(f"Threshold: {args.threshold}%")
    print(f"Since: {args.since}")
    print(f"Minimum commits: {args.min_commits}")
    print()
    
    # Get all tracked files
    all_files = get_all_tracked_files(args.repo_path)
    
    # Filter out excluded patterns
    if exclude_patterns:
        filtered_files = []
        for file_path in all_files:
            excluded = False
            for pattern in exclude_patterns:
                if Path(file_path).match(pattern):
                    excluded = True
                    break
            if not excluded:
                filtered_files.append(file_path)
        all_files = filtered_files
    
    print(f"Analyzing {len(all_files)} files...")
    
    # Analyze each file
    results = []
    owned_files = []
    
    for i, file_path in enumerate(all_files):
        if (i + 1) % 100 == 0:
            print(f"Progress: {i + 1}/{len(all_files)}")
        
        analysis = analyze_file_ownership(
            file_path,
            team_members,
            args.since,
            args.repo_path
        )
        
        if analysis and analysis['total_commits'] >= args.min_commits:
            results.append(analysis)
            
            if analysis['team_commit_percentage'] >= args.threshold:
                owned_files.append(analysis)
    
    # Sort by team ownership percentage
    owned_files.sort(key=lambda x: x['team_commit_percentage'], reverse=True)
    
    # Prepare output
    output_data = {
        'analysis_date': datetime.now().isoformat(),
        'parameters': {
            'team_members': list(team_members),
            'threshold': args.threshold,
            'since': args.since,
            'min_commits': args.min_commits,
            'exclude_patterns': exclude_patterns
        },
        'summary': {
            'total_files_analyzed': len(results),
            'files_above_threshold': len(owned_files)
        },
        'owned_files': owned_files
    }
    
    # Write to file
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Analysis complete!")
    print(f"Total files analyzed: {len(results)}")
    print(f"Files above {args.threshold}% threshold: {len(owned_files)}")
    print(f"Results written to: {args.output}")
    print(f"{'='*60}\n")
    
    # Print top 10 owned files
    if owned_files:
        print("Top files owned by team:")
        print(f"{'File':<50} {'Team %':<10} {'Commits':<10}")
        print('-' * 70)
        for file_data in owned_files[:10]:
            print(f"{file_data['file']:<50} {file_data['team_commit_percentage']:>6.1f}%   {file_data['team_commits']}/{file_data['total_commits']}")


if __name__ == '__main__':
    main()
