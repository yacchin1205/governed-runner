import json

from urllib.parse import urlparse, quote_plus

from aiodocker import Docker


def get_optional_value(object, key):
    labels = object['Labels']
    abskey = f'governedrunner.opt.provider.{key}'
    if abskey not in labels:
        return None
    return labels[abskey]

def get_spawn_ref(object):
    labels = object['Labels']
    repo = labels["repo2docker.repo"]
    ref = labels["repo2docker.ref"]
    return quote_plus(f'{repo}#{ref}')

async def list_images():
    """
    Retrieve local images built by repo2docker
    """
    async with Docker() as docker:
        r2d_images = await docker.images.list(
            filters=json.dumps({"dangling": ["false"], "label": ["repo2docker.ref"]})
        )
    images = [
        {
            "repo": get_optional_value(image, 'repo') or image["Labels"]["repo2docker.repo"],
            "ref": image["Labels"]["repo2docker.ref"],
            "spawnref": get_spawn_ref(image),
            "image_name": image["Labels"]["governedrunner.image_name"],
            "display_name": get_optional_value(image, 'display_name') or image["Labels"]["governedrunner.display_name"],
            "mem_limit": image["Labels"]["governedrunner.mem_limit"],
            "cpu_limit": image["Labels"]["governedrunner.cpu_limit"],
            "status": "built",
        }
        for image in r2d_images
        if "governedrunner.image_name" in image["Labels"]
    ]
    return images

async def list_containers():
    """
    Retrieve the list of local images being built by repo2docker.
    Images are built in a Docker container.
    """
    async with Docker() as docker:
        r2d_containers = await docker.containers.list(
            filters=json.dumps({"label": ["repo2docker.ref"]})
        )
    containers = [
        {
            "repo": get_optional_value(container, 'repo') or container["Labels"]["repo2docker.repo"],
            "ref": container["Labels"]["repo2docker.ref"],
            "spawnref": get_spawn_ref(container),
            "image_name": container["Labels"]["repo2docker.build"],
            "display_name": get_optional_value(container, 'display_name') or container["Labels"]["governedrunner.display_name"],
            "mem_limit": container["Labels"]["governedrunner.mem_limit"],
            "cpu_limit": container["Labels"]["governedrunner.cpu_limit"],
            "status": "building",
        }
        for container in r2d_containers
        if "repo2docker.build" in container["Labels"]
    ]
    return containers
