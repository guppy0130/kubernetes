# metallb

```sh
helm repo add metallb https://metallb.github.io/metallb
k apply -f namespace.yml
helm install --namespace metallb-system metallb metallb/metallb
```
