import re
from urllib.parse import urlparse

from traitlets import Unicode, validate, TraitError
from kubernetes import client, config as kube_config, watch
from binderhub.utils import ByteSpecification, KUBE_REQUEST_TIMEOUT

from .base import ImageBuilder

def _generate_build_name(source_url: str, ref: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]', '-', f"build-{source_url}-{ref}").lower()

class KubeImageBuilder(ImageBuilder):
    """Builds a docker image from specified repository.
    """

    namespace = Unicode(
        "default",
        help="""The namespace to use for building.
        """,
    ).tag(config=True)

    component_label = Unicode(
        "governedrunner",
        help="""The component label to use for building.
        """,
    ).tag(config=True)

    memory_request = ByteSpecification(
        0,
        help="""Amount of memory to request for a builder.
        0 reserves no memory.
""",
    ).tag(config=True)

    memory_limit = ByteSpecification(
        0,
        help="""Max amount of memory allocated for a builder.
        0 sets no limit.
"""
    ).tag(config=True)

    build_docker_host = Unicode(
        "unix://var/run/docker.sock",
        help="""The docker host to use for building.
        """,
    ).tag(config=True)

    @validate('build_docker_host')
    def docker_build_host_validate(self, proposal):
        parts = urlparse(proposal.value)
        if parts.scheme != 'unix' or parts.netloc != '':
            raise TraitError("Only unix domain sockets on same node are supported for build_docker_host")
        return proposal.value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            kube_config.load_incluster_config()
        except Exception:
            kube_config.load_kube_config()
        self.kube_client = client.CoreV1Api()

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

        build_name = _generate_build_name(source_url, ref)
        volume_mounts = [
            client.V1VolumeMount(mount_path="/var/run/docker.sock", name="docker-socket")
        ]

        docker_socket_path = urlparse(self.build_docker_host).path
        volumes = [client.V1Volume(
            name="docker-socket",
            host_path=client.V1HostPathVolumeSource(path=docker_socket_path, type='Socket')
        )]

        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name=build_name,
                labels={
                    "name": build_name,
                    "component": self.component_label,
                },
                annotations={
                    "governedrunner/source-url": source_url,
                    "governedrunner/ref": ref,
                }
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="repo2docker",
                        image=self.repo2docker_image,
                        command=cmd,
                        env=[client.V1EnvVar(name=k, value=v) for k, v in self.optional_envs.items()],
                        resources=client.V1ResourceRequirements(
                            limits={'memory': self.memory_limit},
                            requests={'memory': self.memory_request},
                        ),
                        volume_mounts=volume_mounts,
                    )
                ],
                volumes=volumes,
                restart_policy="Never",
            ),
        )
        try:
            ret = self.kube_client.create_namespaced_pod(
                self.namespace,
                pod,
                _request_timeout=KUBE_REQUEST_TIMEOUT,
            )
        except client.rest.ApiException as e:
            if e.status == 409:
                self.log.warning(f"Pod {build_name} already exists, skipping")
            else:
                raise
        else:
            self.log.info(f"Created pod {build_name}")

        self.log.info(f"Watching pod {build_name}")
        w = watch.Watch()
        try:
            for event in w.stream(
                self.kube_client.list_namespaced_pod,
                namespace=self.namespace,
                label_selector=f"name={build_name}",
                _request_timeout=KUBE_REQUEST_TIMEOUT,
            ):
                pod = event['object']
                phase = pod.status.phase
                self.log.info(f"Pod {build_name} is in phase {phase}")
                if phase == "Succeeded":
                    break
                if phase == "Failed":
                    raise RuntimeError(f"Pod {build_name} failed")
            for line in self.kube_client.read_namespaced_pod_log(
                name=build_name,
                namespace=self.namespace,
                _request_timeout=KUBE_REQUEST_TIMEOUT,
            ).splitlines():
                self.log.info(f"Pod {build_name}: {line}")
        finally:
            w.stop()




