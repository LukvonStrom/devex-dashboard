import mongoengine as me
import random
import uuid
from datetime import datetime, timedelta
import time
from tqdm import tqdm
import numpy as np
from models import PullRequest, Issue, Commit, WorkflowRun, Team, Repository

def random_hour_of_day(dev_work_pattern="business"):
    """
    Generate a random hour of the day based on work patterns
    
    Args:
        dev_work_pattern: 
            "business" - mostly 9am-5pm
            "night_owl" - evening/night hours
            "distributed" - evenly spread
    
    Returns:
        Hour of day (0-23)
    """
    if dev_work_pattern == "business":
        # Business hours distribution (peaks during 9am-5pm)
        if random.random() < 0.8:  # 80% during business hours
            return random.randint(9, 17)
        else:
            # Remaining 20% distributed with morning/evening bias
            return random.choice([7, 8, 18, 19, 20] + list(range(0, 24)))
    elif dev_work_pattern == "night_owl":
        # Night owl (peaks in evening/night)
        if random.random() < 0.7:  # 70% evening/night
            return random.randint(18, 23) if random.random() < 0.7 else random.randint(0, 6)
        else:
            # 30% during the day
            return random.randint(9, 17)
    else:  # distributed
        # More evenly distributed
        return random.randint(0, 23)            # More varied commit message styles
message_styles = [
    # Conventional commits style
    f"{random.choice(['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore'])}{random.choice(['', '(scope)'])}: {random.choice(['Add', 'Update', 'Remove', 'Fix'])} {random.choice(['feature', 'component', 'test', 'dependency', 'documentation'])}",
    # Simple style
    f"{random.choice(['Add', 'Fix', 'Update', 'Implement', 'Refactor', 'Remove', 'Optimize'])} {random.choice(['feature', 'bug', 'performance issue', 'UI component', 'API endpoint', 'documentation', 'test'])}",
    # Detailed style
    f"{random.choice(['Added', 'Fixed', 'Updated', 'Implemented', 'Refactored'])} {random.choice(['the', 'a'])} {random.choice(['main', 'core', 'critical', 'optional'])} {random.choice(['feature', 'component', 'module', 'function', 'service'])} for {random.choice(['better performance', 'improved UX', 'compatibility', 'stability'])}"
]            
common_verbs = ["Add", "Fix", "Update", "Implement", "Refactor", "Remove", "Optimize", "Improve", "Streamline", "Enhance"]
common_targets = ["feature", "bug", "performance issue", "UI component", "API endpoint", "documentation", "test", "workflow", "configuration", "dependency", "accessibility", "error handling"]


# =============================================================================
# MOCK DATA GENERATION CONFIGURATION
# =============================================================================

# Time range configuration
SIMULATION_END_DATE = datetime.now()
SIMULATION_START_DATE = SIMULATION_END_DATE - timedelta(days=365)  # Last year

# Organization structure
ORG_NAME = "mock-org"
REPOS = ["frontend", "backend", "infra"]

# Enhanced team configuration - less predictable size distribution
# and added team productivity/quality factors
TEAM_CONFIG = {
    "Frontend": {
        "size_pct_range": (0.15, 0.45),  # Range instead of fixed percentage
        "repo_focus": {"frontend": 0.8, "backend": 0.15, "infra": 0.05},
        "description": "The Frontend team is responsible for user interfaces and client-side development.",
        "productivity_factor": random.uniform(0.7, 1.3),  # Some teams are more efficient
        "quality_factor": random.uniform(0.7, 1.3)  # Some teams produce higher quality work
    },
    "Backend": {
        "size_pct_range": (0.15, 0.45),
        "repo_focus": {"frontend": 0.1, "backend": 0.8, "infra": 0.1},
        "description": "The Backend team is responsible for APIs, databases, and server-side logic.",
        "productivity_factor": random.uniform(0.7, 1.3),
        "quality_factor": random.uniform(0.7, 1.3)
    },
    "DevOps": {
        "size_pct_range": (0.1, 0.3),
        "repo_focus": {"frontend": 0.05, "backend": 0.15, "infra": 0.8},
        "description": "The DevOps team is responsible for infrastructure, CI/CD, and operations.",
        "productivity_factor": random.uniform(0.7, 1.3),
        "quality_factor": random.uniform(0.7, 1.3)
    },
    "QA": {
        "size_pct_range": (0.05, 0.2),
        "repo_focus": {"frontend": 0.33, "backend": 0.33, "infra": 0.34},
        "description": "The QA team is responsible for quality assurance and testing.",
        "productivity_factor": random.uniform(0.7, 1.3),
        "quality_factor": random.uniform(0.7, 1.3)
    }
}

# Project keys for Jira issues
PROJECT_KEYS = {"frontend": "FE", "backend": "BE", "infra": "INFRA"}

# Volume configuration
ORG_SIZE = 500  # Total number of developers
ISSUES_PER_REPO = 1000
PRS_PER_REPO = 3000
COMMITS_PER_REPO = 5000
WORKFLOW_RUNS_PER_REPO = 2500

# Batch size for database operations
BATCH_SIZE = 500

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def weighted_choice(choices, weights):
    """Make a weighted random choice from a list of options"""
    return random.choices(choices, weights=weights, k=1)[0]

def random_date(start_date, end_date, distribution="uniform", weekday_bias=True):
    """
    Generate a random date between start_date and end_date
    
    Args:
        start_date: Earliest possible date
        end_date: Latest possible date
        distribution: 'uniform' for even distribution, 
                     'recent_heavy' to bias toward recent dates,
                     'variable' for clustered dates with high variance
        weekday_bias: If True, dates are more likely to be weekdays than weekends
    
    Returns:
        Random datetime between start and end dates
    """
    delta = end_date - start_date
    delta_seconds = delta.total_seconds()
    
    # First pick a random point in the time range
    if distribution == "uniform":
        # Uniform distribution across the entire range
        random_second = random.uniform(0, delta_seconds)
    elif distribution == "recent_heavy":
        # Bias toward more recent dates (last 30% of range)
        if random.random() < 0.7:  # 70% chance of recent date
            recent_start = start_date + timedelta(seconds=delta_seconds * 0.7)
            random_second = random.uniform((recent_start - start_date).total_seconds(), delta_seconds)
        else:
            random_second = random.uniform(0, delta_seconds)
    elif distribution == "variable":
        # More clustered random dates with occasional outliers
        if random.random() < 0.9:  # 90% of dates follow a normal distribution
            # Center of the normal distribution (mean) will be somewhere in the range
            mean_point = random.uniform(0, delta_seconds)
            # Standard deviation - higher values create more spread
            std_dev = delta_seconds / random.choice([2, 4, 6, 8])
            # Sample from normal distribution, but clamp to the valid range
            random_second = np.random.normal(mean_point, std_dev)
            random_second = max(0, min(random_second, delta_seconds))
        else:  # 10% are uniform random (could be anywhere)
            random_second = random.uniform(0, delta_seconds)
    else:
        raise ValueError(f"Unknown distribution: {distribution}")
    
    # Get the initial random date
    candidate_date = start_date + timedelta(seconds=random_second)
    
    # Apply weekday bias if requested
    if weekday_bias:
        # Check if it's a weekend (5=Saturday, 6=Sunday)
        is_weekend = candidate_date.weekday() >= 5
        
        if is_weekend:
            # 70% chance to move to a weekday for weekend dates
            if random.random() < 0.7:
                # Decide whether to go forward or backward to find a weekday
                if random.random() < 0.5:
                    # Go forward to Monday (0-4 are weekdays)
                    days_to_add = 7 - candidate_date.weekday()
                    candidate_date += timedelta(days=days_to_add)
                else:
                    # Go backward to Friday
                    days_to_subtract = candidate_date.weekday() - 4
                    candidate_date -= timedelta(days=days_to_subtract)
                
                # Make sure we're still in range
                if candidate_date < start_date:
                    candidate_date = start_date
                elif candidate_date > end_date:
                    candidate_date = end_date
    
    return candidate_date

def long_tail_distribution(min_val, max_val, shape=2.0):
    """
    Generate a random number from a long-tail distribution.
    
    Args:
        min_val: Minimum value 
        max_val: Maximum value
        shape: Parameter controlling the shape of the distribution
              Lower values create longer tails
              
    Returns:
        A random number from the distribution
    """
    # Pareto distribution for long tail
    x = random.paretovariate(shape)
    
    # Scale to our desired range
    range_size = max_val - min_val
    scaled_val = min_val + (x / (x + 1)) * range_size
    
    # Cap at max_val
    return min(scaled_val, max_val)

# Developer characteristics generator
def generate_developer_characteristics(num_developers):
    """
    Generate individual characteristics for developers to create variability
    
    Returns:
        Dictionary mapping developer names to their characteristics
    """
    dev_chars = {}
    
    for i in range(1, num_developers + 1):
        dev_name = f"dev{i}"
        
        # Different developers have different productivity levels
        # This will affect how quickly they complete tasks
        productivity = np.random.normal(1.0, 0.3)  # Mean 1.0, std dev 0.3
        productivity = max(0.3, min(productivity, 2.0))  # Clamp to reasonable range
        
        # Quality of work - affects error rates, PR rejection, etc.
        quality = np.random.normal(1.0, 0.25)
        quality = max(0.4, min(quality, 1.7))
        
        # Activity level - how many contributions they make
        activity = np.random.normal(1.0, 0.4)
        activity = max(0.2, min(activity, 2.5))
        
        # Working hours - when they're most active
        # 0 = evenly distributed, 1 = mostly business hours, 2 = night owl
        work_pattern = random.choice([0, 1, 1, 1, 2])  # Business hours most common
        
        # Specialization - some devs focus on specific types of tasks
        specializations = {
            "bug_fixing": random.uniform(0.5, 1.5),
            "features": random.uniform(0.5, 1.5),
            "refactoring": random.uniform(0.5, 1.5),
            "documentation": random.uniform(0.5, 1.5)
        }
        
        # Some developers tend to work on bigger or smaller tasks
        task_size_preference = random.uniform(0.5, 1.5)
        
        # Tendency to pick up complex issues
        complexity_preference = random.uniform(0.5, 1.5)
        
        # Review thoroughness - affects review time
        review_thoroughness = random.uniform(0.5, 2.0)
        
        # Store characteristics
        dev_chars[dev_name] = {
            "productivity": productivity,
            "quality": quality,
            "activity": activity,
            "work_pattern": work_pattern,
            "specializations": specializations,
            "task_size_preference": task_size_preference,
            "complexity_preference": complexity_preference,
            "review_thoroughness": review_thoroughness
        }
    
    return dev_chars

# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_mock_data():
    """Generate mock data for development and testing purposes."""
    start_time = time.time()
    print(f"Starting mock data generation at {datetime.now()}")
    print(f"Simulating an organization with {ORG_SIZE} members from {SIMULATION_START_DATE.date()} to {SIMULATION_END_DATE.date()}")
    
    # Initialize team productivity dictionary
    team_productivity = {}
    
    # Clear existing data - important to prevent duplicate key errors
    print("Clearing existing data...")
    try:
        # Use a try block in case some collections don't exist yet
        WorkflowRun.objects.delete()
        PullRequest.objects.delete()
        Issue.objects.delete()
        Commit.objects.delete()
        Team.objects.delete()
        Repository.objects.delete()
    except Exception as e:
        print(f"Warning when clearing data: {e}")
        # Continue anyway as the collections might not exist yet
    
    # -------------------------------------------------------------------------
    # Generate developer characteristics for more realistic variability
    # -------------------------------------------------------------------------
    print("Generating developer characteristics...")
    dev_characteristics = generate_developer_characteristics(ORG_SIZE)
    
    # -------------------------------------------------------------------------
    # Generate organization members
    # -------------------------------------------------------------------------
    print("Generating organization members...")
    authors = [f"dev{i}" for i in range(1, ORG_SIZE + 1)]
    
    # -------------------------------------------------------------------------
    # Generate teams with variable sizes
    # -------------------------------------------------------------------------
    print("Generating teams with variable sizes...")
    teams = []
    team_member_map = {}  # Maps members to their team
    remaining_authors = authors.copy()
    
    # First pass: determine team sizes based on ranges
    total_allocated = 0
    min_team_size = 3  # Minimum team size
    team_sizes = {}
    
    # Randomly distribute team sizes within their ranges
    for team_name, team_info in TEAM_CONFIG.items():
        min_pct, max_pct = team_info["size_pct_range"]
        # Randomly select a percentage within the range
        team_pct = random.uniform(min_pct, max_pct)
        # Calculate team size based on percentage
        team_size = max(min_team_size, int(ORG_SIZE * team_pct))
        team_sizes[team_name] = team_size
        total_allocated += team_size
    
    # Adjust if we've allocated too many or too few
    adjustment_needed = ORG_SIZE - total_allocated
    if adjustment_needed != 0:
        # Distribute adjustment across teams proportionally
        team_names = list(team_sizes.keys())
        while adjustment_needed != 0:
            team_to_adjust = random.choice(team_names)
            if adjustment_needed > 0:
                team_sizes[team_to_adjust] += 1
                adjustment_needed -= 1
            else:
                if team_sizes[team_to_adjust] > min_team_size:
                    team_sizes[team_to_adjust] -= 1
                    adjustment_needed += 1
    
    # Second pass: create teams with the determined sizes
    for i, (team_name, team_info) in enumerate(TEAM_CONFIG.items()):
        team_size = team_sizes[team_name]
        
        # Adjust for last team to use all remaining members
        if i == len(TEAM_CONFIG) - 1:
            team_members = remaining_authors
        else:
            # Randomly select members for this team
            team_members = random.sample(remaining_authors, team_size)
            # Remove selected members from remaining pool
            for member in team_members:
                remaining_authors.remove(member)
        
        # Track which team each member belongs to
        for member in team_members:
            team_member_map[member] = team_name
            
        # Store team productivity and quality factors for later use
        team_productivity[team_name] = team_info["productivity_factor"]
        
        # Create team document
        created_date = SIMULATION_START_DATE - timedelta(days=random.randint(30, 365))
        updated_date = created_date + timedelta(days=random.randint(1, 30))
        
        teams.append(Team(
            team_id=i + 1,
            name=team_name,
            members=team_members,
            created_at=created_date,
            updated_at=updated_date,
            description=team_info["description"]
        ))
    
    # Batch insert teams
    Team.objects.insert(teams)
    print(f"Generated {len(teams)} teams with more variable sizes:")
    for team_name, size in team_sizes.items():
        print(f"  - {team_name}: {size} members ({size/ORG_SIZE*100:.1f}%)")
    
    # -------------------------------------------------------------------------
    # Generate repositories
    # -------------------------------------------------------------------------
    print("Generating repositories...")
    repositories = []
    
    for i, repo_name in enumerate(REPOS):
        created_date = SIMULATION_START_DATE - timedelta(days=random.randint(30, 365))
        updated_date = created_date + timedelta(days=random.randint(1, 30))
        
        repositories.append(Repository(
            repo_id=i + 1,
            name=repo_name,
            owner=ORG_NAME,
            created_at=created_date,
            updated_at=updated_date,
            description=f"Repository for {repo_name} code and resources."
        ))
    
    # Batch insert repositories
    Repository.objects.insert(repositories)
    print(f"Generated {len(repositories)} repositories")
    
    # -------------------------------------------------------------------------
    # Generate issues (Jira format) with more variable lead times
    # -------------------------------------------------------------------------
    print(f"Generating issues ({ISSUES_PER_REPO} per repo) with variable lead times...")
    all_issues = []
    
    # Mapping from issue ID to issue key for later reference
    issue_id_to_key = {}
    
    # Generate issue complexity distribution - some repos have more complex issues
    repo_complexity = {
        "frontend": random.uniform(0.8, 1.2),
        "backend": random.uniform(0.8, 1.2),
        "infra": random.uniform(0.8, 1.2)
    }
    
    for repo_idx, repo_name in enumerate(REPOS):
        project_key = PROJECT_KEYS[repo_name]
        repo_path = f"{ORG_NAME}/{repo_name}"
        
        for i in tqdm(range(ISSUES_PER_REPO), desc=f"Issues for {repo_name}"):
            # Random dates with more clustering and variability, weighted toward weekdays
            created_date = random_date(SIMULATION_START_DATE, SIMULATION_END_DATE, "variable", weekday_bias=True)
            
            # Add realistic time of day based on developer work patterns
            author = random.choice(authors)  # Ensure 'author' is initialized
            dev_char = dev_characteristics.get(author, {})
            work_pattern = "business"
            if "work_pattern" in dev_char:
                if dev_char["work_pattern"] == 0:
                    work_pattern = "distributed"
                elif dev_char["work_pattern"] == 2:
                    work_pattern = "night_owl"
            
            # Get a random hour based on the work pattern
            hour = random_hour_of_day(work_pattern)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            # Replace the hour, minute, and second while keeping the date
            created_date = created_date.replace(hour=hour, minute=minute, second=second)
            
            # Issue complexity affects lead time
            complexity_factor = np.random.normal(1.0, 0.5) * repo_complexity[repo_name]
            complexity_factor = max(0.2, min(complexity_factor, 3.0))  # Clamp to reasonable range
            
            # Some issues have very long lead times (outliers)
            lead_time_outlier = random.random() < 0.05  # 5% of issues
            
            # Calculate lead time with high variability
            if lead_time_outlier:
                # Outlier lead time - much longer
                lead_time_hours = random.randint(240, 720)  # 10-30 days
            else:
                # Normal lead time with variability based on complexity
                base_lead_time = random.randint(1, 72)  # 1-72 hours base
                lead_time_hours = int(base_lead_time * complexity_factor)
            
            # Updated date based on activity on the issue
            num_updates = max(1, int(np.random.normal(3, 2)))  # Mean of 3 updates
            update_intervals = [random.randint(1, max(2, lead_time_hours // (num_updates + 1))) for _ in range(num_updates)]
            updated_date = created_date + timedelta(hours=sum(update_intervals))
            
            # Some issues are still open
            is_closed = random.random() > (0.3 + 0.1 * complexity_factor)  # More complex issues less likely to be closed
            
            # Calculate closed date with variable lead time
            if is_closed:
                # Add some variability to closed dates
                closed_date = created_date + timedelta(hours=lead_time_hours)
                # Some issues are reopened and closed again
                if random.random() < 0.1:  # 10% of closed issues
                    closed_date += timedelta(hours=random.randint(24, 120))
            else:
                closed_date = None
            
            # Due dates more variable
            if random.random() > 0.3:  # 70% of issues have due dates
                # Due date relative to creation date
                due_date_days = int(np.random.normal(14, 7))  # Mean of 14 days, std dev of 7
                due_date_days = max(1, due_date_days)  # Minimum 1 day
                due_date = created_date + timedelta(days=due_date_days)
            else:
                due_date = None
            
            # Issue type distribution - slightly more varied
            issue_types = ["Bug", "Task", "Story", "Epic"]
            issue_weights = [0.3, 0.4, 0.2, 0.1]
            
            # Some repos have different issue type distributions
            if repo_name == "frontend":
                issue_weights = [0.25, 0.35, 0.3, 0.1]  # More stories in frontend
            elif repo_name == "backend":
                issue_weights = [0.35, 0.4, 0.15, 0.1]  # More bugs in backend
            elif repo_name == "infra":
                issue_weights = [0.3, 0.45, 0.1, 0.15]  # More tasks and epics in infra
                
            issue_type = weighted_choice(issue_types, issue_weights)
            
            # Status based on whether it's closed
            if is_closed:
                status = random.choice(["Done", "Resolved"])
            else:
                # More variation in open statuses
                status_options = ["To Do", "In Progress", "In Review", "Blocked", "In Testing"]
                status_weights = [0.2, 0.4, 0.2, 0.1, 0.1]
                status = weighted_choice(status_options, status_weights)
            
            # Resolution if closed
            resolution = random.choice(["Fixed", "Done", "Won't Fix", "Duplicate", "Cannot Reproduce"]) if is_closed else None
            
            # Priority with more variability by team and issue type
            priority_options = ["Highest", "High", "Medium", "Low", "Lowest"]
            
            # Default weights
            priority_weights = [0.1, 0.2, 0.4, 0.2, 0.1]
            
            # Bugs tend to be higher priority
            if issue_type == "Bug":
                priority_weights = [0.2, 0.3, 0.3, 0.1, 0.1]
            # Epics tend to be more balanced
            elif issue_type == "Epic":
                priority_weights = [0.15, 0.25, 0.35, 0.15, 0.1]
                
            priority = weighted_choice(priority_options, priority_weights)
            
            # Different issue labels & components with more variability
            possible_labels = ["backend", "frontend", "security", "performance", "ux", "documentation", 
                              "tech-debt", "feature", "enhancement", "critical", "accessibility"]
            
            # Number of labels follows a more realistic distribution
            num_labels_dist = [0, 1, 1, 2, 2, 2, 3, 3, 4]  # More weight to 1-3 labels
            num_labels = random.choice(num_labels_dist)
            labels = random.sample(possible_labels, num_labels) if num_labels > 0 else []
            
            possible_components = ["API", "UI", "Database", "Authentication", "Reporting", "Infrastructure", 
                                  "Frontend", "Backend", "Testing", "Documentation", "Deployment", "Mobile"]
            
            # Number of components follows a variable distribution
            num_components_dist = [0, 0, 1, 1, 1, 1, 2, 2, 3]  # More weight to 1-2 components
            num_components = random.choice(num_components_dist)
            components = random.sample(possible_components, num_components) if num_components > 0 else []
            
            # Sprint with variable naming patterns and some issues not in sprints
            if random.random() > 0.25:  # 75% in a sprint
                # Different sprint naming patterns
                sprint_patterns = [
                    f"Sprint {random.randint(10, 40)}",
                    f"Sprint {random.randint(2023, 2024)}-{random.randint(1, 26)}",
                    f"{random.choice(['Q1', 'Q2', 'Q3', 'Q4'])}-Sprint-{random.randint(1, 13)}"
                ]
                sprint = random.choice(sprint_patterns)
            else:
                sprint = None
            
            # Story points with more variability (Fibonacci sequence common in Agile)
            if issue_type in ["Story", "Task", "Bug"] and random.random() > 0.25:
                story_point_options = [0.5, 1, 2, 3, 5, 8, 13, 21]
                
                # Weight by complexity
                if complexity_factor < 0.8:
                    story_points = random.choice([0.5, 1, 2, 3])
                elif complexity_factor < 1.2:
                    story_points = random.choice([2, 3, 5, 8])
                else:
                    story_points = random.choice([5, 8, 13, 21])
            else:
                story_points = None
                
            # Epic link (for non-epics) with more variability
            epic_link = None
            if issue_type != "Epic" and random.random() > 0.4:
                epic_link = f"{project_key}-{random.randint(1, 20)}"
                
            # Assign based on repo focus and individual characteristics
            # First select a team based on repo focus
            team_weights = [team_info["repo_focus"][repo_name] for team_name, team_info in TEAM_CONFIG.items()]
            team_name = weighted_choice(list(TEAM_CONFIG.keys()), team_weights)
            
            # Get team productivity factor from stored value
            team_prod_factor = team_productivity[team_name]
            
            # Then select team members with bias based on issue characteristics
            team_members = [member for member, team in team_member_map.items() if team == team_name]
            
            # Weighted selection of author based on activity level and specialization
            author_weights = []
            for member in team_members:
                char = dev_characteristics[member]
                weight = char["activity"]  # Base on activity level
                
                # Adjust based on specialization for this issue type
                if issue_type == "Bug":
                    weight *= char["specializations"]["bug_fixing"]
                elif issue_type == "Epic":
                    weight *= char["specializations"]["features"]
                
                # Consider complexity preference
                weight *= (1 + (complexity_factor - 1) * (char["complexity_preference"] - 1))
                
                author_weights.append(weight)
            
            # Normalize weights
            total_weight = sum(author_weights)
            if total_weight > 0:
                author_weights = [w/total_weight for w in author_weights]
                author = random.choices(team_members, weights=author_weights, k=1)[0]
            else:
                author = random.choice(team_members)
            
            # Assignee is sometimes different, sometimes the same, sometimes null
            if random.random() > 0.2:  # 80% of issues have assignees
                if random.random() > 0.3:  # 70% of assigned issues go to a different person
                    assignees = [m for m in team_members if m != author]
                    if assignees:
                        assignee = random.choice(assignees)
                    else:
                        assignee = author
                else:
                    assignee = author
            else:
                assignee = None
            
            # Number of comments varies by complexity and issue type
            base_comments = int(np.random.normal(5, 4))  # Mean of 5 comments
            comment_factor = 1.0
            
            # More complex issues tend to have more comments
            comment_factor *= complexity_factor
            
            # Different issue types have different comment patterns
            if issue_type == "Bug":
                comment_factor *= 1.2  # Bugs often have more back-and-forth
            elif issue_type == "Epic":
                comment_factor *= 1.5  # Epics often have more discussion
                
            comment_count = max(0, int(base_comments * comment_factor))
            
            # Create issue with Jira fields
            issue_id = i + 1 + (repo_idx * ISSUES_PER_REPO)
            issue_key = f"{project_key}-{issue_id}"
            
            # Store issue key for later reference
            issue_id_to_key[issue_id] = issue_key
            
            # Create more varied issue titles
            title_prefixes = ["Add", "Fix", "Update", "Implement", "Refactor", "Optimize", "Remove", "Investigate", "Improve"]
            title_components = ["functionality", "feature", "component", "module", "integration", "API", "UI element", "workflow", "process"]
            
            if issue_type == "Bug":
                title = f"{issue_type}: {random.choice(['Fix', 'Address', 'Resolve'])} {random.choice(['issue with', 'bug in', 'problem with'])} {random.choice(components) if components else random.choice(title_components)} in {repo_name}"
            else:
                title = f"{issue_type}: {random.choice(title_prefixes)} {random.choice(components) if components else random.choice(title_components)} for {repo_name}"
            
            issue = Issue(
                issue_id=issue_id,
                issue_key=issue_key,
                project_key=project_key,
                repo=repo_path,
                title=title,
                description=f"This is a mock description for issue #{i} in {repo_name}.\n\nSteps to reproduce:\n1. Step one\n2. Step two\n3. Step three",
                issue_type=issue_type,
                author=author,
                assignee=assignee,
                created_at=created_date,
                updated_at=updated_date,
                closed_at=closed_date,
                due_date=due_date,
                status=status,
                resolution=resolution,
                priority=priority,
                comment_count=comment_count,
                labels=labels,
                components=components,
                sprint=sprint,
                story_points=story_points,
                epic_link=epic_link
            )
            
            all_issues.append(issue)
            
            # Batch insert if we've reached the batch size
            if len(all_issues) >= BATCH_SIZE:
                Issue.objects.insert(all_issues)
                all_issues = []
    
    # Insert any remaining issues
    if all_issues:
        Issue.objects.insert(all_issues)
    
    print(f"Generated {ISSUES_PER_REPO * len(REPOS)} issues with variable lead times")
    
    # -------------------------------------------------------------------------
    # Generate PRs with references to issues and variable review patterns
    # -------------------------------------------------------------------------
    print(f"Generating PRs ({PRS_PER_REPO} per repo) with variable review patterns...")
    all_prs = []
    
    # Track PR IDs and their authors by repo for later reference
    pr_ids_by_repo = {repo_name: [] for repo_name in REPOS}
    pr_authors_by_id = {}
    
    for repo_idx, repo_name in enumerate(REPOS):
        repo_path = f"{ORG_NAME}/{repo_name}"
        
        for i in tqdm(range(PRS_PER_REPO), desc=f"PRs for {repo_name}"):
            # Random dates within range, with more clustering and variability
            created_date = random_date(SIMULATION_START_DATE, SIMULATION_END_DATE, "variable")
            
            # PR complexity affects review time
            complexity_factor = np.random.normal(1.0, 0.6)  
            complexity_factor = max(0.3, min(complexity_factor, 3.5))  # Allow wider range
            
            # Some PRs have very long review times (outliers)
            review_time_outlier = random.random() < 0.08  # 8% of PRs
            
            # Calculate review time with high variability
            if review_time_outlier:
                # Outlier review time - much longer
                review_time_hours = random.randint(72, 240)  # 3-10 days
            else:
                # Normal review time with variability based on complexity
                base_review_time = random.randint(1, 48)  # 1-48 hours base
                review_time_hours = int(base_review_time * complexity_factor)
            
            # Some PRs are still open with more variable distribution
            is_closed = random.random() > (0.2 + 0.05 * complexity_factor)  # More complex PRs less likely to be closed
            
            # Not all closed PRs are merged - some are abandoned/rejected
            is_merged = is_closed and random.random() > (0.1 + 0.1 * complexity_factor)  # More complex PRs more likely to be rejected
            
            # Calculate closed date with variable review time
            if is_closed:
                closed_date = created_date + timedelta(hours=review_time_hours)
                
                # Some PRs are reopened and closed again
                if random.random() < 0.05:  # 5% of closed PRs
                    closed_date += timedelta(hours=random.randint(24, 72))
            else:
                closed_date = None
                
            merged_date = closed_date if is_merged else None
            
            # PR review count with more variability based on complexity
            if complexity_factor < 1.0:
                review_count = random.randint(0, 2)
            elif complexity_factor < 2.0:
                review_count = random.randint(1, 4)
            else:
                review_count = random.randint(2, 7)  # More complex PRs get more reviews
            
            # PR size varies more widely
            # Use long-tail distribution for file changes and lines
            changed_files = int(long_tail_distribution(1, 50, shape=1.5))
            
            # Lines changed increases with file count but with variability
            base_lines = changed_files * random.randint(5, 50)
            additions = int(base_lines * random.uniform(0.5, 1.5))
            deletions = int(base_lines * random.uniform(0.2, 1.0))
            
            # Link to issues - more variable linking patterns
            linked_issue_key = None
            link_probability = 0.7  # Base probability
            
            # Larger PRs more likely to link to issues
            if changed_files > 10:
                link_probability += 0.2
                
            if random.random() < link_probability:
                project_key = PROJECT_KEYS[repo_name]
                # Get a random issue ID within the range for this repo
                issue_idx = random.randint(0, ISSUES_PER_REPO - 1)
                issue_id = issue_idx + 1 + (repo_idx * ISSUES_PER_REPO)
                linked_issue_key = issue_id_to_key.get(issue_id)
            
            # Assign based on repo focus and individual characteristics
            # First select a team based on repo focus
            team_weights = [team_info["repo_focus"][repo_name] for team_name, team_info in TEAM_CONFIG.items()]
            team_name = weighted_choice(list(TEAM_CONFIG.keys()), team_weights)
            
            # Get team productivity factor from stored value
            team_prod_factor = team_productivity[team_name]
            
            # Then select team members with bias based on PR characteristics
            team_members = [member for member, team in team_member_map.items() if team == team_name]
            
            # Weighted selection of author based on activity level and PR size preference
            author_weights = []
            for member in team_members:
                char = dev_characteristics[member]
                weight = char["activity"]  # Base on activity level
                
                # Adjust based on preference for PR size
                size_factor = (changed_files / 10.0) - 1.0  # -0.9 for small PRs, >0 for large PRs
                weight *= (1 + size_factor * (char["task_size_preference"] - 1))
                
                author_weights.append(max(0.1, weight))  # Ensure positive weight
            
            # Normalize weights
            total_weight = sum(author_weights)
            if total_weight > 0:
                author_weights = [w/total_weight for w in author_weights]
                author = random.choices(team_members, weights=author_weights, k=1)[0]
            else:
                author = random.choice(team_members)
            
            # Number of comments varies by PR complexity and size
            base_comments = int(np.random.normal(3, 3))  # Mean of 3 comments
            comment_factor = 1.0
            
            # More complex PRs tend to have more comments
            comment_factor *= complexity_factor
            
            # Larger PRs tend to have more comments
            if changed_files > 10:
                comment_factor *= 1.5
            
            comment_count = max(0, int(base_comments * comment_factor))
            
            # PR title and body
            # PR title with proper issue reference format [PROJECT-123]
            if linked_issue_key:
                title = f"[{linked_issue_key}] {random.choice(common_verbs)} {random.choice(common_targets)} in {repo_name}"
            else:
                title = f"{random.choice(common_verbs)} {random.choice(common_targets)} in {repo_name}"
            
            # Generate a PR body that references the issue (not stored in DB but used for message)
            body = f"""
            This PR implements changes for {linked_issue_key if linked_issue_key else "feature development"}.
            
            {f"Fixes [{linked_issue_key}]" if linked_issue_key else ""}
            """
            
            pr_id = i + 1 + (repo_idx * PRS_PER_REPO)
            
            # Store PR ID and author for later reference
            pr_ids_by_repo[repo_name].append(pr_id)
            pr_authors_by_id[pr_id] = author
            
            pr = PullRequest(
                pr_id=pr_id,
                repo=repo_path,
                title=title,
                author=author,
                created_at=created_date,
                closed_at=closed_date,
                merged_at=merged_date,
                state="closed" if is_closed else "open",
                review_count=review_count,
                comment_count=comment_count,
                additions=additions,
                deletions=deletions,
                changed_files=changed_files
                # Note: linked_issue and body don't exist in the model
            )
            
            all_prs.append(pr)
            
            # Batch insert if we've reached the batch size
            if len(all_prs) >= BATCH_SIZE:
                PullRequest.objects.insert(all_prs)
                all_prs = []
    
    # Insert any remaining PRs
    if all_prs:
        PullRequest.objects.insert(all_prs)
    
    print(f"Generated {PRS_PER_REPO * len(REPOS)} PRs with variable review patterns")
    
    # -------------------------------------------------------------------------
    # Generate commits with references to PRs and variable frequencies
    # -------------------------------------------------------------------------
    print(f"Generating commits ({COMMITS_PER_REPO} per repo) with variable frequencies...")
    all_commits = []
    
    # Different commit frequency patterns by developer
    # Note: This was simplified as we're using cluster-based commit patterns below
    # which accomplishes the same goal more effectively
    
    for repo_idx, repo_name in enumerate(REPOS):
        repo_path = f"{ORG_NAME}/{repo_name}"
        pr_ids = pr_ids_by_repo[repo_name]
        
        # Create clusters of commit dates to simulate real development patterns
        num_clusters = random.randint(30, 100)  # Number of development "bursts"
        cluster_centers = []
        
        for _ in range(num_clusters):
            # Create a random center within the date range
            center_date = random_date(SIMULATION_START_DATE, SIMULATION_END_DATE, "uniform")
            # Random cluster size (how many commits in this burst)
            cluster_size = int(np.random.normal(COMMITS_PER_REPO / num_clusters, COMMITS_PER_REPO / (num_clusters * 3)))
            cluster_size = max(1, cluster_size)
            # Random cluster spread (how spread out in time)
            cluster_spread_hours = random.randint(1, 72)
            
            cluster_centers.append((center_date, cluster_size, cluster_spread_hours))
        
        # Track commits assigned to each PR for realistic batching
        commits_per_pr = {}
        
        for i in tqdm(range(COMMITS_PER_REPO), desc=f"Commits for {repo_name}"):
            # Choose a random cluster based on its size
            weights = [size for _, size, _ in cluster_centers]
            total_weight = sum(weights)
            if total_weight == 0:
                # Fallback if all clusters are depleted
                committed_date = random_date(SIMULATION_START_DATE, SIMULATION_END_DATE, "uniform", weekday_bias=True)
            else:
                # Normalize weights
                weights = [w/total_weight for w in weights]
                chosen_idx = random.choices(range(len(cluster_centers)), weights=weights)[0]
                center_date, size, spread_hours = cluster_centers[chosen_idx]
                
                # Reduce the size of the chosen cluster
                cluster_centers[chosen_idx] = (center_date, size-1, spread_hours)
                
                # Generate date within the cluster
                time_offset = np.random.normal(0, spread_hours * 0.3)
                time_offset = max(-spread_hours, min(time_offset, spread_hours))
                committed_date = center_date + timedelta(hours=time_offset)
                
                # Ensure date is within simulation range and apply weekday bias
                committed_date = max(SIMULATION_START_DATE, min(committed_date, SIMULATION_END_DATE))
                
                # Apply weekday bias directly (70% chance to move weekend commits to weekdays)
                if committed_date.weekday() >= 5 and random.random() < 0.7:
                    # Move to previous Friday or next Monday
                    if random.random() < 0.5:
                        # Go forward to Monday
                        days_to_add = 7 - committed_date.weekday()
                        committed_date += timedelta(days=days_to_add)
                    else:
                        # Go backward to Friday
                        days_to_subtract = committed_date.weekday() - 4
                        committed_date -= timedelta(days=days_to_subtract)
            
            # Add realistic hour of day based on developer patterns
            dev_char = dev_characteristics.get(author, {})
            work_pattern = "business"
            if "work_pattern" in dev_char:
                if dev_char["work_pattern"] == 0:
                    work_pattern = "distributed"
                elif dev_char["work_pattern"] == 2:
                    work_pattern = "night_owl"
                    
            hour = random_hour_of_day(work_pattern)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            committed_date = committed_date.replace(hour=hour, minute=minute, second=second)
            
            # Link to PR with variable patterns
            # Some commits are not linked to any PR
            if pr_ids and random.random() < 0.8:
                if random.random() < 0.7:  # 70% chance to select by PR commit count for realistic batching
                    pr_weights = []
                    for pr_id in pr_ids:
                        # Prefer PRs with some commits but not too many
                        count = commits_per_pr.get(pr_id, 0)
                        if count == 0:
                            weight = 3.0  # High chance for PRs with no commits
                        elif count < 5:
                            weight = 5.0  # Higher chance for PRs with few commits
                        elif count < 10:
                            weight = 2.0  # Medium chance
                        else:
                            weight = 0.5  # Low chance for PRs with many commits
                        pr_weights.append(weight)
                    
                    # Normalize weights
                    total_weight = sum(pr_weights)
                    pr_weights = [w/total_weight for w in pr_weights]
                    linked_pr_id = random.choices(pr_ids, weights=pr_weights)[0]
                else:
                    linked_pr_id = random.choice(pr_ids)
                
                # Increment commit count for this PR
                commits_per_pr[linked_pr_id] = commits_per_pr.get(linked_pr_id, 0) + 1
            else:
                linked_pr_id = None
            
            # Assign author based on repo focus and individual characteristics
            # First select a team based on repo focus
            team_weights = [team_info["repo_focus"][repo_name] for team_name, team_info in TEAM_CONFIG.items()]
            team_name = weighted_choice(list(TEAM_CONFIG.keys()), team_weights)
            
            # Then select team members with bias based on commit patterns
            team_members = [member for member, team in team_member_map.items() if team == team_name]
            
            # Weighted selection of author based on activity level and commit patterns
            author_weights = []
            for member in team_members:
                char = dev_characteristics[member]
                
                # Base on activity level
                weight = char["activity"] * 0.5 + 0.5  # Soften the impact of activity level
                
                # For linked PRs, prefer the PR author
                if linked_pr_id:
                    pr_author = pr_authors_by_id.get(linked_pr_id)
                    if pr_author and pr_author == member:
                        # This member is the PR author, give higher weight
                        weight *= 3.0
                
                author_weights.append(max(0.1, weight))  # Ensure positive weight
            
            # Normalize weights
            total_weight = sum(author_weights)
            if total_weight > 0:
                author_weights = [w/total_weight for w in author_weights]
                author = random.choices(team_members, weights=author_weights, k=1)[0]
            else:
                author = random.choice(team_members)
            
            # Generate commit size with more variability
            # Different developers have different commit size patterns
            dev_char = dev_characteristics[author]
            size_preference = dev_char["task_size_preference"]
            
            # Use long-tail distribution for additions/deletions
            # Smaller or larger based on developer preference
            additions = int(long_tail_distribution(3, 300, shape=1.2) * size_preference)
            deletions = int(long_tail_distribution(0, 100, shape=1.5) * size_preference)
            files_changed = max(1, int(np.random.normal(3, 2) * size_preference))
            
            # Commit message with proper issue/PR reference format [PROJECT-123]
            # First define the message content
            message_content = random.choice(message_styles)
            
            # Then add the appropriate prefix
            if linked_issue_key:
                # Include issue key reference
                message = f"[{linked_issue_key}] {message_content}"
            elif linked_pr_id:
                # Just PR reference if no issue
                message = f"[PR-{linked_pr_id}] {message_content}"
            else:
                # No references
                message = message_content
            
            commit = Commit(
                sha=f"{repo_path}-commit-{i}-{int(time.time())}",
                repo=repo_path,
                author=author,
                committed_at=committed_date,
                message=message,
                additions=additions,
                deletions=deletions,
                files_changed=files_changed
                # Note: linked_pr doesn't exist in the model
            )
            
            all_commits.append(commit)
            
            # Batch insert if we've reached the batch size
            if len(all_commits) >= BATCH_SIZE:
                Commit.objects.insert(all_commits)
                all_commits = []
    
    # Insert any remaining commits
    if all_commits:
        Commit.objects.insert(all_commits)
    
    print(f"Generated {COMMITS_PER_REPO * len(REPOS)} commits with variable patterns")
    
    # -------------------------------------------------------------------------
    # Generate workflow runs with long-tail distribution for run times
    # -------------------------------------------------------------------------
    print(f"Generating workflow runs ({WORKFLOW_RUNS_PER_REPO} per repo) with long-tail execution times...")
    all_workflows = []
    
    for repo_idx, repo_name in enumerate(REPOS):
        repo_path = f"{ORG_NAME}/{repo_name}"
        pr_ids = pr_ids_by_repo[repo_name]
        
        # Create success rate trends over time to simulate improvement or degradation
        success_rate_trend = random.choice([
            "improving",      # Success rate increases over time
            "degrading",      # Success rate decreases over time
            "stable",         # Success rate stays relatively stable
            "fluctuating",    # Success rate goes up and down
            "step_change"     # Success rate changes dramatically at some point
        ])
        
        # For step change, decide when it happens
        step_change_point = random.uniform(0.3, 0.7)  # Between 30% and 70% through the timeline
        
        # Base success rates
        if success_rate_trend == "improving":
            start_success_rate = 0.6 + random.uniform(0, 0.2)
            end_success_rate = 0.8 + random.uniform(0, 0.15)
        elif success_rate_trend == "degrading":
            start_success_rate = 0.8 + random.uniform(0, 0.15)
            end_success_rate = 0.6 + random.uniform(0, 0.2)
        elif success_rate_trend == "stable":
            mid_rate = 0.75 + random.uniform(-0.1, 0.1)
            start_success_rate = end_success_rate = mid_rate
        elif success_rate_trend == "fluctuating":
            mid_rate = 0.75 + random.uniform(-0.1, 0.1)
            fluctuation = 0.1 + random.uniform(0, 0.1)
            start_success_rate = end_success_rate = mid_rate
            # Fluctuation handled during run generation
        else:  # step_change
            if random.random() < 0.5:  # 50% chance of improvement
                start_success_rate = 0.65 + random.uniform(-0.1, 0.1)
                end_success_rate = 0.85 + random.uniform(-0.05, 0.1)
            else:  # 50% chance of degradation
                start_success_rate = 0.85 + random.uniform(-0.05, 0.1)
                end_success_rate = 0.65 + random.uniform(-0.1, 0.1)
        
        for i in tqdm(range(WORKFLOW_RUNS_PER_REPO), desc=f"Workflow runs for {repo_name}"):
            # Random date with weekday bias
            created_date = random_date(SIMULATION_START_DATE, SIMULATION_END_DATE, "variable", weekday_bias=True)
            

            # Execution time varies by workflow type with true long-tail distribution
            # Different workflow types have different distributions
            workflow_types = ["light_ci", "medium_test", "heavy_deployment"]
            workflow_weights = [0.5, 0.3, 0.2]  # More light CI runs than deployments
            workflow_type = weighted_choice(workflow_types, workflow_weights)

            # Add hour of day based on workflow type (deployments often during non-peak hours)
            if workflow_type == "heavy_deployment":
                # Deployments often happen in early morning or evening
                hour_options = list(range(6, 9)) + list(range(17, 20))
                hour = random.choice(hour_options)
            else:
                # Regular CI typically follows work patterns
                hour = random_hour_of_day("business")
                
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            created_date = created_date.replace(hour=hour, minute=minute, second=second)
            
            # Calculate where in the timeline this run falls (0 to 1)
            timeline_position = (created_date - SIMULATION_START_DATE).total_seconds() / \
                               (SIMULATION_END_DATE - SIMULATION_START_DATE).total_seconds()
            
            # Calculate success rate based on trend
            if success_rate_trend == "improving" or success_rate_trend == "degrading":
                current_success_rate = start_success_rate + (end_success_rate - start_success_rate) * timeline_position
            elif success_rate_trend == "fluctuating":
                # Create a sine wave pattern with random phase
                phase = random.uniform(0, 6.28)  # 0 to 2π
                cycles = 3 + random.uniform(0, 2)  # Number of cycles over the time period
                current_success_rate = start_success_rate + \
                                      0.15 * np.sin(phase + cycles * 6.28 * timeline_position)
            elif success_rate_trend == "step_change":
                if timeline_position < step_change_point:
                    current_success_rate = start_success_rate
                else:
                    # Linear blend right at the step change point for a bit of smoothing
                    if timeline_position < step_change_point + 0.05:
                        blend_factor = (timeline_position - step_change_point) / 0.05
                        current_success_rate = start_success_rate * (1 - blend_factor) + end_success_rate * blend_factor
                    else:
                        current_success_rate = end_success_rate
            else:  # stable
                # Add small random variations to stable
                current_success_rate = start_success_rate + random.uniform(-0.05, 0.05)
            
            # Clamp to reasonable range
            current_success_rate = max(0.5, min(current_success_rate, 0.98))
            
            # Simulate both fast and slow runner pickups with long tail distribution
            pickup_delay = long_tail_distribution(0.1, 1800, shape=1.2)  # 0.1sec to 30min
            
            started_date = created_date + timedelta(seconds=pickup_delay)
            
            
            
            if workflow_type == "light_ci":
                # Lighter CI jobs - mostly quick with occasional slowness
                execution_time = long_tail_distribution(15, 1800, shape=1.5)  # 15sec to 30min
            elif workflow_type == "medium_test":
                # Medium tests - wider range
                execution_time = long_tail_distribution(180, 3600, shape=1.3)  # 3min to 60min
            else:  # heavy_deployment
                # Heavy deployment jobs - long with high variability
                execution_time = long_tail_distribution(300, 7200, shape=1.1)  # 5min to 2hrs
            
            completed_date = started_date + timedelta(seconds=execution_time)
            
            # Different workflow conclusions with variable success rates
            conclusions = ["success", "failure", "cancelled", "timed_out"]
            
            # Base weights on current success rate
            success_weight = current_success_rate
            failure_weight = (1 - current_success_rate) * 0.7  # 70% of non-success is failure
            cancelled_weight = (1 - current_success_rate) * 0.2  # 20% is cancelled
            timeout_weight = (1 - current_success_rate) * 0.1  # 10% is timeout
            
            weights = [success_weight, failure_weight, cancelled_weight, timeout_weight]
            conclusion = weighted_choice(conclusions, weights)
            
            # More complex runs more likely to fail
            if execution_time > 1800 and conclusion == "success":  # For runs over 30 minutes
                if random.random() < 0.3:  # 30% chance to override to failure
                    conclusion = "failure"
            
            # Different runner types with different reliability
            runner_type = random.choice(["GitHub-hosted", "self-hosted"])
            if runner_type == "GitHub-hosted":
                runner_name = random.choice(["ubuntu-latest", "windows-latest", "macos-latest"])
                
                # Different OS runners have different reliability patterns
                if runner_name == "windows-latest" and conclusion == "success":
                    if random.random() < 0.15:  # Windows slightly less reliable
                        conclusion = random.choice(["failure", "timed_out"])
            else:
                runner_name = random.choice(["custom-runner-1", "custom-runner-2", "custom-large-runner"])
                
                # Custom runners might have specific issues
                if runner_name == "custom-runner-1" and conclusion == "success":
                    if random.random() < 0.1:  # Slight reliability issues
                        conclusion = "failure"
            
            # Link to PR - more variable by workflow and repo type
            linked_pr_id = None
            link_probability = 0.7  # Base probability
            
            # Frontend repo may have more workflow runs not linked to PRs
            if repo_name == "frontend":
                link_probability -= 0.1
            
            # Deployment workflows less likely to be directly linked to PRs
            if workflow_type == "heavy_deployment":
                link_probability -= 0.2
            
            if pr_ids and random.random() < link_probability:
                linked_pr_id = random.choice(pr_ids)
            
            # Branch distribution - more realistic patterns
            if linked_pr_id and random.random() < 0.8:
                # If linked to PR, use a feature branch name with different patterns
                branch_patterns = [
                    f"feature/PR-{linked_pr_id}",
                    f"feature/{random.choice(['add', 'fix', 'update'])}-{random.choice(['auth', 'ui', 'api', 'docs'])}-{linked_pr_id}",
                    f"bugfix/issue-{random.randint(100, 999)}",
                    f"user/{random.choice(['dev', 'jsmith', 'apatterson'])}/{random.choice(['feature', 'fix', 'refactor'])}-{random.randint(1, 99)}"
                ]
                branch = random.choice(branch_patterns)
            else:
                # More realistic distribution of branches
                branch_options = ["main"] * 15 + ["master"] * 5 + ["develop"] * 8 + ["staging"] * 5 + ["release"] * 3
                for i in range(5):
                    branch_options.append(f"feature-{i}")
                branch = random.choice(branch_options)
            
            # Workflow name based on type and repo with more variation
            workflow_categories = {
                "CI": ["Build", "Test", "Lint", "Validate", "Verify"],
                "Deploy": ["Deploy to Dev", "Deploy to Staging", "Deploy to Production", "Release"],
                "Test": ["Unit Tests", "Integration Tests", "E2E Tests", "Acceptance Tests", "Performance Tests"],
                "Checks": ["Security Scan", "Dependency Check", "Code Quality", "Coverage"]
            }
            
            if workflow_type == "light_ci":
                category_weights = [0.6, 0.1, 0.2, 0.1]  # More CI for light workflows
            elif workflow_type == "medium_test":
                category_weights = [0.3, 0.1, 0.5, 0.1]  # More Tests for medium workflows
            else:  # heavy_deployment
                category_weights = [0.2, 0.6, 0.1, 0.1]  # More Deploy for heavy workflows
            
            workflow_category = weighted_choice(list(workflow_categories.keys()), category_weights)
            workflow_subtype = random.choice(workflow_categories[workflow_category])
            
            # Sometimes workflows have team names in them
            if random.random() < 0.3:
                team_prefix = f"{random.choice(list(TEAM_CONFIG.keys()))}: "
            else:
                team_prefix = ""
            
            workflow_name = f"{team_prefix}{repo_name.capitalize()} {workflow_category}: {workflow_subtype}"
            
            # Use unique ID generation to avoid duplicates
            # MongoDB will auto-generate _id if not provided
            workflow = WorkflowRun(
                # Use timestamp in ID to guarantee uniqueness
                run_id=int(uuid.uuid4().int % (10 ** 10)),
                repo=repo_path,
                workflow_name=workflow_name,
                created_at=created_date,
                started_at=started_date,
                completed_at=completed_date,
                conclusion=conclusion,
                runner_name=runner_name,
                runner_type=runner_type,
                pickup_time_seconds=pickup_delay,
                execution_time_seconds=execution_time,
                branch=branch
                # Note: linked_pr doesn't exist in the model so we're not storing it
            )
            
            all_workflows.append(workflow)
            
            # Batch insert if we've reached the batch size
            if len(all_workflows) >= BATCH_SIZE:
                WorkflowRun.objects.insert(all_workflows)
                all_workflows = []
    
    # Insert any remaining workflow runs
    if all_workflows:
        WorkflowRun.objects.insert(all_workflows)
    
    print(f"Generated {WORKFLOW_RUNS_PER_REPO * len(REPOS)} workflow runs with long-tail execution times")
    
    # Report generation time
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"Mock data generation completed at {datetime.now()}")
    print(f"Total generation time: {elapsed:.2f} seconds")
    
    # Summary of generated data
    print("\nGENERATED DATA SUMMARY")
    print("=====================")
    print(f"Teams: {len(teams)}")
    print(f"Repositories: {len(repositories)}")
    print(f"Issues: {ISSUES_PER_REPO * len(REPOS)}")
    print(f"Pull Requests: {PRS_PER_REPO * len(REPOS)}")
    print(f"Commits: {COMMITS_PER_REPO * len(REPOS)}")
    print(f"Workflow Runs: {WORKFLOW_RUNS_PER_REPO * len(REPOS)}")

if __name__ == "__main__":
    # Connect to MongoDB
    import os
    mongo_uri = os.getenv("MONGO_URI", "mongodb://admin:password@0.0.0.0:27017/github_metrics?authSource=admin")
    me.connect(host=mongo_uri)
    
    # Generate mock data
    generate_mock_data()