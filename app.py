"""OpenPulse Streamlit application."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from openpulse.analyzer import analyze_repository
from openpulse.github_api import GitHubAPIError, GitHubClient

st.set_page_config(page_title="OpenPulse", page_icon="📡", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 2.2rem; max-width: 1200px;}
.hero {padding: 1.4rem 1.6rem; border: 1px solid rgba(128,128,128,.25);
       border-radius: 16px; margin-bottom: 1.2rem;}
.muted {opacity: .7; font-size: .92rem;}
</style>
""", unsafe_allow_html=True)

st.title("📡 OpenPulse")
st.caption("A clear snapshot of public GitHub project activity and maintenance signals.")
st.markdown(
    '<div class="hero"><strong>Understand a repository at a glance.</strong>'
    '<div class="muted">Explore development activity, issue flow, pull requests, and contributors. '
    'Signals are descriptive—not a quality or security verdict.</div></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Repository")
    repo_input = st.text_input("GitHub repository", value="pallets/flask", placeholder="owner/repo")
    commit_limit = st.slider("Recent commits to inspect", 10, 100, 30, step=10)
    st.caption("Public repositories are supported.")
    st.divider()
    st.caption("Optional token: set the GITHUB_TOKEN environment variable to raise API limits.")

if st.button("Analyze repository", type="primary"):
    st.session_state.pop("snapshot", None)
    try:
        with st.spinner("Fetching repository activity from GitHub…"):
            client = GitHubClient(token=os.getenv("GITHUB_TOKEN"))
            st.session_state.snapshot = analyze_repository(
                client, repo_input.strip(), commit_limit=commit_limit
            )
    except (GitHubAPIError, ValueError) as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Could not analyze this repository: {exc}")

snapshot = st.session_state.get("snapshot")
if snapshot:
    repo = snapshot["repository"]
    st.subheader(repo["full_name"])
    st.caption(repo.get("description") or "No repository description provided.")
    st.markdown(f"[Open on GitHub]({repo['html_url']})")

    metrics = snapshot["metrics"]
    cols = st.columns(5)
    values = [repo["stargazers_count"], repo["forks_count"], metrics["open_issues"],
              metrics["open_pull_requests"], metrics["recent_commit_count"]]
    for col, label, value in zip(cols, ["Stars", "Forks", "Open issues", "Open PRs", "Recent commits"], values):
        col.metric(label, f"{value:,}")

    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("Commit activity")
        activity = pd.DataFrame(snapshot["commit_activity"])
        if not activity.empty and activity["commits"].sum() > 0:
            st.bar_chart(activity.set_index("date")["commits"], height=260)
        else:
            st.info("No commit activity was returned for this sample.")
    with right:
        st.subheader("Maintenance signals")
        st.metric("Contributors in sample", metrics["contributor_count"])
        st.metric("Median open issue age",
                  f'{metrics["median_open_issue_age_days"]} days'
                  if metrics["median_open_issue_age_days"] is not None else "—")
        st.metric("Median open PR age",
                  f'{metrics["median_open_pr_age_days"]} days'
                  if metrics["median_open_pr_age_days"] is not None else "—")
        st.caption("Contributor count is based only on authors in the fetched commit sample.")

    st.subheader("Recent commits")
    commits = pd.DataFrame(snapshot["recent_commits"])
    if not commits.empty:
        st.dataframe(commits[["date", "author", "message", "sha"]],
                     use_container_width=True, hide_index=True)
    else:
        st.info("No commits found in the requested sample.")

    issue_tab, pr_tab = st.tabs(["Open issues", "Open pull requests"])
    with issue_tab:
        issues = pd.DataFrame(snapshot["open_issues"])
        if not issues.empty:
            st.dataframe(issues[["number", "title", "age_days", "labels", "url"]],
                         use_container_width=True, hide_index=True)
        else:
            st.success("No open issues returned.")
    with pr_tab:
        prs = pd.DataFrame(snapshot["open_pull_requests"])
        if not prs.empty:
            st.dataframe(prs[["number", "title", "age_days", "author", "url"]],
                         use_container_width=True, hide_index=True)
        else:
            st.info("No open pull requests returned.")

    st.download_button("Download report (JSON)", json.dumps(snapshot, indent=2, ensure_ascii=False),
                       file_name=f"{repo['name']}-openpulse-report.json", mime="application/json")
    st.caption("Data retrieved from GitHub at " +
               datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") +
               ". API results may be incomplete due to rate limits or pagination.")
else:
    st.info("Enter a public repository and click Analyze repository to get started.")
    st.markdown("Try: pallets/flask, psf/requests, or streamlit/streamlit.")
