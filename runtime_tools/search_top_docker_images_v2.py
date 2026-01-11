import requests, json

def search_top_docker_images_v2(count: int = 20, page: int = 1) -> str:
    """Search Docker Hub for top images by pull count.
    Returns JSON string of image name and pull_count.
    """
    url = 'https://hub.docker.com/v2/search/repositories/'
    params = {
        'page_size': count,
        'page': page,
        'ordering': '-pull_count',
        'query': ''
    }
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
