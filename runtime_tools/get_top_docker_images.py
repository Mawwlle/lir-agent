from langchain.tools import tool
import requests

@tool
def get_top_docker_images(*, count: int = 20) -> str:
    """Fetch the top Docker images by pull count from Docker Hub.
    Returns a JSON-formatted string list of images with name and pull_count.
    """
    url = 'https://hub.docker.com/v2/repositories/'
    params = {
        'page_size': count,
        'ordering': '-pull_count'
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    results = []
    for repo in data.get('results', []):
        results.append({
            'name': repo.get('namespace') + '/' + repo.get('name'),
            'pull_count': repo.get('pull_count')
        })
    import json
    return json.dumps(results, indent=2)
