# Security policy

## Supported versions

Only the latest release tag receives fixes. Security fixes ship as a new version; published tags are never moved.

## Reporting a vulnerability

Please report vulnerabilities **privately**, using GitHub's
[private vulnerability reporting](https://github.com/edtbl76/grkit/security/advisories/new) for this repository.
Don't open a public issue.

Include what you found, how to reproduce it, and what you think the impact is. You'll get an acknowledgement
within a few days, and a fix or a decision as soon as one is ready. You'll be credited in the advisory unless you
ask not to be.

## Scope

grkit is a client library and a project template; it doesn't run guard models itself. Things we especially want to
hear about:

- a way to make `GuardClient` treat a failure as a successful **block or allow decision** it didn't receive, or to
  make a fail-open go uncounted;
- a way for a caller-supplied value to be treated as a trusted `actor`;
- a template guard that can exit `0` without having checked anything;
- anything that makes rendering the template execute untrusted code beyond what Copier documents.
