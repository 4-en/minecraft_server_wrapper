import requests
import json
import difflib

VERSIONS_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

def get_last_version(snapshot=False):
    response = requests.get(VERSIONS_URL)
    versions = json.loads(response.text)
    
    if snapshot:
        return versions["latest"]["snapshot"]
    else:
        return versions["latest"]["release"]
    
def find_version(version, snapshot=False):

    if version.lower() == "latest":
        return get_last_version(snapshot)

    response = requests.get(VERSIONS_URL)
    versions = json.loads(response.text)

    
    version_list = versions["versions"]
    for v in version_list:
        if v["id"] == version:
            return True
    
    # not version found so far, try to find similar version
    matches = difflib.get_close_matches(version, [v["id"] for v in version_list])
    if len(matches) > 0:
        return matches[0]
    else:
        return None
    
def download_server_jar(version, directory) -> bool:
    response = requests.get(VERSIONS_URL)
    versions = json.loads(response.text)

    # find version with id==version
    version_list = versions["versions"]
    url = None
    for v in version_list:
        if v["id"] == version:
            url = v["url"]
            break

    if url is None:
        return False
    
    response = requests.get(url)
    version_info = json.loads(response.text)
    download_url = version_info["downloads"]["server"]["url"]

    # download the jar to directory
    try:
        f = open(f"{directory}/server.jar", "wb")
        response = requests.get(download_url, stream=True)
        for chunk in response.iter_content(chunk_size=128):
            f.write(chunk)
        f.close()
    except Exception as e:
        print(e)
        return False

    return True
    
