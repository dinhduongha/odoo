# UUIDv7 Port — TODO

Branch `uuid`. Fork `c0d524a`. Target 19.0 tip `a5e0f8710`. DB postgres:18 (native `uuidv7()`).
Run dir: `/home/ha/work/odoo-uuidv7-refactor` (compose `odoo-uuid`, ports 18069/18072).
Auto mode. Code reviewed externally by Antigravity + codex.

## ⭐ MILESTONE — branch `uuid-19-swap` (SWAP ROLES) — 2026-06-21
Full all-module demo install: **227/227 modules, Registry loaded, EXIT 0, ZERO demo
failures** (every module's demo data loads). Runtime-verified: login + web client (/odoo,
/web = 200) + 4 companies switchable + demo data readable via web call_kw.
- test_orm suite (2026-06-21): PRODUCT (install/demo/runtime) green, but the TEST SUITE
  is not uuid-adapted. Run on uuid-19-swap:
  - test_orm module: ~53 unit-test failures (test_fields 16, test_onchange 12, test_search 9,
    test_one 9, …) before an HttpCase/tour test hung headless (no browser). Causes:
    29 AssertionError, 17 TypeError, 6 `uuid = integer`.
  - dep tests (base 977 tests: 19 fail/65 err; web 35: 4/11; …): dominated by `uuid = integer`
    — fixtures hardcode int ids (999999999, 146, etc.) and compare to ints.
  - These are mostly TEST-side int-id assumptions + a few likely real ORM edge cases; a
    separate large effort to uuid-adapt the suite. HttpCase/tour need a browser.
  - Run cmd: copy odoo/addons/test_orm into the container's /mnt/extra-addons (the
    odoo/addons mount shadows odoo/odoo/addons/test_orm), then
    `-i test_orm --test-enable --test-tags=/test_orm --http-port=8074 --stop-after-init`.
- PUSH deferred: only remote is origin=github.com/odoo/odoo.git (upstream); no fork remote.
- Final fixes that cleared the last failures:
  - `ir_sequence` standard-impl PG sequence names: `%03d % uuid` -> uuid hex (date-range
    sub keyed by its own id, <=63 char). Latent RUNTIME bug (order/invoice/picking numbering).
  - `pos_restaurant` last_order_preparation_change: json.dumps default=str (uuid ids).
  - `website_sale` recursion: get_param_id did int(False)==0 -> browse(0) phantom id-0
    pricelist whose _origin self-references (infinite currency_id recursion). Fixed
    get_param_id (uuid-aware, None when absent) + OriginIds only yields truthy ids.

- Built from `3327d6fce` (start of the abandoned option-2 "keep routing/fix check_company
  per-module") + cherry-picked GENERIC uuid fixes (QWeb, Json, mail tracking, reference-o2m,
  parse_res_ids, alias_defaults, website_visitor, analytic, survey domain, lunch/event/rating…)
  + **Swap roles**. No per-module check_company hacks.
- SWAP: `base.main_company` = ...0002 = PRIMARY = the demo company (demo loads into the
  loading user's company, so it lands here naturally — NO allowed_company_ids redirection,
  NO cross-company crossover). `base.your_company` = ...0001 = "Production Company", clean.
  Secondary clean company must NOT be named "YourCompany" (base demo renames the main/demo
  company to that; res_company has unique-name constraint).
- Verified: demo in primary company (33 account moves); Production Company clean (0).
- vs option-2 routing (branch `uuid-19-demo-routing`): swap removed the ENTIRE crossover
  class — hr_expense price, mrp seq fallback, pos suffix, website_sale/survey guards,
  models._check_company install_demo skip are all UNNEEDED.
- KNOWN remaining (1, caught/non-fatal): `website_sale` demo — NewId-origin + pricelist/group
  recursion on website_sale_order_9 (genuine uuid bug, only in full demo sequence; not
  crossover). pos_restaurant fixed (json default=str, 1cb22d425).
- Latent: `ir_sequence` %03d % seq.id at ~15 sites (standard impl) — uuid-unsafe PG seq names.

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

### Install WITH demo — ✅ DONE (217/217, EXIT 0)
Full install WITH demo data also succeeds clean (db `uuiddemo`) — no demo-specific
fixes were needed beyond the --without-demo set. Verified: login→/odoo 200, demo data
present (product.template count=10). So both install modes (with/without demo) pass.

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

## FULL ALL-MODULE DEMO INSTALL + Demo-Company routing — 🔄 IN PROGRESS (2026-06-21)
Goal (user): full all-module install with demo for ALL modules, all demo data in the
Demo Company (…0002, option 2 = keep allowed_company_ids routing + relax check_company),
rich supplemental demo where missing.
- Decision history: user picked role-swap (option 1), then switched to option 2 (keep
  routing, skip check). The swap was reverted; bootstrap stays main=…0001/demo=…0002.
- Systemic fix: `models._check_company` early-returns when `install_demo` in context, so
  demo records may reference shared/base data owned by the main company without crossover
  errors. (User note: company-scoped models legitimately reference company-less shared
  models — the framework already allows company_id=False; the skip covers the rest.)
- Demo-data uuid bugs fixed so far (commits e3981f5ff, 2046a4b9d):
  mail.tracking.value m2o uuid columns; Reference-in-o2m core (event/survey); event/
  marketing_card %i/%d reference evals; im_livechat user→partner ref; lunch cron uuid
  quote; rating soft-ref exists() guard; analytic project_plan param '1'→uuid; survey
  certification domain unquoted uuid.
- Module set: the etc/odoo.conf `init` list (~37 apps) + om_account_accountant. Custom
  addons copied into the serve container's /mnt/extra-addons.
- STATUS: iterating full installs (uuidfull_demo6) — crashes move forward each pass as
  per-module demo bugs are fixed.

## MULTI-COMPANY FORCING — ✅ IMPLEMENTED (2026-06-21)
- Demo Company bootstrapped in base_data.sql, pinned `…0002` (xmlid base.demo_company);
  main_company `…0001`. Always 2 companies present.
- group_multi_company implied_by group_user → every internal user gets the switcher.
- user_admin/user_root company_ids include both companies → can actually switch.
- load_demo runs with allowed_company_ids=[demo_company,…] → demo records that default
  their company land in Demo Company.
- Verified: install (no demo) + demo install both EXIT 0; admin.company_ids = both.

### Demo Company chart + warehouse — ✅ DONE
- account ir_module auto-install loads the chart for base.demo_company too; stock
  create_missing_warehouse covers every company. Verified: both companies have 7
  journals + 1 warehouse + chart_template=generic_coa; demo install EXIT 0.

### Account demo transactions — ✅ DONE
Demo install (`-i account --with-demo`) now loads accounting demo cleanly: EXIT 0,
56 posted moves (18 out_invoice / 4 in_invoice / refunds), 20 statement lines, across
YourCompany + the US demo company. Note Odoo 19 changed the flag: demo is OFF unless
`--with-demo` is passed. Root-cause chain fixed (each was a distinct uuid bug):
1. **odoo/orm/fields_relational.py `Many2many.convert_to_record_multi`** — did NOT
   coerce ids to uuid (the single `convert_to_record` and the m2o multi path do). So
   `recordset.x2many` over multiple records yielded **str** ids; field caches are keyed
   by `uuid.UUID` → key mismatch → spurious MissingError on a later field read. THE key
   fix; affects any multi-record m2m read, not just demo.
2. account/models/account_move.py — `BOOL(uuid)` (`has_payment`/`has_st_line`) →
   `<col> IS NOT NULL`. project_todo/res_users.py same `BOOL(project_id)`.
3. account/models/account_account.py — account-merge remap `value::int` / `(...)::int`
   on account ids → `::uuid` (5 sites).
4. account/models/chart_template.py `_install_demo` — pin `with_company(company)` +
   `allowed_company_ids=[company.id]` so the company's own taxes/accounts pass record
   rules during validation.
5. base/models/res_users.py create — derive `company_ids` from the record's own
   `company_id` (not env.company) so company_id ∈ company_ids when demo loads in the
   Demo-Company context (fixes user_demo ValidationError).
6. mail/demo `new_message_separator` — `eval="ref('x') + 1"` (UUID+1) → `ref="x"`.
7. mail/models/mail_thread.py + mail/tools/parser.py — `is_list_of(ids, int)` →
   `uuid.UUID` (message_notify partner/attachment ids; parse_res_ids).
8. account/models/account_bank_statement_line.py — `internal_index` `f'{id:0>10}'`
   (UUID has no format spec) → `id.hex` (uuidv7 hex is lexicographically time-sortable).

### Payment + reconciliation — ✅ VERIFIED
`-i account_payment --with-demo` → EXIT 0, no errors. Reconciliation proven
functionally (shell, real data): out_invoice residual 750 → `account.payment.register`
→ payment `state=paid` / `is_reconciled=True`; invoice residual 0.0,
`payment_state=paid`; 1 `account.partial.reconcile` created. `_compute_payment_state`
(the fixed `has_payment`/`has_st_line` BOOL_OR query) ran against the real partial row
and computed correctly. NOTE: stock account demo creates 0 payments by itself
(`_post_load_demo_data` only posts moves), so payments=0 after a plain demo install is
expected upstream behavior, not a uuid bug.

## CUSTOM ADDONS uuid conversion — ✅ DONE (om_account_accountant suite)
Installed clean with uuidv7 (56 modules incl deps, EXIT 0): om_account_accountant,
om_account_asset, om_account_budget, om_account_daily_reports, om_account_followup,
om_fiscal_year, om_recurring_payments, accounting_pdf_reports. Fixes:
- (core) translate._get_uid UnboundLocalError (broken uid.id block) — committed in odoo repo.
- om_data_remove: parameterize raw SQL (was company_id=%d / unquoted field_id=%s).
- om_hr_payroll_account: analytic_distribution dict key str(account_id).
- om_account_followup: synthetic followup_stat id partner_id*10000+company_id ->
  md5(partner_id::text||'-'||company_id::text)::uuid in the view + matching python helper.
The om SQL report views (asset/followup) work via the global max(uuid)/min(uuid) aggregates.
Custom-addons commits are in the custom-addons/odooapps git repo (separate from odoo repo).
Run: install with --addons-path=...,/path/to/custom-addons/odooapps -i om_account_accountant.
NOTE: followup-report *printing* (wizard) not runtime-tested, but the md5-uuid logic mirrors
the view exactly.

## (was) CUSTOM ADDONS uuid conversion (NEW task — custom-addons/odooapps om_account suite)
Convert om_account_accountant + related OM modules to uuidv7 (same bug classes as core:
%d/int() on ids, browse(int()), -id negations, ids in domain/code strings, json uuid
keys, COALESCE(id,0), create_column int4 FK, fields.Integer used as an id). Modules in
custom-addons/odooapps: om_account_accountant, om_account_asset, om_account_budget,
om_account_daily_reports, om_account_followup, om_fiscal_year, accounting_pdf_reports
(+ om_hr_payroll*, om_recurring_payments, om_data_remove). Not on the refactor compose
addons_path yet.

## (original notes) MULTI-COMPANY FORCING (after full install — user decisions 2026-06-21)
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
- **Controller int() on ids — ✅ DONE (RUNTIME class)**: removed ~188 int() casts on
  url/param record ids across controllers (browse(int()), domain leaves, write/create
  vals, context, URL f-strings, function args); survey question membership uses str(id).
  Word-boundary \bint\( to avoid constraint(/print(); skipped numeric/real-int params.
  Runtime-verified: /web/image/res.partner/<uuid>/avatar_128 -> 200 image/png, company
  logo -> 200, website / -> 200, /my -> 303. Commits in odoo repo.
- Python `-id` negations — ✅ DONE: sort keys use tools.Reverse(id) (product variant pick,
  stock.quant closest removal, stock.move.line, ir.ui.menu, res.partner main_user_id);
  virtual calendar records (hr_holidays public/mandatory days, l10n_in optional holidays)
  use a deterministic negative int from the uuid (owl popover tests id<0). Runtime-verified.
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
