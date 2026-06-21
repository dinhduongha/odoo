# UUIDv7 Port — Handoff

For next engineer / external review (Antigravity, codex). Pairs with `TODO.md`.

## SESSION RESULTS (branch `uuid-19`, rebased onto 19.0 `a5e0f8710`)

**Status: LOGIN + web client + core ORM WORK.** Verified on a fresh DB
(`-i base,web,mail,contacts`, no demo) via curl:
- login POST → 303 → `/odoo` + session cookie; `get_session_info` OK (uuid uid).
- `GET /odoo`, `GET /web` → 200.
- `call_kw` search_read / create / domain `('id','in',[uuid])` / `('company_id','=',uuid)` /
  name_search / read_group → all OK. `share` correct (admin/root False, portal/public True).

**9 fix commits on top of the rebased `base`/`addons`:**
1. `%d`/`int()` on uuid id/uid (format strings, convert.py many2one).
2. `max(uuid)`/`min(uuid)` aggregates with sortop (PK index kept; reverts id::text hacks).
3. **`Field.__get__` regression** — rewrite dropped the `elif self.compute:` branch, so
   non-stored computed fields returned empty (broke group implication → share=True → login). PRIMARY blocker.
4. JSON uuid keys — central `make_json_response` key-stringify, `hash_sign(default=str)`,
   view_group_hierarchy + session_info company keys.
5. parent_path `int()`→`uuid.UUID` (res.company blocked session_info; + stock, website_sale).
6. mail/discuss — alias COALESCE nil-uuid, activity res_id, `new_message_separator`
   Integer→Uuid (`>` not `>=id+1`), stray debug log in ir_model.
7. **domain m2o uuid** — relational optimizer treated uuid-string values as display_names →
   `('m2o','=',uuid)` matched 0. Now uuid-strings compared as ids (domains.py).
   + xmlid COPY `%d`→`%s` (models.py).

**How to repro/serve the test DB:**
```
docker compose -f /home/ha/work/odoo-uuidv7-refactor/docker-compose.yml up -d db
# init core:
docker compose run --rm --no-deps --entrypoint bash odoo-uuid -lc \
 "printf '[options]\nadmin_passwd=admin\n' > /tmp/t.conf && odoo -c /tmp/t.conf -d uuidtest \
  -i base,web,mail,contacts --db_host=db --db_user=odoo --db_password=h17S0IhPvYQEN12T \
  --without-demo=all --stop-after-init"
# serve (port 18069): same run cmd without -i/--stop-after-init, add --http-port=8069 --service-ports
```
A minimal inline config is used to avoid the 40-module `etc/odoo.conf init=` list.

**Remaining (see TODO.md):** discuss unread-separator JS side; FULL module install
(l10n/pos/account likely have more uuid issues — run `./run.sh`); browser UI smoke;
deeper `osv/expression.py` is untouched by the migration and delegates to the Domain engine.

---


## Goal
Convert Odoo 19 primary keys (`id`) and all FKs from integer SERIAL → `uuid` (uuidv7).
Finish core/base/web port, fix login. Rebase onto latest 19.0 first.

## Repo state
- Git root: `/home/ha/work/odoo-uuidv7-refactor/odoo` (branch `uuid`).
- Fork base: `c0d524aebea4baf7738230365bfc752b8cc10afc` (Nov 2025).
- 19.0 tip: `a5e0f8710a95c4bb0b7cef07b4ab1e25cee846a2` (Jun 2026, +5364 commits).
- `uuid` = 2 commits on fork: `5428aef08 base`, `d4909226e addons`. Hand-edited.
- Transformer scripts in `/home/ha/work/odoo-uuidv7-refactor/refactor/*.py` are the
  HISTORICAL/experimental origin (many draft versions) — NOT source of truth now. Fix the
  committed tree by hand.

## Runtime
- Refactor compose: `/home/ha/work/odoo-uuidv7-refactor/docker-compose.yml`
  service `odoo-uuid` (image odoo:19, mounts `./odoo/{odoo,addons}` over image), db postgres:18.
  Web 18069, livechat 18072, db host port 5431. admin_passwd in `etc/odoo.conf`.
- `run.sh` = wipe `data/postgresql` + `data/odoo19`, then `docker compose up --build
  --force-recreate`. Installs module list from `etc/odoo.conf [options] init=`.
- `dev_mode=reload` on → python edits hot-reload; no rebuild for code-only.
- NOTE: running container `odoo19-odoo19-1` is a SEPARATE stock instance — not this.

## UUID mechanism (verified correct)
| Piece | Location |
|---|---|
| `Uuid` field, col `('uuid','uuid')`, default `uuid7()` | `odoo/orm/fields_uuid.py` (NEW) |
| `uuid7()`/`to_uuid()`/`is_uuid()` | `odoo/tools/uuid_utils.py` (NEW) |
| `Id` field col int4→uuid | `odoo/orm/fields_misc.py` |
| `Many2one._column_type` int4→uuid; m2m rel tables UUID | `odoo/orm/fields_relational.py:242,1444` |
| New-table DDL `id UUID NOT NULL DEFAULT uuidv7()` | `odoo/tools/sql.py:279` |
| Bootstrap rows fixed UUIDs, FK cols uuid | `odoo/addons/base/data/base_data.sql` |
| `SUPERUSER_ID = UUID('…0001')` | `odoo/orm/utils.py:22` |
| `psycopg2.extras.register_uuid()` | `odoo/modules/db.py:27` |
| cache seq int→uuid; `max(id)`→`ORDER BY id DESC LIMIT 1` | `odoo/orm/registry.py` |
| session uid str (json default=str) → reparsed to UUID | `odoo/http.py`; `Environment.__new__`; `browse()` |

PG18 native `uuidv7()` confirmed (`SELECT uuidv7()` returns valid v7). Hard dependency.

## Known bugs to fix (static review)
### A. `%d` format on UUID id/uid → TypeError
`odoo/tools/convert.py:346` · `odoo/addons/base/wizard/base_partner_merge.py:238,240` ·
`odoo/addons/base/models/res_users.py:986` · `…/res_device.py:188` ·
`…/ir_module.py:492,670` · `addons/web/controllers/export.py:613-614` · `odoo/orm/models.py:772`.
Fix `%d`→`%s`; Reference values `"%s,%s" % (model, rec.id)`. Then repo-wide sweep
`grep -rnE '#%d|,%d|%\(id\)d'`.

### B. Unguarded `uuid.UUID()` parse → ValueError
`odoo/orm/domains.py:1790` · `odoo/orm/models.py:5239`. Mirror guarded pattern at
`odoo/orm/models.py:299-315`.

### C. `int()` on UUID value
`odoo/tools/convert.py:472` `int(f_val)` for many2one eval — uuid-aware coerce.

### D. Cleanup / latent
`odoo/orm/fields_uuid.py:86` `_logger` undefined (NameError) — add logger; strip dead
commented blocks. `odoo/orm/fields_misc.py:140,152` duplicate `Id.convert_to_column` —
consolidate. `odoo/addons/base/models/ir_model.py:2223,2236` return-type hints int→UUID.

## Login status
Auth path static-clean (uid str→UUID reparse works). Failure is live-only; user left
`[UUID DEBUG]` logs in `addons/web/controllers/home.py`. Repro via `run.sh`, read live
traceback after credentials accept (suspect a `%d`/int() in post-auth `/web` render or
`session_info`). Remove debug logs once fixed.

## Review focus for Antigravity/codex
1. Rebase correctness — no uuid hunk dropped; conflicts resolved toward 19.0 + uuid semantics.
2. Any remaining int assumptions on id/uid (format strings, `int()`, `::int4` casts, `max(id)`).
3. FK integrity: every relational column emitted as `uuid` in new-table DDL + m2m tables.
4. Domain/SQL leaf handling for `('id','in',[…])`, `parent_of`, `child_of` with uuid parent_path.
5. xmlid → uuid resolution determinism in `odoo/tools/convert.py` (module data load).
