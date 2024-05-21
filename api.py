'''
api.py

a handful of helper functions to get data from the Github GraphQL API
'''
from gql import gql, Client
from typing import Dict


def get_project_id(client: Client, org: str, number: int) -> str:
    '''
    Given an organization and project number (visibile in the github ui), get
    the internal ID that allows us to access the project with the GraphQL API

    '''
    query = gql(
        """
     query{
        organization(login: "%s"){
          projectV2(number: %s) {
            id
          }
        }
      }
    """ % (org, number)
    )
    result = client.execute(query)
    return result['organization']['projectV2']['id']


def get_projects(client: Client, org: str):
    '''
    Given an organizatoin, show all the projects, their API ID, and number
    '''
    query = gql('''
    query ($org_name: String!){
    	organization(login: $org_name){
    		projectsV2(first: 100) {
          nodes {
            id,
            title,
            number
          }
    		}
    	}
    }''')
    return client.execute(query, {"org_name": org})


def get_notebook_cards(client: Client, projid: str):
    issue_threads_query = gql('''
    query ($projID: ID!){
      node(id: $projID) {
        ... on ProjectV2{
          projectCards:items (first:100){
            nodes{
              content {
                ... on Issue {
                  title,
                  body,
                  repository {
                    name
                  },
                  labels(first: 100) {
                    nodes {
                      name
                    }
                  }
                  comments (first:100){
                    nodes {
                    createdAt,
                      body,
                      editor {
    				  ... on User{
                          name,
                          url,
                        }
                      }
                    }
                  }
                }
                ... on PullRequest{
                  title,
                  body,
                  repository {
                    name
                  },
                  comments (first:100){
                    nodes {
                      createdAt,
                      body,
                      editor {
    					  ... on User{
                          name,
                          url,
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    ''')
    r = client.execute(issue_threads_query, {"projID": projid})
    return r['node']['projectCards']['nodes']
