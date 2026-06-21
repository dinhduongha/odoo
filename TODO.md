# UUIDv7 Port — TODO

Branch `uuid`. Fork `c0d524a`. Target 19.0 tip `a5e0f8710`. DB postgres:18 (native `uuidv7()`).
Run dir: `/home/ha/work/odoo-uuidv7-refactor` (compose `odoo-uuid`, ports 18069/18072).
Auto mode. Code reviewed externally by Antigravity + codex.

## DONE
- [x] Scope branch diff: 123 files, +2495/-633, 2 commits (`base`,`addons`).
- [x] Map UUID core mechanism: `fields_uuid.py`, `uuid_utils.py`, `Id`/`Many2one` col→uuid,
      `sql.py:279` DDL default, `base_data.sql` bootstrap UUIDs, `SUPERUSER_ID=…0001`,
      `register_uuid()`, registry seq int→uuid, `max(id)`→`ORDER BY id DESC`.
- [x] Verify PG18 `uuidv7()` exists (`SELECT uuidv7()` OK).
- [x] Audit auth/login path: session uid str→UUID reparse OK; login *should* work statically.
- [x] Audit domain/SQL/commands: command sigs int→uuid OK; browse/to_record_ids OK.
- [x] Catalogue concrete bugs (see handoff.md tables A–D).
- [x] Measure 19.0 divergence: +5364 commits, 70 overlap files (28 core).
- [x] Plan approved; decisions: rebase-first, wipe+reinstall OK.

## DONE (this session — branch `uuid-19`, rebased onto 19.0 a5e0f8710)
### Phase 1 — Rebase ✓
- [x] `git rebase --onto a5e0f8710 c0d524a` → branch `uuid-19`. Resolved 5 core + 8 addon conflicts.
- [x] Core uuid mechanism verified intact post-rebase; core byte-compiles.

### Phase 2 — Bug fixes ✓ (commit `a41f181e1`)
- [x] A: `%d`→`%s` on id/uid (convert.py, ir_cron, ir_module, res_device, res_users,
      export.py, base_partner_merge, wizard_ir_model_menu_create).
- [x] C: `int(f_val)`→`to_uuid` (convert.py:472). D: fields_uuid `_logger`, dedup Id.convert_to_column.

### Phase 3 — Live login repro & fix ✓ (LOGIN WORKS)
Root-caused via fresh core init (base,web,mail,contacts) + curl. Fixes:
- [x] **Field.__get__ regression** (commit `fe300f074`): rewrite dropped `elif self.compute:`
      → non-stored computed fields returned empty → group implication broken → share=True
      for admin → notification_type constraint failed → login/registry load blocked. Restored
      stock branch logic. THE primary blocker.
- [x] JSON uuid keys (commit `b6c481250`): http.py make_json_response central key-stringify;
      hash_sign default=str; view_group_hierarchy + session_info company keys.
- [x] parent_path int()→uuid.UUID (commit `d7053ea63`): res.company (blocked session_info) + stock + website_sale.
- [x] mail/discuss (commit `47bc78275`): mail_alias COALESCE nil-uuid, mail_activity res_id,
      new_message_separator Integer→Uuid (`>` not `>=id+1`), ir_model stray debug log.
- [x] max/min(uuid) aggregates (commit `0c47bfb2a`): keep PK index instead of id::text cast.

### Phase 4 — Verify ✓
- [x] Core init base,web,mail,contacts → EXIT 0.
- [x] Login POST → 303 → /odoo + session cookie. session_info OK (uuid uid).
- [x] GET /odoo, /web → 200 (web client loads).
- [x] ORM via call_kw: search_read, domain `('id','in',[uuid])`, create (new uuid) → all OK.
- [x] share correct: __system__/admin=False, portal/public=True.

## FULL MODULE INSTALL (in progress — 69/217 modules)
Driving `-i base,web,sale,account,stock,mrp,hr,website,project,mail,... --without-demo`
to ground-truth addon-level uuid bugs. Fixed bug CLASSES (commits after `55028bf`):
- parent_path int()→uuid (analytic, ir_ui_menu, hr_department, +earlier).
- browse() accepts single int/False (legacy 0 sentinel).
- unique indexes: NULLS NOT DISTINCT (+ partial WHERE for mail_alias) instead of COALESCE(col,0).
- analytic.plan: project_plan nil-uuid sentinel; dynamic column name uses uuid hex.
- registry.init_models stray debug log guard.
- domain STRINGS interpolating ids: quote/str() (fleet, sale, gamification, hr_version, +data).
- generated code / alias_defaults: str() ids (lunch cron, account/project/crm/maintenance).
- fields.Uuid no longer auto-defaults uuid7() (was populating nullable refs → constraint fails).
- view xpath predicate id quoting; uuid-safe python domains in view strings (Field._description_domain).
- lunch report: drop -id negation (uuids globally unique).

### CURRENT BLOCKER (hr.employee_admin)
hr.employee.company_id inherits `related='resource_id.company_id'` + precompute from
resource.mixin; the precompute chain isn't resolving → company_id NULL → not-null
violation. Needs hands-on debugging on an hr-installed DB (related/precompute path).
Likely a CLASS (related+precompute company_id) — worth fixing centrally.

### Remaining
~148 modules unverified. Expect more addon-specific uuid issues past hr (website,
pos, l10n if added). Re-run: `cd /home/ha/work/odoo-uuidv7-refactor && ./run.sh` (full
config) or the minimal `-i <mods>` loop used this session (see handoff.md).

## NOT DONE / FOLLOW-UP
- [ ] **Discuss unread separator JS side**: backend now uses uuid `>`; web/owl client still
      assumes integer id arithmetic for `new_message_separator`. Needs matching JS change.
- [ ] **Full module install** (the 40-module `etc/odoo.conf` list) not yet run — only core.
      Expect more addon-level uuid issues (l10n, pos, account). Run `./run.sh` for full repro.
- [ ] **orm/domains.py + orm/ + osv deep review** (user request) — in progress.
- [ ] Browser/UI smoke (forms, global search, module install action) beyond curl.
- [ ] `\d res_partner` schema spot-check; optional `test_orm` suite.

## RISKS
- Rebase heavy: core ORM moved over 5364 commits; some hunks won't apply — re-locate.
- `uuidv7()` requires postgres:18 (hard dep).
- No int→uuid data migration; greenfield reinstall only.
