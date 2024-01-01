# topolvm

pre-req: cert manager

```bash
helm repo add topolvm https://topolvm.github.io/tololvm
helm repo update
helm install --namespace topolvm-system -f values.yaml topolvm topolvm/topolvm
```

updating:

```bash
helm upgrade --namespace topolvm-system -f values.yaml topolvm topolvm/topolvm
```

* and then delete the existing pods so the new ones can take over
