import requests, json

def search_top_docker_images(count: int = 20) -> str:
    """Return JSON string of top Docker images by pull count using search endpoint.
    """
    url = 'https://hub.docker.com/v2/search/repositories/'
    params = {
        'page_size': count,
        'ordering': '-pull_count',
        'query': ''
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for repo in data.get('results', []):
        results.append({
            'name': repo.get('namespace') + '/' + repo.get('name'),
            'pull_count': repo.get('pull_count')
        })
    return json.dumps(results, indent=2)
