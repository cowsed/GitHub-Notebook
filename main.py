from typing import List, Tuple, Dict
import re
import os
import os.path
from tqdm import tqdm

from datetime import datetime
from colorama import Fore

from gql import gql, Client


from datatypes import EntryInfo, AssetID, Entry, Project, Configuration
from cookies import get_authorized_resource, extract_cookies

from api import get_notebook_cards
from setup_project import get_config_and_gql_client
from constants import ENTRY_TAG


# extract all private github asset links and replace them with local file references. Return the identifiers of those assets so they can be reconstructed later and downloaded
def find_and_replace_asset_urls(text) -> Tuple[str, List[AssetID]]:
    asset_pattern = r'https:\/\/github.com\/([^\/]*)\/([^\/]*)\/assets\/([^\/]*)\/([^\/\)]*)'
    replacement = r'assets/\1/\2/\3/\4'
    url_parts = re.findall(asset_pattern, text)
    attachemts: List[AssetID] = [AssetID(
        parts[0], parts[1], parts[2], parts[3]) for parts in url_parts]

    newtext = re.sub(asset_pattern, replacement, text)
    return newtext, attachemts


def extract_entry_info(header: str) -> EntryInfo:
    entry_info = EntryInfo('uncategorized')

    # split metadata section into pieces
    parts = header.split('|')
    for part in parts:
        part = part.strip()

    # drop '' and `entry` from the start. We don't care about them at this point
    parts = parts[2:]

    # Get Category
    if len(parts) < 1:
        print("invalid header. No category specified")
        return entry_info

    (entry_type, *parts) = parts  # Split list into first and rest

    if entry_type.lower() not in EntryInfo.all:
        entry_type = 'Uncategorized'
    else:
        entry_type = entry_type.lower()
    entry_info.entry_type = entry_type

    # Category specific required metadata
    if entry_type == EntryInfo.PROPOSAL:
        if len(parts) < 1:
            print('invalid header. No proposal name')
            return entry_type
        (proposal_name, *parts) = parts
        entry_info.proposal_title = proposal_name

    # Scan for optional metadata
    for part in parts:
        if part.startswith('date_override'):
            date_str = part.split(' ', 1)[1]
            date = datetime.strptime(date_str, "%m/%d/%y")
            entry_info.date_override = date
    return entry_info


def process_notebook_cards(all_cards: Dict, wanted_label: str) -> Tuple[List[Project], List]:
    notebook_cards: List[Project] = []
    all_assets = []
    for c in all_cards:

        labels = c['content']['labels']['nodes']
        flattened_labels = [l['name'] for l in labels]

        if wanted_label not in flattened_labels:
            # skip processing if we don't want this card
            continue

        card_name = c['content']['title']
        card_reponame = c['content']['repository']['name']

        # only care about entry comments
        entry_comments: List[Entry] = []
        for com in c['content']['comments']['nodes']:
            # if was tagged with the entry tag, strip the tag away (todo process meta commands) and take off first line
            if com['body'].startswith(ENTRY_TAG):
                parts = com['body'].split('\n', 1)
                header, body = parts[0], parts[1]
                entry_type = extract_entry_info(header)

                newbody, assets = find_and_replace_asset_urls(body)
                all_assets += assets

                createdAt = datetime.strptime(
                    com['createdAt'], '%Y-%m-%dT%H:%M:%SZ')

                entry_comments.append(
                    Entry(createdAt, entry_type, newbody))

        notebook_cards.append(
            Project(card_name, card_reponame, flattened_labels, entry_comments))

    return notebook_cards, all_assets


def partition_cards(cards: List) -> Tuple[List, List, List]:
    '''
    Split a list of cards into 3 lists corresponding to the 3 notebooks
    - strategy
    - hardware
    - software
    '''
    sw_tag = 'software-subteam'
    hw_tag = 'hardware-subteam'
    strategy_tag = 'strategy'
    strategy_issues = []
    hardware_issues = []
    software_issues = []
    for c in cards:
        if strategy_tag in c.labels:
            strategy_issues.append(c)
        elif sw_tag in c.labels:
            software_issues.append(c)
        elif hw_tag in c.labels:
            hardware_issues.append(c)
        else:
            print(f"{Fore.RED}Project '{
                  c['content']['title']}' is not categorized into hardware, software, or strategy.{Fore.RESET_ALL}")
    return (strategy_issues, hardware_issues, software_issues)


def make_entry_markdown(entry: Entry):
    dt = entry.createdAt
    if entry.info.date_override is not None:
        dt = entry.info.date_override

    title = f"## {entry.project_name if entry.repo_name is None else (
        entry.repo_name + ": " + entry.project_name)} - {datetime.strftime(dt, "%m/%d/%Y")}"

    entry_type = f'### {entry.info.entry_type.title()}'
    if entry.info.entry_type == EntryInfo.PROPOSAL:
        entry_type += ': '+entry.info.proposal_title

    body = entry.body

    return title + "\n" + entry_type + "\n" + body


def make_notebook(projects: List[Project], repo_name_blocklist: List[str], header: str = '') -> str:
    doc = header + '\n'
    entries = []

    for proj in projects:
        title = proj.name
        repo = proj.repo_name
        if repo in repo_name_blocklist:
            repo = None
        for entry in proj.entries:
            entry.repo_name = repo
            entry.project_name = title
            entries.append(entry)

    entries = sorted(entries, key=lambda e: e.createdAt)
    for entry in entries:
        doc += make_entry_markdown(entry)
        doc += '\n\n'
    return doc


def download_assets(assets: List[AssetID], cookies):
    '''
    For each asset that we extracted from the text, if it is found, skip it or
    if it is not downloaded locally, download it from the server and save to
    the local assets folder

    '''
    print(f"Downloading {len(assets)} assets")

    for asset in tqdm(assets):
        url = f'https://github.com/{asset.orgname
                                    }/{asset.repo}/assets/{asset.id1}/{asset.id2}'
        fname = f'out/assets/{asset.orgname}/{asset.repo}/{asset.id1}/{asset.id2}'
        if os.path.exists(fname):
            # already downloaded
            continue
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        with open(fname, "wb") as f:
            resp = get_authorized_resource(url, cookies)
            f.write(resp.content)


custom_css = '''
<style>
table{
    margin-left: auto;
    margin-right: auto;
}
td, th {
    text-align: center;
}
td,th > img{
    width: 50vw;
}
</style>
'''


if __name__ == '__main__':
    # Get Setup
    configuration: Configuration
    client: Client
    configuration, client = get_config_and_gql_client()

    # Download and process cards
    raw_cards = get_notebook_cards(client, configuration.project_id)
    cards, assets = process_notebook_cards(raw_cards, 'notebook')
    (strategy, hw, sw) = partition_cards(cards)

    # Authenticate and download private github assets (attachements on issues)
    cookies = extract_cookies(1)
    download_assets(assets, cookies)

    # Output notebooks
    outputs = [('out/strategy.md', strategy),
               ('out/hw.md', hw),
               ('out/sw.md', sw)]
    for fname, cards in outputs:
        with open(fname, 'w') as f:
            f.write(make_notebook(cards, ['2024-2025-Planning'], custom_css))
