import requests, json

def fetch_top_docker_images2(count: int = 20) -> str:
    """Fetch top Docker images by pull count using the 'library' namespace endpoint.
    """
    url = 'https://hub.docker.com/v2/repositories/library/'
    params = {'page_size': count, 'ordering': '-pull_count'}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for repo in data.get('results', []):
        results.append({
            'name': f"library/{repo.get('name')}",
            'pull_count': repo.get('pull_count')
        })
    return json.dumps(results, indent=2)
