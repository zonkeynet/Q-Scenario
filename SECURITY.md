# Security review and disclosure

Do not open a public issue containing credentials, private contact data or exploitable details about a live deployment. Use the Q-P1NG maintainer contact in the application for a private report.

Submission validation checks structure, bounds, disabled defaults, hashes and allowable paths. It does **not** decide that a script is benign. Treat every proposed action as untrusted. Review network destinations, command construction, parameter escaping, filesystem paths, permissions, data retention, resource limits and destructive operations. Test with synthetic data in an isolated profile.

Never execute issue code in privileged GitHub Actions jobs. Never interpolate issue titles/bodies into shell commands. Do not checkout a submission branch with a write token or access to secrets. The submission workflow only reads trusted default-branch Python and serializes proposed JSON into a draft PR.

The catalog has HTTPS transport and per-package SHA-256 consistency checks, not a separate signed trust root. A malicious repository administrator can replace both. Import does not grant execution rights; app review is still required. For stronger publisher authentication, add offline-signed catalog releases with pinned public keys and a documented key-rotation process before claiming independent signature verification.
