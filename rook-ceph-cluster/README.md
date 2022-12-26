# rook-ceph-cluster

```sh
helm repo add rook-release https://charts.rook.io/release
helm install --create-namespace --namespace rook-ceph rook-ceph rook-release/rook-ceph
k label ns rook-ceph pod-security.kubernetes.io/enforce=privileged
helm pull rook-release/rook-ceph-cluster
tar -xvzf rook-ceph-cluster*.tgz
```

Then merge our `values.yaml` with the one from `rook-ceph-cluster`.

These `values` used `v1.10.8` of the chart.

```sh
helm upgrade --namespace rook-ceph -f values.yaml rook-ceph-cluster rook-release/rook-ceph-cluster
```
