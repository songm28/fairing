import logging


from kubernetes import client

from fairing.builders.base_builder import BaseBuilder
from fairing.builders import dockerfile
from fairing.constants import constants
from fairing.kubernetes.manager import KubeManager
from fairing.builders.cluster import gcs_context

logger = logging.getLogger(__name__)


class ClusterBuilder(BaseBuilder):
    """Builds a docker image in a Kubernetes cluster.


     Args:
        registry (str): Required. Registry to push image to
                        Example: gcr.io/kubeflow-images
        base_image (str): Base image to use for the image build
        preprocessor (BasePreProcessor): Preprocessor to use to modify inputs
                                         before sending them to docker build
        context_source (ContextSourceInterface): context available to the
                                                 cluster build
        push {bool} -- Whether or not to push the image to the registry
    """
    def __init__(self,
                 registry=None,
                 context_source=None,
                 preprocessor=None,
                 push=True,
                 base_image=constants.DEFAULT_BASE_IMAGE,
                 dockerfile_path=None):
        super().__init__(
                registry=registry,
                push=push,
                preprocessor=preprocessor,
                base_image=base_image,
            )
        self.manager = KubeManager()
        if context_source is None:
            context_source = gcs_context.GCSContextSource()
        self.context_source = context_source

    def build(self):
        dockerfile_path = dockerfile.write_dockerfile(
            dockerfile_path=self.dockerfile_path,
            path_prefix=self.preprocessor.path_prefix,
            base_image=self.base_image
        )
        self.preprocessor.output_map[dockerfile_path] = 'Dockerfile'
        context_path, context_hash = self.preprocessor.context_tar_gz()
        self.image_tag = self.full_image_name(context_hash)
        self.context_source.prepare(context_path)
        labels = {'fairing-builder': 'kaniko'}
        build_pod = client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=client.V1ObjectMeta(
                generate_name="fairing-builder-",
                labels=labels,
            ),
            spec=self.context_source.generate_pod_spec(self.image_tag, self.push)
        )
        created_pod = client. \
            CoreV1Api(). \
            create_namespaced_pod("default", build_pod)
        self.manager.log(
            name=created_pod.metadata.name,
            namespace=created_pod.metadata.namespace,
            selectors=labels)

        # clean up created pod and secret
        self.context_source.cleanup()
        client.CoreV1Api().delete_namespaced_pod(
            created_pod.metadata.name,
            created_pod.metadata.namespace,
            client.V1DeleteOptions())