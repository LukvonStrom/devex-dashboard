import os
import mongoengine as me
import argparse
from datetime import datetime, timedelta
from github import Github
import re
from jira import JIRA
from collections import defaultdict

from models import PullRequest, Issue, Commit, WorkflowRun, Team, Repository

# Parse command line arguments
parser = argparse.ArgumentParser(description='Collect GitHub and Jira metrics')
parser.add_argument('--github-only', action='store_true', help='Only collect GitHub data')
parser.add_argument('--jira-only', action='store_true', help='Only collect Jira data')
parser.add_argument('--teams', action='store_true', help='Collect team information')
parser.add_argument('--repos', action='store_true', help='Collect repository information')
args = parser.parse_args()

# Connect to MongoDB
mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/github_metrics")
me.connect(host=mongo_uri)

# Date range for data collection
end_date = datetime.now()
start_date = end_date - timedelta(days=90)  # Last 90 days

# GitHub authentication
if not args.jira_only:
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required for GitHub data collection")
    g = Github(github_token)

# Jira authentication
if not args.github_only:
    jira_url = os.environ.get("JIRA_URL")
    jira_username = os.environ.get("JIRA_USERNAME")
    jira_api_token = os.environ.get("JIRA_API_TOKEN")
    if not all([jira_url, jira_username, jira_api_token]):
        raise ValueError("JIRA_URL, JIRA_USERNAME and JIRA_API_TOKEN environment variables are required for Jira data collection")
    jira = JIRA(server=jira_url, basic_auth=(jira_username, jira_api_token))

# Configuration
github_repositories = [
    "your-org/repo1",
    "your-org/repo2",
    "your-org/repo3"
]

# Extract unique organizations from repositories
github_organizations = list(set([repo.split('/')[0] for repo in github_repositories]))

jira_projects = ["PROJ", "INFRA", "FE"]  # Project keys to collect

# Extract Jira issue key from commit message
def extract_jira_keys(text):
    if not text:
        return []
    # Match PROJ-123 pattern
    pattern = r'([A-Z]+-\d+)'
    return re.findall(pattern, text)

# Collect GitHub Teams
def collect_github_teams():
    print(f"Starting GitHub Team collection at {datetime.now()}")
    
    team_id_counter = 1
    
    for org_name in github_organizations:
        print(f"Collecting teams for organization: {org_name}")
        
        try:
            # Get the organization
            org = g.get_organization(org_name)
            
            # Get all teams in the organization
            teams = org.get_teams()
            
            for team in teams:
                print(f"Processing team: {team.name}")
                
                # Get team members
                members = []
                try:
                    for member in team.get_members():
                        members.append(member.login)
                except Exception as e:
                    print(f"Error collecting members for team {team.name}: {str(e)}")
                
                # Update or create Team document
                Team.objects(name=team.name).update_one(
                    set__team_id=team_id_counter,
                    set__name=team.name,
                    set__members=members,
                    set__created_at=datetime.now(),  # GitHub API doesn't provide team creation date
                    set__updated_at=datetime.now(),
                    set__description=team.description or f"Team {team.name} in {org_name}",
                    upsert=True
                )
                
                team_id_counter += 1
                
        except Exception as e:
            print(f"Error processing organization {org_name}: {str(e)}")
            
    print(f"Team collection completed at {datetime.now()}")

# Collect GitHub Repositories
def collect_github_repos():
    print(f"Starting GitHub Repository collection at {datetime.now()}")
    
    repo_id_counter = 1
    collected_repos = []
    
    # First collect repositories from the configuration list
    for repo_name in github_repositories:
        try:
            org_name, repo_short_name = repo_name.split('/')
            repo = g.get_repo(repo_name)
            
            # Update or create Repository document
            Repository.objects(name=repo_short_name, owner=org_name).update_one(
                set__repo_id=repo_id_counter,
                set__name=repo_short_name,
                set__owner=org_name,
                set__created_at=repo.created_at,
                set__updated_at=repo.updated_at or repo.pushed_at,
                set__description=repo.description or f"Repository for {repo_short_name}",
                upsert=True
            )
            
            collected_repos.append(repo_name)
            repo_id_counter += 1
            
        except Exception as e:
            print(f"Error processing repository {repo_name}: {str(e)}")
    
    # Then collect additional repositories from organizations if needed
    for org_name in github_organizations:
        try:
            # Get the organization
            org = g.get_organization(org_name)
            
            # Get all repositories in the organization
            repos = org.get_repos()
            
            for repo in repos:
                full_name = f"{org_name}/{repo.name}"
                
                # Skip if already collected from the configuration list
                if full_name in collected_repos:
                    continue
                    
                print(f"Processing additional repository: {full_name}")
                
                # Update or create Repository document
                Repository.objects(name=repo.name, owner=org_name).update_one(
                    set__repo_id=repo_id_counter,
                    set__name=repo.name,
                    set__owner=org_name,
                    set__created_at=repo.created_at,
                    set__updated_at=repo.updated_at or repo.pushed_at,
                    set__description=repo.description or f"Repository for {repo.name}",
                    upsert=True
                )
                
                repo_id_counter += 1
                
        except Exception as e:
            print(f"Error collecting repositories for organization {org_name}: {str(e)}")
            
    print(f"Repository collection completed at {datetime.now()}")

# Collect GitHub data
def collect_github_data():
    print(f"Starting GitHub data collection at {datetime.now()}")
    
    for repo_name in github_repositories:
        print(f"Collecting data for repository: {repo_name}")
        repo = g.get_repo(repo_name)
        
        # Collect Pull Requests
        print("Collecting pull requests...")
        pull_requests = repo.get_pulls(state='all', sort='created', direction='desc')
        for pr in pull_requests:
            if pr.created_at < start_date:
                break
                
            # Update or create PR document
            PullRequest.objects(pr_id=pr.number).update_one(
                set__repo=repo_name,
                set__title=pr.title,
                set__author=pr.user.login,
                set__created_at=pr.created_at,
                set__closed_at=pr.closed_at,
                set__merged_at=pr.merged_at,
                set__state=pr.state,
                set__review_count=len(list(pr.get_reviews())),
                set__comment_count=pr.comments,
                set__additions=pr.additions,
                set__deletions=pr.deletions,
                set__changed_files=pr.changed_files,
                upsert=True
            )
        
        # Collect Commits
        print("Collecting commits...")
        commits = repo.get_commits(since=start_date)
        for commit in commits:
            try:
                # Extract Jira keys from commit message
                jira_keys = extract_jira_keys(commit.commit.message)
                
                # Update or create Commit document
                Commit.objects(sha=commit.sha).update_one(
                    set__repo=repo_name,
                    set__author=commit.author.login if commit.author else "Unknown",
                    set__committed_at=commit.commit.author.date,
                    set__message=commit.commit.message,
                    set__additions=commit.stats.additions,
                    set__deletions=commit.stats.deletions,
                    set__files_changed=len(commit.files),
                    upsert=True
                )
            except Exception as e:
                print(f"Error processing commit {commit.sha}: {str(e)}")
        
        # Collect GitHub Actions workflow run data
        print("Collecting workflow runs...")
        workflow_runs = repo.get_workflow_runs()
        for run in workflow_runs:
            if run.created_at < start_date:
                break
            
            # Calculate pickup time (time between created_at and started_at)
            pickup_time_seconds = None
            if run.created_at and run.run_started_at:
                pickup_time_seconds = (run.run_started_at - run.created_at).total_seconds()
            
            # Calculate execution time (time between started_at and completed_at)
            execution_time_seconds = None
            if run.run_started_at and run.updated_at:
                execution_time_seconds = (run.updated_at - run.run_started_at).total_seconds()
            
            # Determine runner type based on labels
            runner_type = "GitHub-hosted"
            runner_name = "unknown"
            if hasattr(run, 'runner') and run.runner:
                runner_name = run.runner.name
                # This is an assumption - GitHub doesn't explicitly expose whether a runner is self-hosted
                if not any(name in runner_name.lower() for name in ["ubuntu", "windows", "macos", "latest"]):
                    runner_type = "self-hosted"
            
            # Update or create WorkflowRun document
            WorkflowRun.objects(run_id=run.id).update_one(
                set__repo=repo_name,
                set__workflow_name=run.name,
                set__created_at=run.created_at,
                set__started_at=run.run_started_at,
                set__completed_at=run.updated_at,
                set__conclusion=run.conclusion,
                set__runner_name=runner_name,
                set__runner_type=runner_type,
                set__pickup_time_seconds=pickup_time_seconds,
                set__execution_time_seconds=execution_time_seconds,
                set__branch=run.head_branch,
                upsert=True
            )

# Collect Jira data
def collect_jira_data():
    print(f"Starting Jira data collection at {datetime.now()}")
    
    for project_key in jira_projects:
        print(f"Collecting issues for project: {project_key}")
        
        # JQL query to get issues updated since start_date
        jql_query = f'project = {project_key} AND updated >= "{start_date.strftime("%Y-%m-%d")}"'
        issues = jira.search_issues(jql_query, maxResults=False)
        
        for jira_issue in issues:
            # Extract the numeric part of the issue key
            issue_id = int(jira_issue.key.split('-')[1])
            
            # Map Jira fields to our model
            created = datetime.strptime(jira_issue.fields.created, '%Y-%m-%dT%H:%M:%S.%f%z')
            updated = datetime.strptime(jira_issue.fields.updated, '%Y-%m-%dT%H:%M:%S.%f%z')
            
            # Handle resolution date (may be None)
            closed_at = None
            if jira_issue.fields.resolutiondate:
                closed_at = datetime.strptime(jira_issue.fields.resolutiondate, '%Y-%m-%dT%H:%M:%S.%f%z')
            
            # Handle due date (may be None)
            due_date = None
            if hasattr(jira_issue.fields, 'duedate') and jira_issue.fields.duedate:
                due_date = datetime.strptime(jira_issue.fields.duedate, '%Y-%m-%d')
            
            # Get reporter and assignee
            author = jira_issue.fields.reporter.displayName if jira_issue.fields.reporter else "Unknown"
            assignee = jira_issue.fields.assignee.displayName if jira_issue.fields.assignee else None
            
            # Get comments count
            comment_count = 0
            if hasattr(jira_issue.fields, 'comment'):
                comment_count = len(jira_issue.fields.comment.comments) if jira_issue.fields.comment else 0
            
            # Get labels and components
            labels = jira_issue.fields.labels if hasattr(jira_issue.fields, 'labels') else []
            components = [c.name for c in jira_issue.fields.components] if hasattr(jira_issue.fields, 'components') else []
            
            # Get sprint (custom field, may require adjustment for your Jira instance)
            sprint = None
            if hasattr(jira_issue.fields, 'customfield_10007'):  # Common sprint field
                sprint_field = jira_issue.fields.customfield_10007
                if sprint_field and isinstance(sprint_field, list) and len(sprint_field) > 0:
                    # Extract sprint name from field
                    sprint_str = sprint_field[0]
                    sprint_match = re.search(r'name=([^,]+)', sprint_str)
                    if sprint_match:
                        sprint = sprint_match.group(1)
            
            # Get story points (custom field, may require adjustment)
            story_points = None
            if hasattr(jira_issue.fields, 'customfield_10002'):  # Common story points field
                story_points = jira_issue.fields.customfield_10002
            
            # Get epic link (custom field, may require adjustment)
            epic_link = None
            if hasattr(jira_issue.fields, 'customfield_10004'):  # Common epic link field
                epic_link = jira_issue.fields.customfield_10004
            
            # Update or create Issue document with all Jira fields
            Issue.objects(issue_key=jira_issue.key).update_one(
                set__issue_id=issue_id,
                set__project_key=project_key,
                set__title=jira_issue.fields.summary,
                set__description=jira_issue.fields.description,
            )