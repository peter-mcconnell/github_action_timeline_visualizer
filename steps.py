#!/usr/bin/env python
import zipfile
import matplotlib.pyplot as plt
import re
import os
import io
import requests
import datetime

ACTION_LEN = 40

def download_workflow_logs(repo_name, workflow_id, token):
    if repo_name is None:
        print("GITHUB_REPOSITORY is not set")
        exit(1)
    owner, repo = repo_name.split('/')
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{workflow_id}/logs"
    print(f"Downloading logs from {url}")
    
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to get logs: {response.content}")

def parse_log(zip_bytes):
    time_action_pairs = []
    current_group = 'initializing ...'
    with io.BytesIO(zip_bytes) as zip_file:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            log_files = zip_ref.namelist()
            for file in log_files:
                if "/" in file: # we only analyze config files in the zips root
                    continue
                with zip_ref.open(file) as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.decode('utf-8')
                        if "##[" in line:
                            continue
                        if " [command]" in line:
                            current_group = line.split("[command]", 1)[1].rstrip()
                            continue
                        match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s(.+)', line)
                        if match:
                            timestamp = datetime.datetime.fromisoformat(match.group(1)[:19])
                            action = match.group(2)
                            if len(action) > ACTION_LEN:
                                action = action[:ACTION_LEN] + "..."
                            time_action_pairs.append((timestamp, action, current_group))
    return time_action_pairs

def calculate_durations(time_action_pairs):
    durations = []
    for i in range(len(time_action_pairs)-1):
        start_time, action, group = time_action_pairs[i]
        end_time, _, _ = time_action_pairs[i+1]
        duration = (end_time - start_time).total_seconds()
        durations.append((action, duration, group))
    return durations

def build_image(time_action_pairs, target):
    durations = calculate_durations(time_action_pairs)
    durations.sort(key=lambda x: x[1], reverse=True)

    actions, time_spent, groups = zip(*durations[:10])
    print(groups)

    plt.figure(figsize=(10, 8))
    rects = plt.barh(actions, time_spent, color='skyblue')
    plt.bar_label(rects, groups, padding=5, color='black')
    plt.xlabel('Time in Seconds')
    plt.ylabel('Log')
    plt.title('Top 10 Time-Consuming Areas from GitHub Actions Log')
    plt.gca().invert_yaxis()

    plt.savefig(target, bbox_inches='tight')

    plt.close()

def from_workflow():
    workflow_id = os.getenv('INPUT_WORKFLOW_ID')
    repo_name = os.getenv('GITHUB_REPOSITORY')
    github_token = os.getenv('GITHUB_TOKEN')
    target = '/github/workspace/steps.png'
    zip_bytes = download_workflow_logs(repo_name, workflow_id, github_token)
    logs = parse_log(zip_bytes)
    build_image(logs, target)


if __name__ == "__main__":
    from_workflow()
