# ceph-csi

From <https://docs.ceph.com/en/latest/rbd/rbd-kubernetes/>.

## Base

Sets up the following:

```text
storageclass.storage.k8s.io/csi-rbd-sc created
serviceaccount/rbd-csi-nodeplugin created
serviceaccount/rbd-csi-provisioner created
role.rbac.authorization.k8s.io/rbd-external-provisioner-cfg created
clusterrole.rbac.authorization.k8s.io/rbd-csi-nodeplugin created
clusterrole.rbac.authorization.k8s.io/rbd-external-provisioner-runner created
rolebinding.rbac.authorization.k8s.io/rbd-csi-provisioner-role-cfg created
clusterrolebinding.rbac.authorization.k8s.io/rbd-csi-nodeplugin created
clusterrolebinding.rbac.authorization.k8s.io/rbd-csi-provisioner-role created
configmap/ceph-config created
configmap/ceph-csi-config created
configmap/ceph-csi-encryption-kms-config created
secret/csi-rbd-secret created
service/csi-metrics-rbdplugin created
service/csi-rbdplugin-provisioner created
persistentvolumeclaim/rbd-pvc created
deployment.apps/csi-rbdplugin-provisioner created
daemonset.apps/csi-rbdplugin created
```

Note the `persistentvolumeclaim/rbd-pvc` is to test that your configuration is
correct. You can remove this after it's generated.

## Overlays

You should provide the following in `overlays/`:

* [`csi-rbd-userkey.secret`](https://docs.ceph.com/en/latest/rbd/rbd-kubernetes/#setup-ceph-client-authentication)
  * you only need to provide the raw `key` value
  * ensure no trailing newline in the secret
* [`ceph-csi-config.json`](https://docs.ceph.com/en/latest/rbd/rbd-kubernetes/#generate-ceph-csi-configmap)
  * you only need the JSON content
