async def get_stats(self) -> None:
    """
    Get lots of summary statistics using one big query. Sets many attributes
    """
    self._stargazers = 0
    self._forks = 0
    self._languages = dict()
    self._repos = set()
    self._ignored_repos = set()
    
    next_owned = None
    next_contrib = None
    while True:
        raw_results = await self.queries.query(
            Queries.repos_overview(owned_cursor=next_owned,
                                   contrib_cursor=next_contrib)
        )
        raw_results = raw_results if raw_results is not None else {}

        self._name = (raw_results
                      .get("data", {})
                      .get("viewer", {})
                      .get("name", None))
        if self._name is None:
            self._name = (raw_results
                          .get("data", {})
                          .get("viewer", {})
                          .get("login", "No Name"))

        contrib_repos = (raw_results
                         .get("data", {})
                         .get("viewer", {})
                         .get("repositoriesContributedTo", {}))
        owned_repos = (raw_results
                       .get("data", {})
                       .get("viewer", {})
                       .get("repositories", {}))
        
        repos = owned_repos.get("nodes", [])
        if self._consider_forked_repos:
            repos += contrib_repos.get("nodes", [])
        else:
            for repo in contrib_repos.get("nodes", []):
                name = repo.get("nameWithOwner")
                if name in self._ignored_repos or name in self._exclude_repos:
                    continue
                self._ignored_repos.add(name)

        for repo in repos:
            name = repo.get("nameWithOwner")
            if name in self._repos or name in self._exclude_repos:
                continue
            self._repos.add(name)
            self._stargazers += repo.get("stargazers").get("totalCount", 0)
            self._forks += repo.get("forkCount", 0)

            for lang in repo.get("languages", {}).get("edges", []):
                lang_name = lang.get("node", {}).get("name", "Other")
                if lang_name == "Jupyter Notebook" or lang_name in self._exclude_langs:
                    continue
                languages = await self.languages
                if lang_name in languages:
                    languages[lang_name]["size"] += lang.get("size", 0)
                    languages[lang_name]["occurrences"] += 1
                else:
                    languages[lang_name] = {
                        "size": lang.get("size", 0),
                        "occurrences": 1,
                        "color": lang.get("node", {}).get("color")
                    }
                print(f"Added language {lang_name} with size {lang.get('size', 0)}")

        if owned_repos.get("pageInfo", {}).get("hasNextPage", False) or \
                contrib_repos.get("pageInfo", {}).get("hasNextPage", False):
            next_owned = (owned_repos
                          .get("pageInfo", {})
                          .get("endCursor", next_owned))
            next_contrib = (contrib_repos
                            .get("pageInfo", {})
                            .get("endCursor", next_contrib))
        else:
            break

    langs_total = sum([v.get("size", 0) for v in self._languages.values()])
    for k, v in self._languages.items():
        v["prop"] = 100 * (v.get("size", 0) / langs_total)
    print(f"Final language stats: {self._languages}")
