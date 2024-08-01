from dotenv import dotenv_values


def get_mongodb_uri():
    config = dotenv_values(".env")
    mongodb_uri = config.get("MONGODB_URI")

    # print(mongodb_uri)

    return mongodb_uri


def get_port():
    config = dotenv_values(".env")
    port = config.get("PORT")

    # print(port)

    return int(port) if port else 8080
