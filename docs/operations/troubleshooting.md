# Troubleshooting

## Backend nem érhető el

- Ellenőrizd: `docker compose ps`.
- Próbáld: `curl http://localhost:8000/health`.
- Nézd meg: `docker compose logs api`.

## Frontend nem mutat státuszt

- Ellenőrizd a `VITE_API_BASE_URL` értékét.
- Próbáld közvetlenül megnyitni a backend `/health` végpontját.

