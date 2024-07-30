from traitlets import Unicode
from traitlets.config import Configurable


class BaseSpawnerMixin(Configurable):

    rdmfs_token = Unicode(
        help="""
        A token for RDMFS.
        """,
    ).tag(config=True)

    rdmfs_image = Unicode(
        "gcr.io/nii-ap-ops/rdmfs:20211221",
        help="""
        An image for RDMFS.
        """,
    ).tag(config=True)
