from traitlets import Dict
from traitlets.config import LoggingConfigurable


class ImageBuilder(LoggingConfigurable):
    """Base class for image builders"""

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
