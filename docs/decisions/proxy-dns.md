# Fixed-source proxy DNS fallback

17 November 2026. The published cloud policy permits the two Greenhouse hosts. Fresh HTTPS clients work through the inherited proxy, while socket.getaddrinfo fails for both public hosts. The app previously rejected legitimate requests before its HTTP client reached that proxy.

When local DNS raises OSError, allow only exact boards-api.greenhouse.io or job-boards.greenhouse.io URLs over HTTPS with an inherited HTTPS proxy to use proxy-side DNS. Keep TLS verification, source host approval, standard-port checks, robots rules, no redirects and response/rate limits. A DNS response containing private/non-global addresses is still rejected; arbitrary hosts and literal private IPs never get this fallback. This is deliberately not a general proxy trust setting.

Unit checks cover allowed fixed HTTPS sources, denied HTTP/arbitrary/private addresses, private DNS results and absence of a proxy. The normal app fetcher then successfully fetched a Graphcore page and the worker imported/re-imported a Monzo board in disposable storage. No environment policy or private configuration was changed to achieve those checks.
