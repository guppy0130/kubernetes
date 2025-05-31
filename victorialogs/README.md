# victorialogs

```shell
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo update
helm show values vm/victoria-logs-single > chicago/values.yml
helm --kube-context chicago install vls vm/victoria-logs-single -f chicago/values.yml -n metrics
helm --kube-context chicago upgrade vls vm/victoria-logs-single -f chicago/values.yml -n metrics
```
