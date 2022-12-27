# homebridge

* <https://github.com/homebridge/homebridge/wiki/Install-Homebridge-on-Docker>
* <https://www.devwithimagination.com/2020/02/02/running-homebridge-on-docker-without-host-network-mode/>
* <https://github.com/oznu/docker-homebridge/issues/437>

## Notes

* username/password defaults to `admin/admin` so we can skip first-time setup
* not super sure how that `NodePort` is working, because it's definitely still
  publishing on 5353 despite supposedly being allocated to a random port...

## Shortcomings

* MAC address is a lie (unsure if this matters)
