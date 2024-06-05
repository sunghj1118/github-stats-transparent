import aiohttp
import logging

class Stats:
    def __init__(self, user, access_token, session, exclude_repos=None, exclude_langs=None, consider_forked_repos=False):
        self.user = user
        self.access_token = access_token
        self.session = session
        self.exclude_repos = exclude_repos
        self.exclude_langs = exclude_langs
        self.consider_forked_repos = consider_forked_repos
        self.repos = []
        self.headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

    async def get_stats(self):
        logging.info("Fetching stats for user: %s", self.user)
        query = """
        {
            user(login: "%s") {
                repositories(first: 100, isFork: %s, ownerAffiliations: OWNER) {
                    nodes {
                        nameWithOwner
                        stargazerCount
                        forkCount
                        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
                            edges {
                                size
                                node {
                                    name
                                    color
                                }
                            }
                        }
                    }
                }
            }
        }
        """ % (self.user, "false" if not self.consider_forked_repos else "true")

        async with self.session.post('https://api.github.com/graphql', json={'query': query}, headers=self.headers) as response:
            if response.status != 200:
                logging.error("GraphQL query failed with status %s: %s", response.status, await response.text())
                raise Exception(f"GitHub API returned status {response.status}")

            data = await response.json()
            logging.info("GitHub API response: %s", data)

            user_data = data.get("data", {}).get("user")
            if not user_data:
                logging.error("No user data found in GitHub API response")
                raise Exception("No user data found")

            self.repos = user_data.get("repositories", {}).get("nodes", [])
            for repo in self.repos:
                if not repo:
                    logging.warning("Encountered None repo in the response")
                name = repo.get("nameWithOwner")
                stargazers = repo.get("stargazerCount")
                forks = repo.get("forkCount")
                languages = repo.get("languages", {}).get("edges", [])

                logging.info("Repository: %s, Stars: %d, Forks: %d, Languages: %s", name, stargazers, forks, languages)

    @property
    async def languages(self):
        languages = {}
        for repo in self.repos:
            for edge in repo.get("languages", {}).get("edges", []):
                language = edge.get("node", {}).get("name")
                if language not in languages:
                    languages[language] = {"size": 0, "color": edge.get("node", {}).get("color", "#000000")}
                languages[language]["size"] += edge.get("size", 0)
        return languages

    @property
    async def stargazers(self):
        return sum(repo.get("stargazerCount", 0) for repo in self.repos)

    @property
    async def forks(self):
        return sum(repo.get("forkCount", 0) for repo in self.repos)

    @property
    async def total_contributions(self):
        # Example implementation, replace with actual logic
        return 0

    @property
    async def lines_changed(self):
        # Example implementation, replace with actual logic
        return (0, 0)

    @property
    async def views(self):
        # Example implementation, replace with actual logic
        return 0

    @property
    async def all_repos(self):
        return self.repos

    @property
    async def name(self):
        return self.user

# Add this at the top of your script to enable logging
logging.basicConfig(level=logging.INFO)
