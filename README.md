# OpenPulse

**A lightweight, open-source GitHub repository health dashboard.**

OpenPulse turns public GitHub activity into a clear snapshot of project health: maintenance activity, issue and pull-request flow, contributor participation, and recent development.

> Early-stage project. Metrics are descriptive signals, not a definitive score of software quality or maintainer performance.

## Features
- Inspect any public GitHub repository by owner/repo
- View stars, forks, open issues, open pull requests, and recent commits
- Review recent commit activity and contributor participation
- Explore issue and pull-request age and labels
- Export the collected snapshot as JSON
- Optional GitHub token support for higher API rate limits
- Unit tests for the analysis layer

## Quick start
Requires Python 3.10 or newer.

    git clone https://github.com/anshbyte1/OpenPulse.git
    cd OpenPulse
    python -m venv .venv
    # Windows: .venv\Scripts\activate
    # macOS/Linux: source .venv/bin/activate
    pip install -r requirements.txt
    streamlit run app.py

Open the local URL printed by Streamlit, enter a repository such as pallets/flask, and select Analyze repository.

## Optional GitHub token
Unauthenticated GitHub API requests have a low rate limit. Set a personal access token with public read access as GITHUB_TOKEN.

Windows PowerShell:
    $env:GITHUB_TOKEN="your_token"
    streamlit run app.py

macOS/Linux:
    export GITHUB_TOKEN="your_token"
    streamlit run app.py

OpenPulse never asks for or stores your token in the app. It is sent only to api.github.com in the Authorization header.

## How metrics work
OpenPulse fetches repository metadata, recent commits, open issues, and pull requests from the GitHub REST API. It reports observable counts and time-based summaries. It does not infer code correctness, security, bus factor, or maintainer intent.

- Recent commits: commits returned by the configured recent-commit window.
- Issue/PR age: age in days based on creation timestamp for currently open items.
- Contributor count: distinct authors in the fetched recent commit sample.
- Activity: recent commit counts grouped by calendar date.

Results are limited by GitHub API pagination and rate limits. A small recent sample is not a complete history.

## Development
    pip install -r requirements-dev.txt
    pytest

## Roadmap
- [ ] Historical snapshots and trend comparisons
- [ ] Configurable date windows
- [ ] More detailed release and workflow signals
- [ ] Caching and API efficiency improvements

Contributions, bug reports, and feature requests are welcome. See CONTRIBUTING.md and CODE_OF_CONDUCT.md.

## License
MIT. See LICENSE.
