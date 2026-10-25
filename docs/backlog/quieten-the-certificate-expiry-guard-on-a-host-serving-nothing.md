---
kind: change
waits_on: []
design_with: []
recorded_by: "the operator"
re_checked: 2026-10-19
---

`CertificateExpiryNotObserved` (`absent(traefik_tls_certs_not_after{cn!=""}) or count(...{cn=""}) > 0`, from `alert-on-certificate-expiry`) fires on any host that holds no certificate because nothing is routed yet, and reaches Slack. Staging did so from 2026-09-13 until an application first reached it on 2026-09-16. Every new or rebuilt host built from `docs/bootstrap-a-new-host.md` meets it between stage 7 and stage 8, so its first alert is noise; staging was rebuilt again on 2026-10-18.

Must not: suppress it wherever no certificate exists, which also silences the case it exists for, a Traefik that served certificates and now serves none. A fix needs a series saying the host is *meant* to serve one (a router count or a per-stack expectation).

- **Kind**: It needs that expectation's design and owes a delta to the certificate-expiry alerting requirement in `iac-platform-services`.
- **Recorded by**: the operator and a session on 2026-09-15, from the staging host; not by a change.
