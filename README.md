# kubernetes configs

## Usage

Uses kustomize for deployment/management.

### Diff viewing

Assuming you have the following installed:

* `kubecolor` (aliased to `k`)
* `delta` (diff visualization)

```bash
k --plain diff -k . | delta --default-language=yml
```

[Source](https://github.com/hidetatz/kubecolor/issues/77).

### Apply/delete

```bash
k apply -k .
k delete -k .
```
