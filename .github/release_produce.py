from git import Repo
from datetime import datetime
import pytz
from packaging.version import parse

repo_path = "/home/runner/work/Test"
Repo.clone_from(
    "https://github.com/ToolDelta/ToolDelta.git",
    to_path=repo_path,
    branch="main",
)
# repo_path = "/home/xingchen/WorkSpace/ToolDelta/.github/test"
repo = Repo(repo_path)
tags = [tag for tag in repo.tags if tag.name != "binaries"]
max_version = max(tags, key=lambda tag: parse(tag.name), default=None)
if max_version:
    utc_time = max_version.commit.committed_datetime
    local_tz = pytz.timezone("Asia/Shanghai")
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
    tag_creation_date = local_time.strftime("%Y-%m-%d %H:%M")
    print(f"最大版本号: {max_version.name}")
    print(f"Tag {max_version.name} 的创建日期是: {tag_creation_date}")
else:
    exit()

tag_creation_datetime = datetime.strptime(tag_creation_date, "%Y-%m-%d %H:%M")

new_commits_log = repo.git.log(
    '--pretty={"commit":"%H","author":"%aN","summary":"%s","date":"%cd"}',
    since=tag_creation_datetime,
    date="format:%Y-%m-%d %H:%M",
)

new_commits_list = new_commits_log.split("\n")
new_real_commits_list = [eval(item) for item in new_commits_list if item]
print(new_real_commits_list)

ToolDeltaVersion = open("version").read().strip()

with open("changelog.md", "w") as CHANGELOG:
    CHANGELOG.write(f"## ToolDelta Release v{ToolDeltaVersion} ({tag_creation_date})\n")
    for commit in new_real_commits_list:
        commit_id = commit["commit"]
        author = commit["author"]
        summary = commit["summary"]
        date = commit["date"]
        CHANGELOG.write(
            f"- [#{commit_id}](https://github.com/ToolDelta/commit/{commit_id}) [{author}](https://github.com/{author}) {summary} ({date})\n"
        )
    CHANGELOG.close()
