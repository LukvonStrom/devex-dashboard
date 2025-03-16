import mongoengine as me


class Team(me.Document):
    team_id = me.IntField(primary_key=True)
    name = me.StringField(required=True)
    members = me.ListField(me.StringField())
    created_at = me.DateTimeField()
    updated_at = me.DateTimeField()
    description = me.StringField()
    
    meta = {
        'indexes': [
            'name',
            'created_at',
            'updated_at'
        ]
    }

class Repository(me.Document):
    repo_id = me.IntField(primary_key=True)
    name = me.StringField(required=True)
    owner = me.StringField()
    created_at = me.DateTimeField()
    updated_at = me.DateTimeField()
    description = me.StringField()
    
    meta = {
        'indexes': [
            'name',
            'owner',
            'created_at',
            'updated_at'
        ]
    }

# Define MongoDB Document Classes with MongoEngine
class PullRequest(me.Document):
    pr_id = me.IntField(primary_key=True)
    repo = me.StringField(required=True)
    title = me.StringField()
    author = me.StringField()
    created_at = me.DateTimeField()
    closed_at = me.DateTimeField()
    merged_at = me.DateTimeField()
    state = me.StringField()
    review_count = me.IntField(default=0)
    comment_count = me.IntField(default=0)
    additions = me.IntField(default=0)
    deletions = me.IntField(default=0)
    changed_files = me.IntField(default=0)
    
    meta = {
        'indexes': [
            'repo',
            'author',
            'created_at',
            'merged_at'
        ]
    }

class Issue(me.Document):
    issue_id = me.IntField()  # Numeric part of the issue key
    issue_key = me.StringField(primary_key=True)  # e.g., "PROJ-123"
    project_key = me.StringField(required=True)  # e.g., "PROJ"
    repo = me.StringField()  # Keep for backward compatibility
    title = me.StringField()  # Summary in Jira terminology
    description = me.StringField()
    issue_type = me.StringField(default="Task")  # Bug, Task, Story, Epic, etc.
    author = me.StringField()  # Reporter in Jira terminology
    assignee = me.StringField()  # Person assigned to the issue
    created_at = me.DateTimeField()
    updated_at = me.DateTimeField()
    closed_at = me.DateTimeField()
    due_date = me.DateTimeField()
    status = me.StringField(default="To Do")  # To Do, In Progress, Done, etc.
    resolution = me.StringField()  # Fixed, Won't Fix, Cannot Reproduce, etc.
    priority = me.StringField(default="Medium")  # Highest, High, Medium, Low, Lowest
    comment_count = me.IntField(default=0)
    labels = me.ListField(me.StringField())
    components = me.ListField(me.StringField())
    sprint = me.StringField()
    story_points = me.FloatField()
    epic_link = me.StringField()  # Reference to parent epic
    
    meta = {
        'indexes': [
            'repo',
            'project_key',
            'author',
            'assignee',
            'created_at',
            'closed_at',
            'status',
            'issue_type',
            'priority',
            'sprint'
        ]
    }

class Commit(me.Document):
    sha = me.StringField(primary_key=True)
    repo = me.StringField(required=True)
    author = me.StringField()
    committed_at = me.DateTimeField()
    message = me.StringField()
    additions = me.IntField(default=0)
    deletions = me.IntField(default=0)
    files_changed = me.IntField(default=0)
    
    meta = {
        'indexes': [
            'repo',
            'author',
            'committed_at'
        ]
    }

class WorkflowRun(me.Document):
    run_id = me.IntField(primary_key=True)
    repo = me.StringField(required=True)
    workflow_name = me.StringField()
    created_at = me.DateTimeField()  # When workflow was queued
    started_at = me.DateTimeField()  # When runner picked up the workflow
    completed_at = me.DateTimeField()
    conclusion = me.StringField()  # success, failure, cancelled, etc.
    runner_name = me.StringField()
    runner_type = me.StringField()  # GitHub-hosted or self-hosted
    pickup_time_seconds = me.FloatField()  # Time between created_at and started_at
    execution_time_seconds = me.FloatField()  # Time between started_at and completed_at
    branch = me.StringField()
    
    meta = {
        'indexes': [
            'repo',
            'created_at',
            'runner_type',
            'branch'
        ]
    }