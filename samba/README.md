# samba

* <https://github.com/samba-in-kubernetes/samba-container>

not running operator, but some config examples:

* <https://github.com/samba-in-kubernetes/samba-operator/blob/ec7f4696aedc0076a52715e28a671fbec32b7d71/docs/howto.md>

## connect

`smb://[any cluster endpoint]:30001/`

* the loadbalancer uses the nodeport range, and we've mapped 445 -> 30001.
* it may make sense to configure smbd to 30001 in the container?
