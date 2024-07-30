import asyncio
import re
from urllib.parse import urlparse, quote
from uuid import uuid4

from traitlets import Unicode, Int, validate, TraitError
from kubernetes_asyncio import client, config as kube_config, watch
from kubernetes_asyncio.client.api_client import ApiClient
from kubernetes_asyncio.client.rest import ApiException
from binderhub.utils import ByteSpecification, KUBE_REQUEST_TIMEOUT

from .base import ImageBuilder


POD_REQUEST_TIMEOUT = 30


def _generate_image_name(image_prefix: str, source_url: str, ref: str) -> str:
    encoded_url = quote(source_url, safe='')
    return image_prefix + re.sub(r'[^a-zA-Z0-9]', '-', f"{encoded_url}").lower() + f":{ref}"


def _generate_build_name(source_url: str, ref: str) -> str:
    encoded_url = quote(source_url, safe='')
    name = re.sub(r'[^a-zA-Z0-9]', '-', f"build-{encoded_url}-{ref}").lower()
    if len(name) > 63:
        name = name[:63]
    return name


class KubeImageBuilder(ImageBuilder):
    """Builds a docker image from specified repository.
    """

    initialized = False

    namespace = Unicode(
        "default",
        help="""The namespace to use for building.
        """,
    ).tag(config=True)

    image_prefix = Unicode(
        "",
        help="""The prefix to use for the built image.
        """,
    ).tag(config=True)

    push_secret = Unicode(
        "binder-push-secret",
        allow_none=True,
        help="""The name of the secret to use for pushing images.
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

    build_timeout = Int(
        60 * 60,
        help="""The timeout in seconds for building.
        """,
    ).tag(config=True)

    log_tail_lines = Int(
        100,
        help="""The number of lines to tail in the logs.
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
        self.initialized = False

    async def wait_for_running(
        self,
        kube_client: client.CoreV1Api,
        build_name: str,
        timeout_seconds: int = 30
    ) -> bool:
        w = watch.Watch()
        async with w.stream(
            kube_client.list_namespaced_pod,
            namespace=self.namespace,
            label_selector=f"name={build_name}",
            timeout_seconds=timeout_seconds,
        ) as stream:
            async for event in stream:
                pod = event['object']
                phase = pod.status.phase
                self.log.info(f"Pod {build_name} is in phase {phase}")
                if phase == "Running":
                    return True
                if phase == "Succeeded":
                    return True
                if phase == "Failed":
                    raise RuntimeError(f"Pod {build_name} failed")
        return False

    async def build(self, source_url: str) -> str:
        if not self.initialized:
            try:
                kube_config.load_incluster_config()
            except Exception:
                await kube_config.load_kube_config()
            self.initialized = True
        async with ApiClient() as api:
            kube_client = client.CoreV1Api(api)
            ref = str(uuid4())

            labels = []

            builder_labels = {
                "repo2docker.repo": source_url,
                "repo2docker.ref": ref,
            }
            labels += [f"governedrunner.opt.{k}={v}" for k, v in self.optional_labels.items()]
            builder_labels.update(dict([(f"governedrunner.opt.{k}", v) for k, v in self.optional_labels.items()]))

            image_name = _generate_image_name(self.image_prefix, source_url, ref)

            # image_name
            cmd = [
                "jupyter-repo2docker",
                "--ref",
                ref,
                "--image",
                image_name,
                "--user-name",
                "jovyan",
                "--user-id",
                "1100",
                "--no-run",
            ]

            if self.push_secret:
                cmd.append('--push')

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

            if self.push_secret:
                volume_mounts.append(client.V1VolumeMount(mount_path="/root/.docker", name='docker-push-secret'))
                volumes.append(client.V1Volume(
                    name='docker-push-secret',
                    secret=client.V1SecretVolumeSource(secret_name=self.push_secret)
                ))

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
                await asyncio.wait_for(
                    kube_client.create_namespaced_pod(
                        self.namespace,
                        pod,
                    ),
                    POD_REQUEST_TIMEOUT,
                )
            except asyncio.TimeoutError:
                raise
            except ApiException as e:
                if e.status == 409:
                    self.log.warning(f"Pod {build_name} already exists, skipping")
                else:
                    raise
            else:
                self.log.info(f"Created pod {build_name}")

            self.log.info(f"Waiting for pod {build_name} to start")
            running = await self.wait_for_running(
                kube_client,
                build_name,
                timeout_seconds=self.build_timeout,
            )

            if not running:
                raise RuntimeError(f"Pod {build_name} did not start in time")

            self.log.info(f"Watching pod {build_name} to completion")

            reuse_pattern = re.compile(r'Reusing existing image \(([^\)]+)\),.+')
            finished_pattern = re.compile(r'Successfully tagged\s+([^\s]+).*')
            image = None

            resp = await kube_client.read_namespaced_pod_log(
                name=build_name,
                namespace=self.namespace,
                follow=True,
                tail_lines=self.log_tail_lines,
                _preload_content=False,
            )
            while True:
                line = await resp.content.readline()
                if not line:
                    break
                line = line.decode('utf-8')
                if self.log_stream_callback is not None:
                    self.log_stream_callback('building', line)
                log = line.rstrip("\n")
                m = reuse_pattern.match(log)
                if m:
                    image = m.group(1)
                    self.log.info(f'Reusing detected: {image}')
                m = finished_pattern.match(log)
                if m:
                    image = m.group(1)
                    self.log.info(f'Finished detected: {image}')
                self.log.info(f'Builder({source_url}): {log}')

            self.log.info(f"Deleting pod {build_name}...")
            delete_options = client.V1DeleteOptions()

            try:
                await asyncio.wait_for(
                    kube_client.delete_namespaced_pod(
                        name=build_name,
                        namespace=self.namespace,
                        body=delete_options,
                    ),
                    POD_REQUEST_TIMEOUT,
                )
            except asyncio.TimeoutError:
                raise
            except ApiException as e:
                if e.status == 404:
                    self.log.warning(f"Pod {build_name} already gone, skipping")
                else:
                    raise
            self.log.info(f"Deleted pod {build_name}")

            if image is None:
                raise RuntimeError('Failed to build image')
            return image

