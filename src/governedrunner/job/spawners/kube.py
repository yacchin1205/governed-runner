from kubespawner import KubeSpawner
from tornado import web
from .base import BaseSpawnerMixin


class Repo2DockerKubeSpawner(BaseSpawnerMixin, KubeSpawner):
    """
    A custom spawner for using images built with repo2docker.
    """

    def get_env(self):
        env = super().get_env()
        if 'repo_url' in self.user_options:
            env['BINDER_REPO_URL'] = self.user_options['repo_url']
        for key in (
                'binder_ref_url',
                'binder_launch_host',
                'binder_persistent_request',
                'binder_request'):
            if key in self.user_options:
                env[key.upper()] = self.user_options[key]
        return env

    @property
    def extra_pod_config(self):
        pv_volumes = []
        init_containers = list(self.init_containers) + list(self.extra_init_containers)
        if 'rdm_node_id' not in self.user_options:
            return {
                'initContainers': init_containers,
                'volumes': pv_volumes,
            }
        return {
          'initContainers': init_containers,
          'volumes': pv_volumes + [
            {
              'name': 'mntdata',
              'emptyDir': {},
            },
          ]
        }

    @property
    def extra_init_containers(self):
        return []

    @property
    def extra_container_config(self):
        pv_mounts = []
        if 'rdm_node_id' not in self.user_options:
            return { 'volumeMounts': pv_mounts }
        return {
            'volumeMounts': pv_mounts + [
                {
                    'name': 'mntdata',
                    'mountPath': '/mnt',
                    'mountPropagation': 'HostToContainer',
                }
            ],
        }

    @property
    def extra_containers(self):
        if 'rdm_node_id' not in self.user_options:
            return []
        node_id = self.user_options['rdm_node_id']
        if not self.rdmfs_token:
            raise web.HTTPError(
                400,
                "No repo_token for: %s" % (node_id),
            )
        return [
            {
                'name': 'rdmfs',
                'image': self.rdmfs_image,
                'env': [
                  {
                    'name': 'RDM_NODE_ID',
                    'value': node_id,
                  },
                  {
                    'name': 'RDM_API_URL',
                    'value': self.user_options['rdm_api_url'],
                  },
                  {
                    'name': 'RDM_TOKEN',
                    'value': self.rdmfs_token,
                  },
                  {
                    'name': 'MOUNT_PATH',
                    'value': '/var/rdmfs/rdm',
                  },
                ],
                'lifecycle': {
                  'preStop': {
                    'exec': {
                      'command': ["/bin/sh","-c","xattr -w command terminate /var/rdmfs/rdm"],
                    }
                  }
                },
                'securityContext': {
                  'privileged': True,
                },
                'volumeMounts': [
                  {
                    'name': 'mntdata',
                    'mountPath': '/var/rdmfs',
                    'mountPropagation': 'Bidirectional',
                  }
                ]
            }
        ]
    # @property
    # def mount_binds(self):
    #     base_mount_binds = super().mount_binds.copy()
    #     if self.extra_mounts is None:
    #         return base_mount_binds
    #     base_mount_binds += [Mount(**m) for m in self.extra_mounts]
    #     return base_mount_binds

    # async def start(self, *args, **kwargs):
    #     await self.set_limits()
    #     await self.set_extra_mounts()
    #     return await super().start(*args, **kwargs)

    # async def stop(self, *args, **kwargs):
    #     await super().stop(*args, **kwargs)
    #     rdmfs_id = await self.get_rdmfs_object()
    #     if rdmfs_id is None:
    #         return
    #     await self.remove_object_by_id(rdmfs_id)
