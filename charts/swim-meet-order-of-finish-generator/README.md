# Helm Chart

This chart deploys the web app, service, ingress, and the ACME helper resources needed to obtain and renew the ingress TLS certificate.

## Development Defaults

For a sample development deployment, use `values-development.yaml`.

It sets:

- release resource names to `oof`
- ingress name to `oof`
- nginx basic auth annotations referencing Secret `basic-auth`
- ACME webroot PVC storage class to `nfs-client-vast`

## Values To Set

At minimum, set:

- `ingress.userDomains`
- `tlsAcme.email`
- `tlsAcme.kubeconfig.secretName`

If your cluster needs a specific storage class for the ACME webroot PVC, also set:

- `tlsAcme.webServer.storageClassName`

If you enable ingress basic auth, create the referenced htpasswd Secret in the target namespace before installing or upgrading.

## Example

```bash
helm upgrade --install oof <chart-dir> \
  --namespace oof \
  -f values-development.yaml \
  --set tlsAcme.email=<ACME_EMAIL> \
  --set tlsAcme.kubeconfig.secretName=kubeconfig
```

Set your ingress host explicitly in your own values file or with `--set ingress.userDomains[0]=app.placeholder.invalid`.
