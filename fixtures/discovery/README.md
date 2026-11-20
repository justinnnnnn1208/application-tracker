# Discovery adapter contract fixtures

lever-public-board.json is synthetic test data following the official Lever public postings API field contract. It is not a real vacancy, does not get seeded into the app, and must never count towards the genuine reviewed evaluation set in fixtures/eval. Tests exercise parser bounds, explicit dates, untrusted text, identity and manual worker integration without accessing application forms.

ashby-public-board.json is also synthetic. It tests explicitly listed-only intake, literal fields, published-date/partial-date handling, off-board URL rejection, owner-preserving dedupe and untrusted text. It does not represent a real Ashby posting or live verification.
