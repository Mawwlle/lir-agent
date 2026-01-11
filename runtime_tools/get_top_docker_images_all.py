import requests, json

def get_top_docker_images_all(count: int = 20, page: int = 1) -> str:
    """Fetch top Docker images across all namespaces by pull count.
    Uses Docker Hub API v2 repositories endpoint.
    Returns JSON string list of image full name and pull_count.
    """
    url = 'https://hub.docker.com/v2/repositories/'
    params = {
        'page': page,
        'page_size': count,
        'ordering': '-pull_count'
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for repo in data.get('results', []):
        namespace = repo.get('namespace')
        name = repo.get('name')
        full_name = f"{namespace}/{name}" if namespace else name
        results.append({
            'name': full_name,
            'pull_count': repo.get('pull_count')
        })
    return json.dumps(results, indent=2)
