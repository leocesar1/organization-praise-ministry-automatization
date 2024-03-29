from pymongo import MongoClient
from default.default import get_Credentials, Metaclass

mongo = get_Credentials("mongo")["mongo"]

# print(mongoPassword)


def get_database():
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = f"mongodb+srv://{mongo['user']}:{mongo['password']}@cluster-lm-31.1eebaz1.mongodb.net/?retryWrites=true&w=majority"

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)

    # Create the database for our example (we will use the same database throughout the tutorial
    return client["worship-ministry-organization"]


# This is added so that many files can reuse the function get_database()
if __name__ == "__main__":
    # Get the database
    dbname = get_database()
