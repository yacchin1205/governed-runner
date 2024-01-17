import logging
import re
from urllib.parse import urlparse

from aiodocker import Docker
from traitlets import Unicode, Dict, List, Callable

from governedrunner.api.rdm import RDMService
from .base import ImageBuilder


class DockerImageBuilder(ImageBuilder):
    """Builds a docker image from specified repository.
    """

    repo2docker_image = Unicode(
        "quay.io/jupyterhub/repo2docker:main",
        help="""The repo2docker image to use for building.
        """,
    ).tag(config=True)

    optional_envs = Dict(
        {},
        help="""Optional environment variables to pass to the builder.
        """,
    ).tag(config=True)

    extra_buildargs = List(
        [],
        help="""Extra build arguments to pass to the builder.
        """,
    ).tag(config=True)

    log_stream_callback = Callable(
        None,
        help="""Callback function to call when log is emitted.
        """,
    ).tag(config=True)

    async def build(self, source_url: str) -> str:
        ref = 'HEAD'

        labels = []

        builder_labels = {
            "repo2docker.repo": source_url,
            "repo2docker.ref": ref,
        }
        labels += [f"governedrunner.opt.{k}={v}" for k, v in self.optional_labels.items()]
        builder_labels.update(dict([(f"governedrunner.opt.{k}", v) for k, v in self.optional_labels.items()]))

        cmd = [
            "jupyter-repo2docker",
            "--ref",
            ref,
            "--user-name",
            "jovyan",
            "--user-id",
            "1100",
            "--no-run",
        ]

        for label in labels:
            cmd += [
                "--label",
                label
            ]

        for barg in self.extra_buildargs:
            cmd += [
                "--build-arg",
                barg
            ]

        cmd.append(source_url)
        envs = []
        for k, v in self.optional_envs.items():
            envs.append(f'{k}={v}')

        config = {
            "Cmd": cmd,
            "Image": self.repo2docker_image,
            "Labels": builder_labels,
            "Volumes": {
                "/var/run/docker.sock": {
                    "bind": "/var/run/docker.sock",
                    "mode": "rw",
                }
            },
            "Env": envs,
            "HostConfig": {
                "Binds": ["/var/run/docker.sock:/var/run/docker.sock"],
            },
            "Tty": False,
            "AttachStdout": False,
            "AttachStderr": False,
            "OpenStdin": False,
        }

        reuse_pattern = re.compile(r'Reusing existing image \(([^\)]+)\),.+')
        finished_pattern = re.compile(r'Successfully tagged\s+([^\s]+).*')
        image = None
        async with Docker() as docker:
            container = await docker.containers.run(config=config)
            async for log in container.log(stdout=True, stderr=True, follow=True):
                if self.log_stream_callback is not None:
                    self.log_stream_callback('building', log)
                log = log.rstrip("\n")
                m = reuse_pattern.match(log)
                if m:
                    image = m.group(1)
                    self.log.info(f'Resusing detected: {image}')
                m = finished_pattern.match(log)
                if m:
                    image = m.group(1)               
                    self.log.info(f'Finished detected: {image}')
                self.log.info(f'Builder({source_url}): {log}')
            if image is None:
                raise RuntimeError('Failed to build image')
            await container.delete()
        return image
