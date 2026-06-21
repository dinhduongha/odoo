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

## FULL MODULE INSTALL — ✅ DONE (217/217, EXIT 0, --without-demo)
All 217 modules of the etc/odoo.conf list (+deps=220) install clean on db `uuidfull`.
Verified serving: login→303 /odoo, session_info (uuid uid, company …0001), GET /odoo→200.
Got here via ~30 more fix commits past the login work (see git log). The single
highest-leverage one: Integer column_type was int8→reverted to int4 (unblocked ~19
modules at once). Other classes: ir.default json uuid keys/values, create_column int4→uuid,
domain/code/xpath id quoting, -id negations in SQL views, mail.followers UNION NULL,
purchase.bill.union, chart_template uuid xml_id, account journal alias_defaults.

### Still TODO for install
- **Install WITH demo** (`--without-demo` was used). Demo data will surface more uuid
  issues (and ties into the Demo Company work below). Run without `--without-demo=all`.

## FULL MODULE INSTALL (historical — superseded above)
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

## MULTI-COMPANY FORCING (after full install — user decisions 2026-06-21)
1. Force multi-company = on DB init auto-create a 2nd company + grant base.group_multi_company
   to internal users (so multi-company UI always shows).
2. Demo data → a dedicated "Demo Company" (main_company stays clean); load demo with that
   company as the active/default company.
3. Do AFTER uuid full install is stable.
4. PINNED company ids: main_company = '00000000-0000-0000-0000-000000000001'
   (already set via base_data.sql bootstrap line 155-156). Demo Company =
   '00000000-0000-0000-0000-000000000002' — ALSO pin in base_data.sql bootstrap
   (mirror main_company). Ready-to-add block (insert after the main_partner block,
   ~line 160; reuse currency …0001):
     insert into res_partner (id, name, company_id, create_date) VALUES ('00000000-0000-0000-0000-000000000002', 'Demo Company', '00000000-0000-0000-0000-000000000002', now() at time zone 'UTC');
     insert into ir_model_data (name, module, model, noupdate, res_id) VALUES ('demo_partner', 'base', 'res.partner', true, '00000000-0000-0000-0000-000000000002');
     insert into res_company (id, name, partner_id, currency_id, create_date) VALUES ('00000000-0000-0000-0000-000000000002', 'Demo Company', '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', now() at time zone 'UTC');
     insert into ir_model_data (name, module, model, noupdate, res_id) VALUES ('demo_company', 'base', 'res.company', true, '00000000-0000-0000-0000-000000000002');
   NOTE: a 2nd company always present = the "force multi-company" baseline. Deferred to
   the multi-company phase to avoid compounding single-company install failures now.
Implementation sketch: post_init hook (or base data) to create the 2nd/Demo company + add
group; for demo, load demo data under with_company(demo_company) / default_company_id context.
Also relevant: gen_company_id_backfill_sql.py for child company_id.

## NOT DONE / FOLLOW-UP
- **Controller `browse(int(url_param))` class (RUNTIME, not install-blocking)**: many web
  controllers cast a url/kwarg id with int() before browse — breaks on uuid at request
  time. Drop the int() (browse accepts str uuid). Sites: website_slides/controllers/main.py
  (many), website_blog, website_sale_loyalty, payment_stripe, website_event_booth_sale,
  html_editor (ir_ui_view, ir_qweb_fields), mass_mailing/controllers, website/website_form.
  Sweep: grep -rnE "browse\(int\(" addons (exclude real-int params like *_iterations/_limit).
- Python `-id` negations (runtime, not install-blocking): virtual-record dicts/sorts in
  hr_holidays/l10n_in_hr_holidays/mail ir_ui_menu/product_template/stock — `-uuid` will
  TypeError when hit; need a non-arithmetic unique-id / reverse-sort scheme.
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
