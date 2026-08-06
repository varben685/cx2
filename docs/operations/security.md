# Security

## Alapelvek

- `.env` nem kerülhet commitba.
- Webhook payload nem tartalmazhat API-kulcsot vagy jelszót.
- Valódi exchange order execution nincs az MVP-ben.
- Hibás payloadot biztonságosan, titkok kiszivárgása nélkül kell naplózni.

