## Why not store the JWT in localStorage?

localStorage is readable by any JavaScript running on the page — including
injected JavaScript from a successful XSS attack. If an attacker gets even
one script tag to execute (an unescaped user input rendered into the DOM,
a compromised third-party script, a vulnerable dependency), that script can
simply read `localStorage.getItem('token')` and exfiltrate it. There is no
browser-level protection stopping same-origin JS from reading it — that's
the whole point of localStorage, and it's exactly what makes it dangerous
for secrets.

### Alternatives, and their trade-offs

- **In-memory (React state / module variable)** — what this app does. The
  token exists only in JS memory, never touches disk, and disappears on
  page reload. Immune to localStorage-reading XSS specifically, but a
  running XSS payload can still read it from memory while the page is
  open — in-memory storage reduces exposure, it doesn't eliminate it.
  Cost: the user has to log in again on every page refresh.
- **httpOnly cookie, set by the server** — the browser stores it, but
  JavaScript cannot read it at all (that's what `httpOnly` means), so an
  XSS payload can't exfiltrate it directly. This is the strongest
  protection against token theft via XSS. Trade-off: the server has to
  set/manage the cookie, and you need CSRF protection instead, since
  cookies are sent automatically on every request to the origin
  (including ones a malicious site could trigger).
- **sessionStorage** — same readability problem as localStorage (any
  same-origin JS can read it); the only difference is it clears when the
  tab closes rather than persisting. Not meaningfully safer against XSS.

This app uses in-memory storage for now, accepting "re-login on refresh"
as the cost, rather than persisting the token anywhere XSS could read it
at rest.

