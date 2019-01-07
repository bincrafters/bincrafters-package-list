import requests
import json
import csv
import logging
import os
from conans.client import conan_api

logging.basicConfig(level=logging.INFO, format="%(message)s")


API_URL = "https://api.github.com"
ORG = "bincrafters"
MAX_PAGES = 10
TOKEN = os.getenv("GITHUB_TOKEN")
CONAN_INSTANCE, _, _ = conan_api.Conan.factory()
CONAN_REMOTE = "bincrafters"


def get_projects():
    repos = []
    headers = {"Authorization": "token {}".format(TOKEN)}
    url = "{}/orgs/{}/repos".format(API_URL, ORG)
    args = {"per_page": "100"}
    for page in range(1,MAX_PAGES):
        args["page"] = page
        response = requests.get(url=url, params=args, headers=headers)
        json_data = response.json()
        if not json_data:
            break
        for repo in json_data:
            if "conan-" in repo["name"]:
                repos.append(repo["name"])
    return repos


def has_recipe(repo):
    headers = {"Authorization": "token {}".format(TOKEN)}
    url = "{}/repos/{}/{}/contents/conanfile.py".format(API_URL, ORG, repo)
    response = requests.get(url, headers=headers)
    return response.ok


def search_recipe(repo, remote):
    pattern = "{}/*@{}/stable".format(repo[repo.find('-')+1:], ORG)
    result = CONAN_INSTANCE.search_recipes(pattern, remote)
    return False if result.get('error') or not result.get('results') else True


def is_published(repo):
    return search_recipe(repo, CONAN_REMOTE)


def is_official(repo):
    return search_recipe(repo, "conan-center")


if __name__ == "__main__":
    repos = get_projects()
    with open('bincrafters-packages.csv', mode='w') as csv_fd:
        csv_writer = csv.writer(csv_fd, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(["github", "has-recipe", "is-published", "in-conan-center"])
        for repo in repos:
            recipe = has_recipe(repo)
            published = is_published(repo)
            official = is_official(repo)
            logging.info("{}: {}, {}, {}".format(repo, recipe, published, official))
            csv_writer.writerow([repo, recipe, published, official])
