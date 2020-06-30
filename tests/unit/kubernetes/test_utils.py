from kubeflow.fairing.kubernetes import utils as k8s_utils
from kubernetes.client.models.v1_pod_spec import V1PodSpec
from kubernetes.client.models.v1_container import V1Container
from kubernetes import client

# import pytest
import unittest

class TestUtils(unittest.TestCase):

    def test_resource_mutator(self):
        pod_spec = V1PodSpec(containers=[V1Container(
            name='model',
            image="image"
        )],)
        k8s_utils.get_resource_mutator(cpu=1.5, memory=0.5)(None, pod_spec, "")
        actual = pod_spec.containers[0].resources.limits
        expected = {'cpu': 1.5, 'memory': '0.47Gi'}
        assert actual == expected


    def test_resource_mutator_no_cpu(self):
        pod_spec = V1PodSpec(containers=[V1Container(
            name='model',
            image="image"
        )],)
        k8s_utils.get_resource_mutator(memory=0.5)(None, pod_spec, "")
        actual = pod_spec.containers[0].resources.limits
        expected = {'memory': '0.47Gi'}
        assert actual == expected


    def test_resource_mutator_no_mem(self):
        pod_spec = V1PodSpec(containers=[V1Container(
            name='model',
            image="image"
        )],)
        k8s_utils.get_resource_mutator(cpu=1.5)(None, pod_spec, "")
        actual = pod_spec.containers[0].resources.limits
        expected = {'cpu': 1.5}
        assert actual == expected

    def test_resource_mutator_gpu(self):
        pod_spec = V1PodSpec(containers=[V1Container(
            name='model',
            image="image"
        )],)
        k8s_utils.get_resource_mutator(gpu=1)(None, pod_spec, "")
        actual = pod_spec.containers[0].resources.limits
        expected = {'nvidia.com/gpu': 1}
        assert actual == expected

    def test_resource_mutator_gpu_vendor(self):
        pod_spec = V1PodSpec(containers=[V1Container(
            name='model',
            image="image"
        )],)
        k8s_utils.get_resource_mutator(gpu=2, gpu_vendor='amd')(None, pod_spec, "")
        actual = pod_spec.containers[0].resources.limits
        expected = {'amd.com/gpu': 2}
        assert actual == expected

    def test_add_env_no_env(self):
        pod_spec = V1PodSpec(containers=[V1Container(
            name='model',
            image="image"
        )],)
        env_vars = {'var1': 'value1', 'var2': 'value2'}
        k8s_utils.add_env(env_vars=env_vars)(None, pod_spec, "")
        actual = pod_spec.containers[0].env
        expected = [
            {'name': 'var1', 'value': 'value1', 'value_from': None},
            {'name': 'var2', 'value': 'value2', 'value_from': None}
        ]
        assert str(actual) == str(expected)

    def test_add_env_has_env(self):
        pod_spec = V1PodSpec(containers=[V1Container(
            name='model',
            image="image",
            env=[client.V1EnvVar(name='var0', value='value0')]
        )],)
        env_vars = {'var1': 'value1', 'var2': 'value2'}
        k8s_utils.add_env(env_vars=env_vars)(None, pod_spec, "")
        actual = pod_spec.containers[0].env
        expected = [
            {'name': 'var0', 'value': 'value0', 'value_from': None},
            {'name': 'var1', 'value': 'value1', 'value_from': None},
            {'name': 'var2', 'value': 'value2', 'value_from': None}
        ]
        assert str(actual) == str(expected)

    def test_add_env_fromconref_has_env(self):
        pod_spec = V1PodSpec(containers=[V1Container(
            name='model',
            image="image",
            env=[client.V1EnvVar(name='var0', value='value0')]
        )],)
        env_vars = {'var1': {'name':'config1', 'key':'key1', 'type':'configmap'}, \
                    'var2': {'name':'secret2', 'key':'key2', 'type':'secret'}, \
                    'var3':'value3'
                    }
        k8s_utils.add_env(env_vars=env_vars)(None, pod_spec, "")
        actual = pod_spec.containers[0].env
        expected = [
            {'name': 'var0', 'value': 'value0', 'value_from': None},
            {'name': 'var1', 'value': 'value1', 'value_from': None},
            {'name': 'var2', 'value': 'value2', 'value_from': None}
        ]
        # assert str(actual) == str(expected)
        print("actual:{}".format(str(actual)))
        print("expected:{}".format(str(expected)))
        print(pod_spec)
        self.assertTrue(str(actual)==str(expected))

    
    
if __name__=="__main__":
    unittest.main()