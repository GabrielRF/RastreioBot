from rastreio import db

import configparser
import requests

config = configparser.ConfigParser()
config.read("bot.conf")

api_key = config["LOGGI"]["api_key"]
email = config["LOGGI"]["email"]
final_codes = {int(x) for x in config["LOGGI"]["final_codes"].split(", ")}


def process_response(response, tracking_code):
    statuses = response.get("statuses", [])
    status_codes = {s.get("statusCode") for s in statuses}
    if status_codes & final_codes:
        db.update_package(tracking_code, finished=True)


def get(code, retries=0):
    payload = {
        "query": f"""{{
            packageHistory(trackingKey: "{code}") {{
                statuses {{
                    status
                    statusDisplay
                    detailedStatusDisplay
                    statusCode
                    updated
                }}
            }}
        }}"""
    }
    headers = {"Authorization": f"{email}:{api_key}"}
    url = "https://api.loggi.com/graphql"
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        if retries:
            return get(code, retries=retries - 1)
        else:
            return None
    return process_response(response.json(), code)


if __name__ == "__main__":
    print(get(sys.argv[1], 0))
