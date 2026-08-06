# Backend

A backend FastAPI alkalmazás. Az induló szerkezet:

- `api`: HTTP route-ok.
- `application`: use case-ek.
- `domain`: tiszta üzleti logika.
- `infrastructure`: adatbázis és adapterek.
- `analytics`: mutatók.
- `ml`: baseline modellek.

Az első működő végpontok:

- `GET /health`
- `GET /ready`

