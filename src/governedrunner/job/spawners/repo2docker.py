import json
import os

from aiodocker import Docker
from aiodocker.exceptions import DockerError
from dockerspawner import DockerSpawner
from docker.errors import APIError
from docker.types import Mount
from jinja2 import Environment, BaseLoader
from jupyterhub.traitlets import ByteSpecification
from traitlets import Unicode
from traitlets.config import Configurable
from tornado import web

from .docker import list_images


# Default CPU period
# See: https://docs.docker.com/config/containers/resource_constraints/#limit-a-containers-access-to-memory#configure-the-default-cfs-scheduler
CPU_PERIOD = 100_000


class SpawnerMixin(Configurable):

    """
    Mixin for spawners that derive from DockerSpawner, to use local Docker images
    built with tljh-repo2docker.

    Call `set_limits` in the spawner `start` method to set the memory and cpu limits.
    """

    image_form_template = Unicode(
        """
        <style>
            #image-list {
                max-height: 600px;
                overflow: auto;
            }
            .image-info {
                font-weight: normal;
            }
        </style>
        <script>
            setTimeout(function() {
                selectServers();
            }, 100);

            function selectServers() {
                if (!window.location.hash.match(/^#.+/)) {
                    return;
                }
                const ref = window.location.hash.match(/^#(.+)$/)[1];
                $("input[image-data='" + ref + "']").prop('checked', true);
                console.log(ref);
            }
        </script>
        <div class='form-group' id='image-list'>
        {% for image in image_list %}
        <label for='image-item-{{ loop.index0 }}' class='form-control input-group'>
            <div class='col-md-1'>
                <input type='radio' name='image' image-data='{{ image.spawnref }}' id='image-item-{{ loop.index0 }}' value='{{ image.image_name }}' />
            </div>
            <div class='col-md-11'>
                <strong>{{ image.display_name }}</strong>
                <div class='row image-info'>
                    <div class='col-md-4'>
                        Repository:
                    </div>
                    <div class='col-md-8'>
                        <a href="{{ image.repo }}" target="_blank">{{ image.repo }}</a>
                    </div>
                </div>
                <div class='row image-info'>
                    <div class='col-md-4'>
                        Memory Limit (GB):
                    </div>
                    <div class='col-md-8'>
                        <strong>{{ image.mem_limit | replace("G", "") }}</strong>
                    </div>
                </div>
                <div class='row image-info'>
                    <div class='col-md-4'>
                        CPU Limit:
                    </div>
                    <div class='col-md-8'>
                        <strong>{{ image.cpu_limit }}</strong>
                    </div>
                </div>
            </div>
        </label>
        {% endfor %}
        </div>
        """,
        config=True,
        help="""
        Jinja2 template for constructing the list of images shown to the user.
        """,
    )

    rdmfs_base_path = Unicode(
        config=True,
        help="""
        A base path for RDMFS.
        """,
    )

    rdmfs_token = Unicode(
        config=True,
        help="""
        A token for RDMFS.
        """,
    )

    extra_mounts = None

    async def list_images(self):
        """
        Return the list of available images
        """
        return await list_images()

    async def get_options_form(self):
        """
        Override the default form to handle the case when there is only one image.
        """
        images = await self.list_images()

        # make default limits human readable
        default_mem_limit = self.mem_limit
        if isinstance(default_mem_limit, (float, int)):
            # default memory unit is in GB
            default_mem_limit /= ByteSpecification.UNIT_SUFFIXES["G"]
            if float(default_mem_limit).is_integer():
                default_mem_limit = int(default_mem_limit)

        default_cpu_limit = self.cpu_limit
        if default_cpu_limit and float(default_cpu_limit).is_integer():
            default_cpu_limit = int(default_cpu_limit)

        # add memory and cpu limits
        for image in images:
            image["mem_limit"] = image["mem_limit"] or default_mem_limit
            image["cpu_limit"] = image["cpu_limit"] or default_cpu_limit

        image_form_template = Environment(loader=BaseLoader).from_string(
            self.image_form_template
        )
        return image_form_template.render(image_list=images)

    async def set_limits(self):
        """
        Set the user environment limits if they are defined in the image
        """
        imagename = self.user_options.get("image")
        async with Docker() as docker:
            image = await docker.images.inspect(imagename)

        mem_limit = image["ContainerConfig"]["Labels"].get(
            "governedrunner.mem_limit", None
        )
        cpu_limit = image["ContainerConfig"]["Labels"].get(
            "governedrunner.cpu_limit", None
        )

        # override the spawner limits if defined in the image
        if mem_limit:
            self.mem_limit = mem_limit
        if cpu_limit:
            self.cpu_limit = float(cpu_limit)

        if self.cpu_limit:
            self.extra_host_config.update(
                {
                    "cpu_period": CPU_PERIOD,
                    "cpu_quota": int(float(CPU_PERIOD) * self.cpu_limit),
                }
            )

    async def set_extra_mounts(self):
        """
        Prepare volume binds for GRDM
        """
        imagename = self.user_options.get("image")
        async with Docker() as docker:
            image = await docker.images.inspect(imagename)
        
        provider_prefix = image["ContainerConfig"]["Labels"].get(
            "governedrunner.opt.provider", None
        )
        if provider_prefix != 'rdm':
            return
        await self._set_rdm_mounts(image)

    async def _set_rdm_mounts(self, image):
        repo = image["ContainerConfig"]["Labels"].get(
            "governedrunner.opt.repo", None
        )
        repo_token = self.rdmfs_token
        if not repo_token:
            raise web.HTTPError(
                400,
                "No repo_token for: %s" % (repo),
            )
        self.log.info("Preparing RDMFS... " + 'name=' + repr(self.user.name) + ', repo=' + repr(repo))
        mount_path = os.path.join(self.rdmfs_base_path, self.container_name)
        if not os.path.exists(mount_path):
            os.makedirs(mount_path)
        self.extra_mounts = [
            dict(type='bind', source=mount_path, target='/mnt', propagation='rshared'),
        ]
        rdmfs_id = await self.get_rdmfs_object()
        if rdmfs_id is not None:
            await self.remove_object_by_id(rdmfs_id)
        rdmfs_id = await self.create_rdmfs_object({
            'RDM_NODE_ID': image["ContainerConfig"]["Labels"].get(
                "governedrunner.opt.user.rdm_node_id", None
            ),
            'RDM_API_URL': image["ContainerConfig"]["Labels"].get(
                "governedrunner.opt.user.rdm_api_url", None
            ),
            'RDM_TOKEN': repo_token,
            'MOUNT_PATH': '/mnt/rdm',
        })
        await self.start_object_by_id(rdmfs_id)

    async def get_rdmfs_object(self):
        object_name = self.object_name + '_rdmfs'
        self.log.debug("Getting %s '%s'", self.object_type, object_name)
        try:
            async with Docker() as docker:
                obj = await docker.containers.get(object_name)
            return obj.id
        except DockerError as e:
            if e.status == 404:
                self.log.info(
                    "%s '%s' is gone", self.object_type.title(), object_name
                )
            elif e.status == 500:
                self.log.info(
                    "%s '%s' is on unhealthy node",
                    self.object_type.title(),
                    object_name,
                )
            else:
                raise
        return None

    async def create_rdmfs_object(self, env):
        host_config = dict(
            Mounts=[
                {
                    "Type": "bind",
                    "Source": m['source'],
                    "Target": "/mnt",
                    "ReadOnly": False,
                    "BindOptions": {
                        "Propagation": "rshared",
                    },
                }
                for m in (self.extra_mounts or [])
            ],
            Privileged=True,
        )
        create_kwargs = dict(
            Image='gcr.io/nii-ap-ops/rdmfs:20211221',
            Env=[f'{k}={v}' for k, v in env.items()],
            AutoRemove=True,
            HostConfig=host_config,
        )
        async with Docker() as docker:
            obj = await docker.containers.create(
                create_kwargs,
                name=self.container_name + '_rdmfs',
            )
        return obj.id

    async def start_object_by_id(self, object_id):
        async with Docker() as docker:
            obj = await docker.containers.get(object_id)
            await obj.start()

    async def remove_object_by_id(self, object_id):
        self.log.info("Removing %s %s", self.object_type, object_id)
        try:
            async with Docker() as docker:
                obj = await docker.containers.get(object_id)
                desc = await obj.show()
                if 'State' in desc and desc['State']['Running']:
                    self.log.info('terminating...')
                    exec = await obj.exec(["/bin/sh","-c","xattr -w command terminate /mnt/rdm"])
                    result = await exec.start(detach=True)
                    self.log.info('terminated: {}'.format(result))
                    self.log.info('deleting...')
                    await obj.delete()
                else:
                    self.log.info('deleting...')
                    await obj.delete()
        except DockerError as e:
            if e.status == 409:
                self.log.debug(
                    "Already removed %s: %s", self.object_type, object_id
                )
            elif e.status == 404:
                self.log.debug(
                    "Already removed %s: %s", self.object_type, object_id
                )
            else:
                raise


class Repo2DockerSpawner(SpawnerMixin, DockerSpawner):
    """
    A custom spawner for using local Docker images built with repo2docker.
    """

    @property
    def mount_binds(self):
        base_mount_binds = super().mount_binds.copy()
        if self.extra_mounts is None:
            return base_mount_binds
        base_mount_binds += [Mount(**m) for m in self.extra_mounts]
        return base_mount_binds

    async def start(self, *args, **kwargs):
        await self.set_limits()
        await self.set_extra_mounts()
        return await super().start(*args, **kwargs)

    async def stop(self, *args, **kwargs):
        await super().stop(*args, **kwargs)
        rdmfs_id = await self.get_rdmfs_object()
        if rdmfs_id is None:
            return
        await self.remove_object_by_id(rdmfs_id)
