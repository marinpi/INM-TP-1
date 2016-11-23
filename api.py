from flask import Flask
app = Flask(__name__)
from neo4j.v1 import GraphDatabase, basic_auth
import json
import credentials
import pprint

NEO4J_URL = credentials.NEO4J_URL # NEO4J server URL (usually bolt://xxx.xxx.xxx.xxx:7687)
NEO4J_USER = credentials.NEO4J_USER
NEO4J_PASS = credentials.NEO4J_PASS

@app.route("/repositories")
def getRepositories():
    # Put in database
    driver = GraphDatabase.driver(NEO4J_URL, auth=basic_auth(NEO4J_USER, NEO4J_PASS))
    session = driver.session()
    result = session.run("MATCH (a:Repository) RETURN a")
    session.close()

    repoList = []
    for nrepo in result:
        nrepo = nrepo['a']
        repoList.append({'id':nrepo['id'], 'name':nrepo['name'], 'owner':nrepo['owner'], 'language':nrepo['language']})

    return json.dumps(repoList)

@app.route("/languages")
def getLanguagesList():
    # Put in database
    driver = GraphDatabase.driver(NEO4J_URL, auth=basic_auth(NEO4J_USER, NEO4J_PASS))
    session = driver.session()
    result = session.run("MATCH (a:Repository) RETURN distinct a.language ORDER BY a.language")
    session.close()

    repoList = []
    for nrepo in result:
        repoList.append(nrepo['a.language'])

    return json.dumps(repoList)

@app.route("/languages/<language>")
def getLanguageStats(language):
    # Put in database
    driver = GraphDatabase.driver(NEO4J_URL, auth=basic_auth(NEO4J_USER, NEO4J_PASS))
    session = driver.session()
    result = session.run("MATCH (a:Repository)-[:CONTAINS]->(b:BuildFile) WHERE a.language='"+language+"' RETURN b.technology AS tool, b.name AS filename, count(a) as usage ORDER BY b.technology")
    session.close()

    languageStats = []
    for tool in result:
        toolSt = dict()
        toolSt['tool'] = tool['tool']
        toolSt['filename'] = tool['filename']
        toolSt['usage'] = tool['usage']
        languageStats.append(toolSt)

    return json.dumps(languageStats)


@app.route("/committers")
def getCommittersList():
    # Put in database
    driver = GraphDatabase.driver(NEO4J_URL, auth=basic_auth(NEO4J_USER, NEO4J_PASS))
    session = driver.session()
    result = session.run("MATCH (a:Commit) RETURN distinct a.owner ORDER BY a.owner")
    session.close()

    repoList = []
    for nrepo in result:
        repoList.append(nrepo['a.owner'])

    return json.dumps(repoList)

@app.route("/committers/<name>")
def getCommitterStats(name):
    # Put in database
    driver = GraphDatabase.driver(NEO4J_URL, auth=basic_auth(NEO4J_USER, NEO4J_PASS))
    session = driver.session()
    result = session.run("MATCH (a:Commit) WHERE a.owner='"+name+"' RETURN a.owner AS owner, sum(a.added) as added, sum(a.removed) as deleted")
    session.close()

    userStats = dict()
    for user in result:
        userStats['owner'] = user['owner']
        userStats['added'] = user['added']
        userStats['deleted'] = user['deleted']
        break #Only first result TODO improve that

    return json.dumps(userStats)


if __name__ == "__main__":
    app.run()