from kubernetes import client
from kubernetes.client.models.v1_resource_requirements import V1ResourceRequirements
from kubeflow.fairing.constants import constants


def get_resource_mutator(cpu=None, memory=None, gpu=None, gpu_vendor='nvidia'):
    """The mutator for getting the resource setting for pod spec.

    The useful example:
    https://github.com/kubeflow/fairing/blob/master/examples/train_job_api/main.ipynb

    :param cpu: Limits and requests for CPU resources (Default value = None)
    :param memory: Limits and requests for memory (Default value = None)
    :param gpu: Limits for GPU (Default value = None)
    :param gpu_vendor: Default value is 'nvidia', also can be set to 'amd'.
    :returns: object: The mutator function for setting cpu and memory in pod spec.

    """
    def _resource_mutator(kube_manager, pod_spec, namespace): #pylint:disable=unused-argument
        if cpu is None and memory is None and gpu is None:
            return
        if pod_spec.containers and len(pod_spec.containers) >= 1:
            # All cloud providers specify their instace memory in GB
            # so it is peferable for user to specify memory in GB
            # and we convert it to Gi that K8s needs
            limits = {}
            if cpu:
                limits['cpu'] = cpu
            if memory:
                memory_gib = "{}Gi".format(round(memory/1.073741824, 2))
                limits['memory'] = memory_gib
            if gpu:
                limits[gpu_vendor + '.com/gpu'] = gpu
            if pod_spec.containers[0].resources:
                if pod_spec.containers[0].resources.limits:
                    pod_spec.containers[0].resources.limits = {}
                for k, v in limits.items():
                    pod_spec.containers[0].resources.limits[k] = v
            else:
                pod_spec.containers[0].resources = V1ResourceRequirements(limits=limits)
    return _resource_mutator


def mounting_pvc(pvc_name, pvc_mount_path=constants.PVC_DEFAULT_MOUNT_PATH):
    """The function for pod_spec_mutators to mount persistent volume claim.

    :param pvc_name: The name of persistent volume claim
    :param pvc_mount_path: Path for the persistent volume claim mounts to.
    :returns: object: function for mount the pvc to pods.

    """
    mounting_name = str(constants.PVC_DEFAULT_VOLUME_NAME) + pvc_name
    def _mounting_pvc(kube_manager, pod_spec, namespace): #pylint:disable=unused-argument
        volume_mount = client.V1VolumeMount(
            name=mounting_name, mount_path=pvc_mount_path)
        if pod_spec.containers[0].volume_mounts:
            pod_spec.containers[0].volume_mounts.append(volume_mount)
        else:
            pod_spec.containers[0].volume_mounts = [volume_mount]

        volume = client.V1Volume(
            name=mounting_name,
            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=pvc_name))
        if pod_spec.volumes:
            pod_spec.volumes.append(volume)
        else:
            pod_spec.volumes = [volume]
    return _mounting_pvc

# def add_env(env_vars):
#     """The function for pod_spec_mutators to add custom environment vars.
#     :param vars: dict of custom environment vars.
#     :returns: object: function for add environment vars to pods.
#     """
#     def _add_env(kube_manager, pod_spec, namespace): #pylint:disable=unused-argument
#         env_list = []
#         for env_name, env_value in env_vars.items():
#             env_list.append(client.V1EnvVar(name=env_name, value=env_value))

#         if pod_spec.containers and len(pod_spec.containers) >= 1:
#             if pod_spec.containers[0].env:
#                 pod_spec.containers[0].env.extend(env_list)
#             else:
#                 pod_spec.containers[0].env = env_list
#     return _add_env

def build_env_list_for_pod(env_vars):
    env_list = []
    for env_name, env_value in env_vars.items():
        if env_name is None or env_value is None : continue
        if type(env_value)==str: # env is key/value pair
            env_list.append(client.V1EnvVar(name=env_name, value=env_value))

        elif type(env_value)==dict: # env is ref
            if env_value.keys() is None or len(env_value.keys()) < 3: continue
            if "type" not in env_value.keys() or "name" not in env_value.keys() or "key" not in env_value.keys(): continue
            
            ref_type=env_value["type"]
            ref_name=env_value["name"]
            ref_key=env_value["key"]
            ref_selector = None
            env_var_source = None
            if ref_type.lower() == "configmap": 
                ref_selector=client.V1ConfigMapKeySelector(key=ref_key, name=ref_name)
                env_var_source = client.V1EnvVarSource(config_map_key_ref=ref_selector)
            elif ref_type.lower() == "secret": 
                ref_selector=client.V1SecretKeySelector(key=ref_key, name=ref_name)
                env_var_source = client.V1EnvVarSource(secret_key_ref=ref_selector)
            elif ref_type.lower() == "field": pass
            elif ref_type.lower() == "resource_field": pass
            
            if env_var_source is not None: env_list.append(client.V1EnvVar(name=env_name, value_from=env_var_source))
    return env_list

def add_env(env_vars):
    """The function for pod_spec_mutators to add custom environment vars.
    :param env_vars: dict of custom environment vars.
                 key -> env var name
                 value -> dict or str, {"name":ref_name,"key":ref_key,"type":ref_type(configmap/secret/field/resourcefield)}
    :returns: object: function for add environment vars to pods.
    """
    def _add_env(kube_manager, pod_spec, namespace): #pylint:disable=unused-argument
        env_list = build_env_list_for_pod(env_vars=env_vars)
        if pod_spec.containers and len(pod_spec.containers) >= 1 and len(env_list) > 0:
            if pod_spec.containers[0].env:
                pod_spec.containers[0].env.extend(env_list)
            else:
                pod_spec.containers[0].env = env_list
    return _add_env