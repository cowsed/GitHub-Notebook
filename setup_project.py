from gql.transport.aiohttp import AIOHTTPTransport
from gql import gql, Client
import os
from typing import Tuple
from datatypes import Configuration
from api import get_project_id

from constants import API_URL, CONFIG_FILE_PATH


def is_config_setup():
    return os.path.exists(CONFIG_FILE_PATH)


def make_client(api_token: str) -> Client:
    api_headers = {'Authorization': 'token '+api_token}

    # Select your transport with a defined url endpoint
    transport = AIOHTTPTransport(url=API_URL, headers=api_headers)

    # Create a GraphQL client using the defined transport
    client = Client(transport=transport, fetch_schema_from_transport=False)
    return client


def setup_config() -> Tuple[Configuration, Client]:
    conf = Configuration()
    conf.api_token = input("Enter your GitHub API Token: ")
    client = make_client(conf.api_token)

    conf.organization = input("Enter your GitHub Organization Name: ")
    conf.project_number = int(input(
        f"Enter the project number. (Check https://github.com/orgs/{conf.organization}/projects): "))
    conf.project_id = get_project_id(
        client, conf.organization, conf.project_number)
    item = input("General Repository Name: ")
    conf.repo_name_blocklist = [item]
    return conf, client


def get_config_and_gql_client():
    if is_config_setup() == False:
        configuration, client = setup_config()
        configuration.write_config(CONFIG_FILE_PATH)
    else:
        configuration = Configuration.load_config(CONFIG_FILE_PATH)
        client = make_client(configuration.api_token)
    return configuration, client
