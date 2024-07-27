from traitlets import Unicode, Dict, List, Callable
from traitlets.config import LoggingConfigurable


class ImageBuilder(LoggingConfigurable):
    """Base class for image builders"""

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

    optional_labels = Dict(
        {},
        help="""Optional labels to set on the built image.
        """,
    ).tag(config=True)

    async def build(self, source_url: str) -> str:
        """
        Build a Docker image from the source URL.

        Args:
            source_url: Source URL

        Returns:
            The built image URL
        """
        raise NotImplementedError()
