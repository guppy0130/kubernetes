from copy import deepcopy
from enum import StrEnum
from pathlib import Path
from typing import Any, Optional

import typer
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

app = typer.Typer()


def recursively_wrap_strs_in_ruamel_double_quote(obj: Any) -> Any:
    """Double quote all the strings (recursively)"""
    if isinstance(obj, str):
        return DoubleQuotedScalarString(obj)
    elif isinstance(obj, dict):
        return {
            k: recursively_wrap_strs_in_ruamel_double_quote(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [recursively_wrap_strs_in_ruamel_double_quote(x) for x in obj]
    return obj


class DoubleQuotedWrapperYAML(YAML):
    """
    Double quote all the strings
    """

    def dump(
        self: Any,
        data,
        stream: Any = None,
        *,
        transform: Any = None,
    ) -> Any:
        # double quote all the strings
        data = recursively_wrap_strs_in_ruamel_double_quote(data)
        # format the way we like it
        if isinstance(data, (list, set)):
            self.indent(mapping=2, sequence=2, offset=0)
        else:
            self.indent(mapping=2, sequence=4, offset=2)
        return super().dump(data, stream, transform=transform)


yaml = DoubleQuotedWrapperYAML()
yaml.explicit_start = True


# TODO: generate dynamically
class Env(StrEnum):
    """
    k8s manifest deployment locations
    """

    CHIN_HOSTED_GUPPY = "chin-hosted-guppy"
    ANTIOCH = "antioch"
    CHICAGO = "chicago"


ENV_TO_TZ: dict[Env, str] = {
    Env.ANTIOCH: "America/Los_Angeles",
    Env.CHICAGO: "America/Chicago",
    Env.CHIN_HOSTED_GUPPY: "America/Chicago",
}

ENV_TO_PVC_STORAGE_CLASS: dict[Env, str] = {
    Env.ANTIOCH: "topolvm-nvme-ext4",
    Env.CHICAGO: "csi-rbd-sc",
}


class Manifest(StrEnum):
    DEPLOYMENT = "deployment"
    INGRESS = "ingress"
    SERVICE = "service"
    PVC = "pvc"


BASE_INGRESS_MANIFEST = {
    "apiVersion": "networking.k8s.io/v1",
    "kind": "Ingress",
    "metadata": {"name": ""},
}

BASE_SERVICE_MANIFEST = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": ""},
}

BASE_DEPLOYMENT_MANIFEST = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {"name": ""},
    "spec": {},
}

BASE_PVC_MANIFEST = {
    "apiVersion": "v1",
    "kind": "PersistentVolumeClaim",
    "metadata": {"name": ""},
    "spec": {
        "resources": {"requests": {"storage": "1Gi"}},
        "volumeMode": "Filesystem",
        "accessModes": ["ReadWriteOnce"],
    },
}

BASE_KUSTOMIZATION_MANIFEST = {
    "apiVersion": "kustomize.config.k8s.io/v1beta1",
    "kind": "Kustomization",
    "namespace": "default",
    "labels": [{"pairs": {"app": ""}, "includeSelectors": True}],
    "resources": [],
}


def base_manifest_generator(
    manifest_type: Manifest, app_name: str, port: Optional[int] = None
) -> dict[str, Any]:
    """
    Generates base k8s manifests for different resource types.

    Args:
        manifest_type: Type of manifest to generate (ingress, service, pvc)
        app_name: Name of the application
        port: Optional port number required for ingress and pvc manifests

    Returns:
        Dictionary containing the base k8s manifest
    """
    if manifest_type in {Manifest.INGRESS, Manifest.PVC} and port is None:
        raise ValueError(f"{manifest_type=} requires a port")

    extras = {"metadata": {"name": app_name}}

    match manifest_type:
        case Manifest.INGRESS:
            return (
                BASE_INGRESS_MANIFEST
                | extras
                | {
                    "spec": {
                        "rules": [
                            {
                                "host": f"{app_name}.k3s.home",
                                "http": {
                                    "paths": [
                                        {
                                            "path": "/",
                                            "pathType": "Prefix",
                                            "backend": {
                                                "service": {
                                                    "name": app_name,
                                                    "port": {"name": app_name},
                                                }
                                            },
                                        }
                                    ]
                                },
                            }
                        ]
                    },
                }
            )
        case Manifest.SERVICE:
            return (
                BASE_SERVICE_MANIFEST
                | extras
                | {
                    "spec": {
                        "ports": [{"port": port, "name": app_name}],
                        "selector": {"app": app_name},
                    }
                }
            )
        case Manifest.PVC:
            return BASE_PVC_MANIFEST | extras | {}
        case Manifest.DEPLOYMENT:
            return (
                BASE_DEPLOYMENT_MANIFEST
                | extras
                | {
                    "spec": {
                        "replicas": 1,
                        "selector": {"matchLabels": {"app": app_name}},
                        "strategy": {"type": "RollingUpdate"},
                        "template": {
                            "spec": {
                                "containers": [
                                    {
                                        "name": app_name,
                                        "image": "",
                                        # the env is really important
                                        "env": [],
                                    }
                                ]
                            }
                        },
                    }
                }
            )

    raise ValueError(f"Unknown {manifest_type=}")


def generate_patches(
    manifest_type: Manifest, env: Env
) -> list[dict[str, Any]]:
    """
    Generate patches based on the env
    """
    match manifest_type:
        case Manifest.DEPLOYMENT:
            return [
                {
                    "path": "/spec/template/spec/containers/0/env/-",
                    "op": "add",
                    "value": {
                        "name": "TZ",
                        "value": ENV_TO_TZ[env],
                    },
                }
            ]
        case Manifest.PVC:
            if env in ENV_TO_PVC_STORAGE_CLASS:
                return [
                    {
                        "path": "/spec/storageClassName",
                        "op": "replace",
                        "value": ENV_TO_PVC_STORAGE_CLASS[env],
                    }
                ]

    # TODO: maybe should raise here instead to indicate no patches necessary
    return []


@app.command()
def generate(
    name: str = typer.Option(
        ..., help="New top level folder to make/app being deployed"
    ),
    envs: list[Env] = typer.Option(
        default_factory=list, help="Envs to generate overlays for"
    ),
    manifests: list[Manifest] = typer.Option(
        default_factory=list, help="Manifests to generate"
    ),
    port: Optional[int] = typer.Option(None, help="Port for service/ingress"),
):
    """
    Generate new app kustomize directories and manifest components. based on
    the extra manifests provided, modify the deployments, kustomization, etc.
    """

    # ensure the deployment manifest is always present
    if Manifest.DEPLOYMENT not in manifests:
        manifests.append(Manifest.DEPLOYMENT)
    manifests = sorted(manifests)

    # setup structure and write files
    parent_dir = Path(__file__, "../", name).resolve()
    base_dir = Path(parent_dir, "base")
    base_dir.mkdir(parents=True, exist_ok=True)

    base_kustomization = deepcopy(BASE_KUSTOMIZATION_MANIFEST)
    base_kustomization["labels"][0]["pairs"]["app"] = name

    base_manifest_dict: dict[Manifest, dict[str, Any]] = {}
    for manifest in manifests:
        output = Path(base_dir, manifest.value + ".yml")
        generated_manifest = base_manifest_generator(
            manifest_type=manifest, app_name=name, port=port
        )
        base_manifest_dict[manifest] = generated_manifest
        base_kustomization["resources"].append(
            str(output.relative_to(base_dir))
        )

    # reconcile extra base manifests
    deployment_spec = base_manifest_dict[Manifest.DEPLOYMENT]["spec"]
    deployment_template = deployment_spec["template"]["spec"]
    manifest_first_container = deployment_template["containers"][0]
    if {Manifest.SERVICE, Manifest.DEPLOYMENT}.issubset(manifests):
        manifest_first_container["ports"] = [
            {"containerPort": port, "name": name}
        ]
    if {Manifest.PVC, Manifest.DEPLOYMENT}.issubset(manifests):
        manifest_first_container["volumeMounts"] = [
            {"mountPath": "/mnt/pvc", "name": name}
        ]
        deployment_template["volumes"] = [
            {"name": name, "persistentVolumeClaim": {"claimName": name}}
        ]
        # RWO PVC may need this
        deployment_spec["strategy"]["type"] = "Recreate"

    # write all the base manifests to disk
    for manifest_type, manifest in base_manifest_dict.items():
        output = Path(base_dir, manifest_type.value + ".yml")
        yaml.dump(manifest, output)

    # write base kustomization file
    base_kustomization_file = Path(base_dir, "kustomization.yml")
    yaml.dump(base_kustomization, base_kustomization_file)

    # handle each of the envs now
    for env in envs:
        overlay_dir = Path(parent_dir, "overlays", env)
        overlay_dir.mkdir(parents=True, exist_ok=True)

        # generate patches for deployment and pvc if they exist
        extra_resources: list[Path] = []
        for manifest_type in {Manifest.DEPLOYMENT, Manifest.PVC}.intersection(
            manifests
        ):
            output = Path(overlay_dir, f"{manifest_type.value}-patch.yml")
            patches = generate_patches(manifest_type=manifest_type, env=env)
            if patches:  # if no patches, don't generate file
                extra_resources.append(output)
                yaml.dump(patches, output)

        # write the kustomization file for the env
        env_kustomization = deepcopy(BASE_KUSTOMIZATION_MANIFEST)
        env_kustomization["labels"][0]["pairs"]["app"] = name
        env_kustomization["resources"].extend(
            [
                str(base_dir.relative_to(overlay_dir, walk_up=True)),
                *[str(r.relative_to(overlay_dir)) for r in extra_resources],
            ]
        )
        env_kustomization_file = Path(overlay_dir, "kustomization.yml")
        yaml.dump(env_kustomization, env_kustomization_file)


if __name__ == "__main__":
    app()
