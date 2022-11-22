# tempo

* <https://grafana.com/docs/tempo/latest/configuration/>

Note the headless service, which allows service ports to be opened before the
deployment is "healthy". This is required because we'll try to connect to
ourselves via CoreDNS, which means the service has to be active.

Test that we're "ready" by checking the `/ready` endpoint inside the pod:

```sh
printf 'GET /ready HTTP/1.1\r\nHost: tempo:3200\r\n\r\n' | nc tempo 3200
```

* <https://github.com/grafana/tempo/pull/531>
* <https://github.com/grafana/tempo/issues/493>
* <https://reachmnadeem.wordpress.com/2021/01/30/distributed-tracing-using-grafana-tempo-jaeger-with-amazon-s3-as-backend-in-openshift-kubernetes/>
