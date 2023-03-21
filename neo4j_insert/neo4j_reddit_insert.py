from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from dotenv import load_dotenv
import json
import os


def create_post(tx, id, date, title, content, username, commentCount, score, subreddit):
    query = (
        "CREATE (p1:Post { id: $id, date: $date, title: $title, content: $content, username: $username, commentCount: $commentCount, score: $score, subreddit: $subreddit })"
        "RETURN p1"
    )
    result = tx.run(query, id=id, date=date, title=title, content=content, username=username, commentCount=commentCount, score=score, subreddit=subreddit)
    try:
        return [{"p1": row["p1"]["id"]} for row in result]
    except ServiceUnavailable as exception:
        print("{query} raised an error: \n {exception}".format(
            query=query, exception=exception))
        raise
    

def create_comment(tx, id, date, content, username, score, post_id):
    query = (
        "CREATE (c1:Comment { id: $id, date: $date, content: $content, username: $username, score: $score, postId: $postId })"
        "RETURN c1"
    )
    result = tx.run(query, id=id, date=date, content=content, username=username, score=score, postId=post_id)
    try:
        return [{"c1": row["c1"]["id"]} for row in result]
    except ServiceUnavailable as exception:
        print("{query} raised an error: \n {exception}".format(
            query=query, exception=exception))
        raise


def create_orchestrator(uri, user, password, posts, commetns):
    data_base_connection = GraphDatabase.driver(uri=uri, auth=(user, password))
    with data_base_connection.session(database="neo4j") as session:
        # Write transactions allow the driver to handle retries and transient errors
        print(session)
        for post in posts:
            result = session.execute_write(create_post, post["id"], post["date"], post["title"], post["content"], post["username"], post["commentCount"], post["score"], post["subreddit"])
            for row in result:
                print(f"Created: {result}")
        for comment in comments:
            result = session.execute_write(create_comment, comment["id"], comment["date"], comment["content"], comment["username"], comment["score"], comment["post_id"])
            for row in result:
                print(f"Created: {result}")


def delete_all(tx):
    query = (
        "MATCH (n) DETACH DELETE n "
        "RETURN n"
    )
    result = tx.run(query)
    try:
        return [{"n": row["n"]["username"]} for row in result]
    # Capture any errors along with the query and data for traceability
    except ServiceUnavailable as exception:
        print("{query} raised an error: \n {exception}".format(
            query=query, exception=exception))


def delete_database(uri, user, password):
    data_base_connection = GraphDatabase.driver(uri=uri, auth=(user, password))
    with data_base_connection.session(database="neo4j") as session:
        # Write transactions allow the driver to handle retries and transient errors
        result = session.execute_write(delete_all)
        for row in result:
            print(f"Deleted: {row['n']}")


if __name__ == "__main__":
    load_dotenv()
    with open('reddit_posts_dump.json', 'r') as outfile:
        posts = json.load(outfile)
    with open('reddit_comments_dump.json', 'r') as outfile:
        comments = json.load(outfile)
    uri = os.environ.get("NEO4J_URI")
    print(uri)
    user = os.environ.get("NEO4J_USER")
    print(user)
    password = os.environ.get("NEO4J_PASSWORD")
    print(password)
    delete_database(uri, user, password)
    create_orchestrator(uri, user, password, posts, comments)
