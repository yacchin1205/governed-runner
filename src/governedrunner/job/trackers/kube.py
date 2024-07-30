from typing import Any

from kubernetes_asyncio import client, watch
from kubernetes_asyncio.client.api_client import ApiClient

from traitlets.config import LoggingConfigurable

from .base import JobTracker, ProcessTracker


class KubePodTracker(ProcessTracker):
    log: Any
    pod: str
    namespace: str
    log_tail_lines: int = 100

    def __init__(self, parent: LoggingConfigurable, pod: str, namespace: str):
        self.pod = pod
        self.namespace = namespace
        self.log = parent.log

    async def wait_for_running(
        self,
        kube_client: client.CoreV1Api,
        timeout_seconds: int = 30
    ) -> bool:
        w = watch.Watch()
        async with w.stream(
            kube_client.list_namespaced_pod,
            namespace=self.namespace,
            label_selector=f"name={self.pod}",
            timeout_seconds=timeout_seconds,
        ) as stream:
            async for event in stream:
                pod = event['object']
                phase = pod.status.phase
                self.log.info(f"Pod {self.pod} is in phase {phase}")
                if phase == "Running":
                    notebook_container_status = pod.status.container_statuses[0]
                    self.log.info(f"Container {notebook_container_status.name} is in state {notebook_container_status.state}")
                    if notebook_container_status.started:
                        return True
                if phase == "Succeeded":
                    return True
                if phase == "Failed":
                    raise RuntimeError(f"Pod {self.pod} failed")
        return False

    async def wait(self, log_stream_callback):
        async with ApiClient() as api:
            kube_client = client.CoreV1Api(api)

            self.log.info(f"Waiting for pod {self.pod} to start")
            await self.wait_for_running(kube_client)

            self.log.info(f"Reading logs from pod {self.pod}")
            resp = await kube_client.read_namespaced_pod_log(
                name=self.pod,
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
                if log_stream_callback is None:
                    continue
                log_stream_callback('running', line)

            self.log.info(f"Retrieving exit code of pod {self.pod}")
            pod = await kube_client.read_namespaced_pod(self.pod, self.namespace)
            notebook_container_status = pod.status.container_statuses[0]
            self.log.info(f"Container {notebook_container_status.name} is in state {notebook_container_status.state}")
            if notebook_container_status.state.terminated is None:
                raise RuntimeError(f"Pod {self.pod} is not terminated")
            return notebook_container_status.state.terminated.exit_code


class KubeTracker(JobTracker):
    async def track_process(self, spawner, spawner_response):
        return KubePodTracker(self, spawner.pod_name, spawner.namespace)
