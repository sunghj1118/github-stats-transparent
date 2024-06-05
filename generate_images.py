#!/usr/bin/python3

import asyncio
import os
import re
import aiohttp
import logging

from github_stats import Stats

# Configure logging
logging.basicConfig(level=logging.INFO)

################################################################################
# Helper Functions
################################################################################

def generate_output_folder() -> None:
    """
    Create the output folder if it does not already exist
    """
    if not os.path.isdir("generated"):
        os.mkdir("generated")

################################################################################
# Individual Image Generation Functions
################################################################################

async def generate_overview(s: Stats) -> None:
    """
    Generate an SVG badge with summary statistics
    :param s: Represents user's GitHub statistics
    """
    with open("templates/overview.svg", "r") as f:
        output = f.read()

    # Add logging to verify data insertion
    name = await s.name
    logging.info(f"Name: {name}")
    output = re.sub("{{ name }}", name, output)

    stars = await s.stargazers
    logging.info(f"Stars: {stars}")
    output = re.sub("{{ stars }}", f"{stars:,}", output)

    forks = await s.forks
    logging.info(f"Forks: {forks}")
    output = re.sub("{{ forks }}", f"{forks:,}", output)

    contributions = await s.total_contributions
    logging.info(f"All-time contributions: {contributions}")
    output = re.sub("{{ contributions }}", f"{contributions:,}", output)

    lines_changed = await s.lines_changed
    changed = lines_changed[0] + lines_changed[1]
    logging.info(f"Lines of code changed: {changed}")
    output = re.sub("{{ lines_changed }}", f"{changed:,}", output)

    views = await s.views
    logging.info(f"Repository views (past two weeks): {views}")
    output = re.sub("{{ views }}", f"{views:,}", output)

    repos = await s.all_repos
    logging.info(f"Repositories with contributions: {len(repos)}")
    output = re.sub("{{ repos }}", f"{len(repos):,}", output)

    generate_output_folder()
    with open("generated/overview.svg", "w") as f:
        f.write(output)

async def generate_languages(s: Stats) -> None:
    """
    Generate an SVG badge with summary languages used
    :param s: Represents user's GitHub statistics
    """
    with open("templates/languages.svg", "r") as f:
        output = f.read()

    progress = ""
    lang_list = ""
    sorted_languages = sorted((await s.languages).items(), reverse=True, key=lambda t: t[1].get("size"))
    delay_between = 150
    for i, (lang, data) in enumerate(sorted_languages):
        color = data.get("color")
        color = color if color is not None else "#000000"
        ratio = [.98, .02]
        if data.get("prop", 0) > 50:
            ratio = [.99, .01]
        if i == len(sorted_languages) - 1:
            ratio = [1, 0]
        progress += (f'<span style="background-color: {color};'
                     f'width: {(ratio[0] * data.get("prop", 0)):0.3f}%;'
                     f'margin-right: {(ratio[1] * data.get("prop", 0)):0.3f}%;" '
                     f'class="progress-item"></span>')
        lang_list += f"""
<li style="animation-delay: {i * delay_between}ms;">
<svg xmlns="http://www.w3.org/2000/svg" class="octicon" style="fill:{color};"
viewBox="0 0 16 16" version="1.1" width="16" height="16"><path
fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8z"></path></svg>
<span class="lang">{lang}</span>
<span class="percent">{data.get("prop", 0):0.2f}%</span>
</li>
"""

    output = re.sub(r"{{ progress }}", progress, output)
    output = re.sub(r"{{ lang_list }}", lang_list, output)

    generate_output_folder()
    with open("generated/languages.svg", "w") as f:
        f.write(output)

################################################################################
# Main Function
################################################################################

async def main() -> None:
    """
    Generate all badges
    """
    access_token = os.getenv("ACCESS_TOKEN")
    if not access_token:
        raise Exception("A personal access token is required to proceed!")
    user = os.getenv("GITHUB_ACTOR")
    exclude_repos = os.getenv("EXCLUDED")
    exclude_repos = ({x.strip() for x in exclude_repos.split(",")} if exclude_repos else None)
    exclude_langs = os.getenv("EXCLUDED_LANGS")
    exclude_langs = ({x.strip() for x in exclude_langs.split(",")} if exclude_langs else None)
    consider_forked_repos = len(os.getenv("COUNT_STATS_FROM_FORKS")) != 0

    async with aiohttp.ClientSession() as session:
        s = Stats(user, access_token, session, exclude_repos=exclude_repos, exclude_langs=exclude_langs, consider_forked_repos=consider_forked_repos)
        await asyncio.gather(generate_languages(s), generate_overview(s))

if __name__ == "__main__":
    asyncio.run(main())
