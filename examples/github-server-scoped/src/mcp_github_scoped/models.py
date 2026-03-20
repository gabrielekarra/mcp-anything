"""Data models for github-scoped MCP server."""

from dataclasses import dataclass
from typing import Any


@dataclass
class SecurityAdvisoriesListGlobalAdvisoriesParams:
    """Parameters for security_advisories_list_global_advisories."""
    ghsa_id: str | None = None
    type: str | None = None
    cve_id: str | None = None
    ecosystem: str | None = None
    severity: str | None = None
    cwes: dict | None = None
    is_withdrawn: bool | None = None
    affects: dict | None = None
    published: str | None = None
    updated: str | None = None
    modified: str | None = None
    epss_percentage: str | None = None
    epss_percentile: str | None = None
    before: str | None = None
    after: str | None = None
    direction: str | None = None
    per_page: int | None = None
    sort: str | None = None

@dataclass
class SecurityAdvisoriesGetGlobalAdvisoryParams:
    """Parameters for security_advisories_get_global_advisory."""
    ghsa_id: str

@dataclass
class GistsListParams:
    """Parameters for gists_list."""
    since: str | None = None
    per_page: int | None = None
    page: int | None = None

@dataclass
class GistsCreateParams:
    """Parameters for gists_create."""
    description: str | None = None
    files: dict
    public: dict | None = None

@dataclass
class GistsGetParams:
    """Parameters for gists_get."""
    gist_id: str

@dataclass
class GistsUpdateParams:
    """Parameters for gists_update."""
    gist_id: str
    description: str | None = None
    files: dict | None = None

@dataclass
class GetNotificationsParams:
    """Parameters for get_notifications."""
    all: bool | None = None
    participating: bool | None = None
    since: str | None = None
    before: str | None = None
    page: int | None = None
    per_page: int | None = None

@dataclass
class ActivityMarkNotificationsAsReadParams:
    """Parameters for activity_mark_notifications_as_read."""
    last_read_at: str | None = None
    read: bool | None = None

@dataclass
class ActivityGetThreadParams:
    """Parameters for activity_get_thread."""
    thread_id: int

@dataclass
class ActivityMarkThreadAsDoneParams:
    """Parameters for activity_mark_thread_as_done."""
    thread_id: int

@dataclass
class ActivitySetThreadSubscriptionParams:
    """Parameters for activity_set_thread_subscription."""
    thread_id: int
    ignored: bool | None = None

@dataclass
class OrgsListIssueTypesParams:
    """Parameters for orgs_list_issue_types."""
    org: str

@dataclass
class TeamsListParams:
    """Parameters for teams_list."""
    org: str
    per_page: int | None = None
    page: int | None = None
    team_type: str | None = None

@dataclass
class TeamsListMembersInOrgParams:
    """Parameters for teams_list_members_in_org."""
    org: str
    team_slug: str
    role: str | None = None
    per_page: int | None = None
    page: int | None = None

@dataclass
class ActionsDownloadJobLogsForWorkflowRunParams:
    """Parameters for actions_download_job_logs_for_workflow_run."""
    owner: str
    repo: str
    job_id: int

@dataclass
class ActionsListRepoWorkflowsParams:
    """Parameters for actions_list_repo_workflows."""
    owner: str
    repo: str
    per_page: int | None = None
    page: int | None = None

@dataclass
class ActionsGetWorkflowParams:
    """Parameters for actions_get_workflow."""
    owner: str
    repo: str
    workflow_id: dict

@dataclass
class ActionsCreateWorkflowDispatchParams:
    """Parameters for actions_create_workflow_dispatch."""
    owner: str
    repo: str
    workflow_id: dict
    ref: str
    inputs: dict | None = None
    return_run_details: bool | None = None

@dataclass
class ReposListBranchesParams:
    """Parameters for repos_list_branches."""
    owner: str
    repo: str
    protected: bool | None = None
    per_page: int | None = None
    page: int | None = None

@dataclass
class CodeScanningListAlertsForRepoParams:
    """Parameters for code_scanning_list_alerts_for_repo."""
    owner: str
    repo: str
    tool_name: str | None = None
    tool_guid: str | None = None
    page: int | None = None
    per_page: int | None = None
    ref: str | None = None
    pr: int | None = None
    direction: str | None = None
    before: str | None = None
    after: str | None = None
    sort: str | None = None
    state: str | None = None
    severity: str | None = None
    assignees: str | None = None

@dataclass
class CodeScanningGetAlertParams:
    """Parameters for code_scanning_get_alert."""
    owner: str
    repo: str
    alert_number: int

@dataclass
class ReposListCommitsParams:
    """Parameters for repos_list_commits."""
    owner: str
    repo: str
    sha: str | None = None
    path: str | None = None
    author: str | None = None
    committer: str | None = None
    since: str | None = None
    until: str | None = None
    per_page: int | None = None
    page: int | None = None

@dataclass
class ReposGetCommitParams:
    """Parameters for repos_get_commit."""
    owner: str
    repo: str
    page: int | None = None
    per_page: int | None = None
    ref: str

@dataclass
class ReposGetContentParams:
    """Parameters for repos_get_content."""
    owner: str
    repo: str
    path: str
    ref: str | None = None

@dataclass
class ReposCreateOrUpdateFileContentsParams:
    """Parameters for repos_create_or_update_file_contents."""
    owner: str
    repo: str
    path: str
    message: str
    content: str
    sha: str | None = None
    branch: str | None = None
    committer: dict | None = None
    author: dict | None = None

@dataclass
class ReposDeleteFileParams:
    """Parameters for repos_delete_file."""
    owner: str
    repo: str
    path: str
    message: str
    sha: str
    branch: str | None = None
    committer: dict | None = None
    author: dict | None = None

@dataclass
class DependabotListAlertsForRepoParams:
    """Parameters for dependabot_list_alerts_for_repo."""
    owner: str
    repo: str
    state: str | None = None
    severity: str | None = None
    ecosystem: str | None = None
    package: str | None = None
    manifest: str | None = None
    epss_percentage: str | None = None
    has: dict | None = None
    assignee: str | None = None
    scope: str | None = None
    sort: str | None = None
    direction: str | None = None
    before: str | None = None
    after: str | None = None
    per_page: int | None = None

@dataclass
class DependabotGetAlertParams:
    """Parameters for dependabot_get_alert."""
    owner: str
    repo: str
    alert_number: int

@dataclass
class ReposCreateForkParams:
    """Parameters for repos_create_fork."""
    owner: str
    repo: str
    organization: str | None = None
    name: str | None = None
    default_branch_only: bool | None = None

@dataclass
class GitCreateRefParams:
    """Parameters for git_create_ref."""
    owner: str
    repo: str
    ref: str
    sha: str

@dataclass
class GitGetTagParams:
    """Parameters for git_get_tag."""
    owner: str
    repo: str
    tag_sha: str

@dataclass
class GitGetTreeParams:
    """Parameters for git_get_tree."""
    owner: str
    repo: str
    tree_sha: str
    recursive: str | None = None

@dataclass
class IssuesListForRepoParams:
    """Parameters for issues_list_for_repo."""
    owner: str
    repo: str
    milestone: str | None = None
    state: str | None = None
    assignee: str | None = None
    type: str | None = None
    creator: str | None = None
    mentioned: str | None = None
    labels: str | None = None
    sort: str | None = None
    direction: str | None = None
    since: str | None = None
    per_page: int | None = None
    page: int | None = None

@dataclass
class IssuesCreateParams:
    """Parameters for issues_create."""
    owner: str
    repo: str
    title: dict
    body: str | None = None
    assignee: str | None = None
    milestone: dict | None = None
    labels: list | None = None
    assignees: list | None = None
    type: str | None = None

@dataclass
class IssuesGetParams:
    """Parameters for issues_get."""
    owner: str
    repo: str
    issue_number: int

@dataclass
class IssuesUpdateParams:
    """Parameters for issues_update."""
    owner: str
    repo: str
    issue_number: int
    title: dict | None = None
    body: str | None = None
    assignee: str | None = None
    state: str | None = None
    state_reason: str | None = None
    milestone: dict | None = None
    labels: list | None = None
    assignees: list | None = None
    issue_field_values: list | None = None
    type: str | None = None

@dataclass
class IssuesCreateCommentParams:
    """Parameters for issues_create_comment."""
    owner: str
    repo: str
    issue_number: int
    body: str

@dataclass
class IssuesAddSubIssueParams:
    """Parameters for issues_add_sub_issue."""
    owner: str
    repo: str
    issue_number: int
    sub_issue_id: int
    replace_parent: bool | None = None

@dataclass
class IssuesListLabelsForRepoParams:
    """Parameters for issues_list_labels_for_repo."""
    owner: str
    repo: str
    per_page: int | None = None
    page: int | None = None

@dataclass
class IssuesCreateLabelParams:
    """Parameters for issues_create_label."""
    owner: str
    repo: str
    name: str
    color: str | None = None
    description: str | None = None

@dataclass
class IssuesGetLabelParams:
    """Parameters for issues_get_label."""
    owner: str
    repo: str
    name: str

@dataclass
class PullsListParams:
    """Parameters for pulls_list."""
    owner: str
    repo: str
    state: str | None = None
    head: str | None = None
    base: str | None = None
    sort: str | None = None
    direction: str | None = None
    per_page: int | None = None
    page: int | None = None

@dataclass
class PullsCreateParams:
    """Parameters for pulls_create."""
    owner: str
    repo: str
    title: str | None = None
    head: str
    head_repo: str | None = None
    base: str
    body: str | None = None
    maintainer_can_modify: bool | None = None
    draft: bool | None = None
    issue: int | None = None

@dataclass
class PullsGetParams:
    """Parameters for pulls_get."""
    owner: str
    repo: str
    pull_number: int

@dataclass
class PullsUpdateParams:
    """Parameters for pulls_update."""
    owner: str
    repo: str
    pull_number: int
    title: str | None = None
    body: str | None = None
    state: str | None = None
    base: str | None = None
    maintainer_can_modify: bool | None = None

@dataclass
class PullsCreateReviewCommentParams:
    """Parameters for pulls_create_review_comment."""
    owner: str
    repo: str
    pull_number: int
    body: str
    commit_id: str
    path: str
    position: int | None = None
    side: str | None = None
    line: int | None = None
    start_line: int | None = None
    start_side: str | None = None
    in_reply_to: int | None = None
    subject_type: str | None = None

@dataclass
class PullsCreateReplyForReviewCommentParams:
    """Parameters for pulls_create_reply_for_review_comment."""
    owner: str
    repo: str
    pull_number: int
    comment_id: int
    body: str

@dataclass
class PullsMergeParams:
    """Parameters for pulls_merge."""
    owner: str
    repo: str
    pull_number: int
    commit_title: str | None = None
    commit_message: str | None = None
    sha: str | None = None
    merge_method: str | None = None

@dataclass
class PullsSubmitReviewParams:
    """Parameters for pulls_submit_review."""
    owner: str
    repo: str
    pull_number: int
    review_id: int
    body: str | None = None
    event: str

@dataclass
class PullsUpdateBranchParams:
    """Parameters for pulls_update_branch."""
    owner: str
    repo: str
    pull_number: int
    expected_head_sha: str | None = None

@dataclass
class ReposListReleasesParams:
    """Parameters for repos_list_releases."""
    owner: str
    repo: str
    per_page: int | None = None
    page: int | None = None

@dataclass
class ReposGetLatestReleaseParams:
    """Parameters for repos_get_latest_release."""
    owner: str
    repo: str

@dataclass
class ReposGetReleaseByTagParams:
    """Parameters for repos_get_release_by_tag."""
    owner: str
    repo: str
    tag: str

@dataclass
class SecretScanningListAlertsForRepoParams:
    """Parameters for secret_scanning_list_alerts_for_repo."""
    owner: str
    repo: str
    state: str | None = None
    secret_type: str | None = None
    resolution: str | None = None
    assignee: str | None = None
    sort: str | None = None
    direction: str | None = None
    page: int | None = None
    per_page: int | None = None
    before: str | None = None
    after: str | None = None
    validity: str | None = None
    is_publicly_leaked: bool | None = None
    is_multi_repo: bool | None = None
    hide_secret: bool | None = None

@dataclass
class SecretScanningGetAlertParams:
    """Parameters for secret_scanning_get_alert."""
    owner: str
    repo: str
    alert_number: int
    hide_secret: bool | None = None

@dataclass
class SecurityAdvisoriesListRepositoryAdvisoriesParams:
    """Parameters for security_advisories_list_repository_advisories."""
    owner: str
    repo: str
    direction: str | None = None
    sort: str | None = None
    before: str | None = None
    after: str | None = None
    per_page: int | None = None
    state: str | None = None

@dataclass
class ActivitySetRepoSubscriptionParams:
    """Parameters for activity_set_repo_subscription."""
    owner: str
    repo: str
    subscribed: bool | None = None
    ignored: bool | None = None

@dataclass
class ReposListTagsParams:
    """Parameters for repos_list_tags."""
    owner: str
    repo: str
    per_page: int | None = None
    page: int | None = None

@dataclass
class SearchCodeParams:
    """Parameters for search_code."""
    q: str
    sort: str | None = None
    order: str | None = None
    per_page: int | None = None
    page: int | None = None

@dataclass
class SearchIssuesAndPullRequestsParams:
    """Parameters for search_issues_and_pull_requests."""
    q: str
    sort: str | None = None
    order: str | None = None
    per_page: int | None = None
    page: int | None = None
    advanced_search: str | None = None

@dataclass
class SearchReposParams:
    """Parameters for search_repos."""
    q: str
    sort: str | None = None
    order: str | None = None
    per_page: int | None = None
    page: int | None = None

@dataclass
class SearchUsersParams:
    """Parameters for search_users."""
    q: str
    sort: str | None = None
    order: str | None = None
    per_page: int | None = None
    page: int | None = None

@dataclass
class ReposCreateForAuthenticatedUserParams:
    """Parameters for repos_create_for_authenticated_user."""
    name: str
    description: str | None = None
    homepage: str | None = None
    private: bool | None = None
    has_issues: bool | None = None
    has_projects: bool | None = None
    has_wiki: bool | None = None
    has_discussions: bool | None = None
    team_id: int | None = None
    auto_init: bool | None = None
    gitignore_template: str | None = None
    license_template: str | None = None
    allow_squash_merge: bool | None = None
    allow_merge_commit: bool | None = None
    allow_rebase_merge: bool | None = None
    allow_auto_merge: bool | None = None
    delete_branch_on_merge: bool | None = None
    squash_merge_commit_title: str | None = None
    squash_merge_commit_message: str | None = None
    merge_commit_title: str | None = None
    merge_commit_message: str | None = None
    has_downloads: bool | None = None
    is_template: bool | None = None

@dataclass
class ActivityListReposStarredByAuthenticatedUserParams:
    """Parameters for activity_list_repos_starred_by_authenticated_user."""
    sort: str | None = None
    direction: str | None = None
    per_page: int | None = None
    page: int | None = None

@dataclass
class ActivityStarRepoForAuthenticatedUserParams:
    """Parameters for activity_star_repo_for_authenticated_user."""
    owner: str
    repo: str

@dataclass
class ActivityUnstarRepoForAuthenticatedUserParams:
    """Parameters for activity_unstar_repo_for_authenticated_user."""
    owner: str
    repo: str

