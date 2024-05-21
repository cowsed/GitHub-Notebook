from typing import Dict, List
from datetime import datetime
import jsonpickle


class EntryInfo:
    MOTIVATION: str = 'motivation'
    PROPOSAL: str = 'proposal'
    EVALUATION: str = 'evaluation'
    UPDATE: str = 'update'
    TEST: str = 'test'
    all: List[str] = [MOTIVATION, PROPOSAL, EVALUATION, UPDATE, TEST]

    entry_type: str
    date_override: datetime | None
    proposal_title: str | None

    def __init__(self, val):
        self.entry_type = val
        self.date_override = None
        self.proposal_title = None


class Entry:
    info: EntryInfo
    createdAt: datetime
    body: str
    repo_name: str | None
    project_name: str

    def __init__(self, createdAt, entry_type, body):
        self.createdAt = createdAt
        self.info = entry_type
        self.body = body


class Project:
    name: str
    repo_name: str
    labels: List[str]
    entries: List[Entry]

    def __init__(self, name: str, repo_name: str, labels: List[str], entries: List[str]):
        self.name = name
        self.repo_name = repo_name
        self.labels = labels
        self.entries = entries


class AssetID:
    orgname: str
    repo: str
    id1: str
    id2: str

    def __init__(self, orgname, repo, id1, id2):
        self.orgname = orgname
        self.repo = repo
        self.id1 = id1
        self.id2 = id2


class Configuration:
    api_token: str
    organization: str
    project_number: int
    project_id: str

    repo_name_blocklist: List[str]

    def write_config(self, fname: str):
        json_string = jsonpickle.encode(self)
        with open(fname, 'w') as f:
            f.write(json_string)

    @staticmethod
    def load_config(fname: str):
        json_string = ''
        with open(fname, 'r') as f:
            json_string = f.read()
        recreated_obj = jsonpickle.decode(json_string)
        return recreated_obj
