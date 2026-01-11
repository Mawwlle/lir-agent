import requests, json

def fetch_top_docker_images(count: int = 20) -> str:
    """Return a JSON string of top Docker images by pull count.
    Args:
        count: Number of top images to retrieve.
    Returns:
        JSON-formatted string list of image name and pull_count.
    """
    url = 'https://hub.docker.com/v2/repositories/'
    params = {'page_size': count, 'ordering': '-pull_count'}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for repo in data.get('results', []):
        results.append({
            'name': f"{repo.get('namespace')}/{repo.get('name')}",
            'pull_count': repo.get('pull_count')
        })
    return json.dumps(results, indent=2)
