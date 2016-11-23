# Necessary libraries
import requests
import json
import credentials
from neo4j.v1 import GraphDatabase, basic_auth

NEO4J_URL = credentials.NEO4J_URL # NEO4J server URL (usually bolt://xxx.xxx.xxx.xxx:7687)
NEO4J_USER = credentials.NEO4J_USER
NEO4J_PASS = credentials.NEO4J_PASS
GITHUB_TOKEN = credentials.GITHUB_TOKEN # Token for GitHub API Access

BUILD_FILES = dict({
    'build.xml' : 'Ant',
    'pom.xml' : 'Maven',
    'build.gradle' : 'Gradle',
})

def getRepositories(user):
    url = 'https://api.github.com/users/' + user + '/repos'

    # Build and send the request
    r = requests.get(url,params={'access_token':GITHUB_TOKEN})
    # Parse received JSON
    parsed_json = json.loads(r.text)

    # Put in database
    driver = GraphDatabase.driver(NEO4J_URL, auth=basic_auth(NEO4J_USER, NEO4J_PASS))
    session = driver.session()

    # Add all repositories for current User, if no exist
    for repo in parsed_json:
        if repo['language']:
            print(str(repo['id']) + ' ' + str(repo['name']) + ' ' + str(repo['owner']['login']) + ' ' + str(repo['language']))
            session.run("MERGE (a:Repository {id:'" + str(repo['id']) + "', owner:'" + repo['owner']['login'] + "', name:'" + repo['name'] + "', language:'" + repo['language'] + "'})")
            getCommits(user, repo['name'])
            getBuildFile(user, repo['name'])

    session.close()

def getCommits(user, repo):
    url = 'https://api.github.com/repos/' + user + '/' + repo + '/commits'

    # Build and send the request
    r = requests.get(url, params={'access_token': GITHUB_TOKEN})
    # Parse received JSON
    parsed_json = json.loads(r.text)

    # Put in database
    driver = GraphDatabase.driver(NEO4J_URL, auth=basic_auth(NEO4J_USER, NEO4J_PASS))
    session = driver.session()

    # Add all commits to database, if author is identified. Limit to 5 commits
    counter = 0
    for commit in parsed_json:
        if counter >= 5:
            break
        if commit['author']:
            getSingleCommit(user, repo, commit['sha'])
            counter +=1


def getSingleCommit(user, repo, sha):
    url = 'https://api.github.com/repos/' + user + '/' + repo + '/commits/'+sha

    # Build and send the request
    r = requests.get(url, params={'access_token': GITHUB_TOKEN})
    # Parse received JSON
    scommit = json.loads(r.text)

    # Put in database
    driver = GraphDatabase.driver(NEO4J_URL, auth=basic_auth(NEO4J_USER, NEO4J_PASS))
    session = driver.session()

    if 'stats' in scommit.keys():
        # Add commit stats if no exist
        print(user+' '+repo+' '+scommit['author']['login']+' '+str(scommit['stats']['additions'])+' additions, '+str(scommit['stats']['deletions'])+' deletions.')
        session.run(
            "MATCH (repo:Repository {name: '"+repo+"'}) MERGE (a:Commit {added:" + str(scommit['stats']['additions']) + ", owner:'" + scommit['author']['login'] + "', sha:'" + sha + "', removed:" + str(scommit['stats']['deletions']) + "}) MERGE (repo)-[:CONTAINS]->(a)")

    session.close()


def getBuildFile(user, repo):
    url = 'https://api.github.com/repos/' + user + '/' + repo + '/contents'

    # Build and send the request
    r = requests.get(url, params={'access_token': GITHUB_TOKEN})
    # Parse received JSON
    scommit = json.loads(r.text)

    # Put in database
    driver = GraphDatabase.driver(NEO4J_URL, auth=basic_auth(NEO4J_USER, NEO4J_PASS))
    session = driver.session()

    fileList = []
    fileFound = False
    for file in scommit:
        if (file['type'] == 'file'):
            fileList.append(file['name'])
            if file['name'] in BUILD_FILES.keys():
                fileFound = True
                session.run(
                    "MATCH (repo:Repository {name: '" + repo + "'}) MERGE (a:BuildFile {name:'" + str(
                        file['name']) + "', technology:'" + BUILD_FILES[file['name']] +
                    "'}) MERGE (repo)-[:CONTAINS]->(a)")

    if not fileFound:
        print(fileList)

    session.close()







