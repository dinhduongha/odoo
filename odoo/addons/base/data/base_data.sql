-------------------------------------------------------------------------
-- Pure SQL
-------------------------------------------------------------------------

-------------------------------------------------------------------------
-- UUIDv7 primary keys
--
-- PostgreSQL has no built-in max()/min() aggregate for the uuid type.
-- Define them here with a sort operator (sortop) so that the planner can
-- still satisfy max(id)/min(id) with the primary-key btree index
-- (Index Scan Backward) instead of falling back to a sequential scan or
-- an index-defeating max(id::text) cast.
-------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION _uuid_larger(uuid, uuid) RETURNS uuid
    LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT CASE WHEN $1 IS NULL THEN $2 WHEN $2 IS NULL THEN $1 WHEN $1 > $2 THEN $1 ELSE $2 END $$;

CREATE OR REPLACE FUNCTION _uuid_smaller(uuid, uuid) RETURNS uuid
    LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT CASE WHEN $1 IS NULL THEN $2 WHEN $2 IS NULL THEN $1 WHEN $1 < $2 THEN $1 ELSE $2 END $$;

DROP AGGREGATE IF EXISTS max(uuid);
DROP AGGREGATE IF EXISTS min(uuid);

CREATE AGGREGATE max(uuid) (
    sfunc = _uuid_larger, stype = uuid, combinefunc = _uuid_larger,
    parallel = safe, sortop = OPERATOR(>)
);
CREATE AGGREGATE min(uuid) (
    sfunc = _uuid_smaller, stype = uuid, combinefunc = _uuid_smaller,
    parallel = safe, sortop = OPERATOR(<)
);

CREATE TABLE ir_actions (
  id uuid NOT NULL DEFAULT uuidv7(),
  primary key(id)
);
CREATE TABLE ir_act_window (primary key(id)) INHERITS (ir_actions);
CREATE TABLE ir_act_report_xml (primary key(id)) INHERITS (ir_actions);
CREATE TABLE ir_act_url (primary key(id)) INHERITS (ir_actions);
CREATE TABLE ir_act_server (primary key(id)) INHERITS (ir_actions);
CREATE TABLE ir_act_client (primary key(id)) INHERITS (ir_actions);

CREATE TABLE res_users (
    id uuid NOT NULL DEFAULT uuidv7(),
    -- No FK references below, will be added later by ORM
    -- (when the destination rows exist)
    company_id uuid, -- references res_company,
    partner_id uuid, -- references res_partner,
    active boolean default True,
    create_date timestamp without time zone,
    login varchar(64) NOT NULL UNIQUE,
    password varchar default null,
    primary key(id)
);

CREATE TABLE res_groups (
    id uuid NOT NULL DEFAULT uuidv7(),
    name jsonb NOT NULL,
    primary key(id)
);

CREATE TABLE ir_module_category (
    id uuid NOT NULL DEFAULT uuidv7(),
    create_uid uuid, -- references res_users on delete set null,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    write_uid uuid, -- references res_users on delete set null,
    parent_id uuid REFERENCES ir_module_category ON DELETE SET NULL,
    name jsonb NOT NULL,
    primary key(id)
);

CREATE TABLE ir_module_module (
    id uuid NOT NULL DEFAULT uuidv7(),
    create_uid uuid, -- references res_users on delete set null,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    write_uid uuid, -- references res_users on delete set null,
    website character varying,
    summary jsonb,
    name character varying NOT NULL,
    author character varying,
    icon varchar,
    state character varying(16),
    latest_version character varying,
    shortdesc jsonb,
    category_id uuid REFERENCES ir_module_category ON DELETE SET NULL,
    description jsonb,
    application boolean default False,
    demo boolean default False,
    web boolean DEFAULT FALSE,
    license character varying(32),
    sequence integer DEFAULT 100,
    auto_install boolean default False,
    to_buy boolean default False,
    primary key(id)
);

CREATE TABLE ir_module_module_dependency (
    id uuid NOT NULL DEFAULT uuidv7(),
    name character varying,
    module_id uuid REFERENCES ir_module_module ON DELETE cascade,
    auto_install_required boolean DEFAULT true,
    primary key(id)
);

CREATE TABLE ir_model_data (
    id uuid NOT NULL DEFAULT uuidv7(),
    create_uid uuid,
    create_date timestamp without time zone DEFAULT (now() at time zone 'UTC'),
    write_date timestamp without time zone DEFAULT (now() at time zone 'UTC'),
    write_uid uuid,
    res_id uuid,
    noupdate boolean DEFAULT False,
    name varchar NOT NULL,
    module varchar NOT NULL,
    model varchar NOT NULL,
    primary key(id)
);

CREATE TABLE res_currency (
    id uuid NOT NULL DEFAULT uuidv7(),
    name varchar NOT NULL,
    symbol varchar NOT NULL,
    primary key(id)
);

CREATE TABLE res_company (
    id uuid NOT NULL DEFAULT uuidv7(),
    name varchar NOT NULL,
    partner_id uuid,
    currency_id uuid,
    sequence integer,
    create_date timestamp without time zone,
    primary key(id)
);

CREATE TABLE res_partner (
    id uuid NOT NULL DEFAULT uuidv7(),
    company_id uuid,
    create_date timestamp without time zone,
    name varchar,
    primary key(id)
);


---------------------------------
-- Default data
---------------------------------
insert into res_currency (id, name, symbol) VALUES ('00000000-0000-0000-0000-000000000001', 'USD', '$');
insert into ir_model_data (name, module, model, noupdate, res_id) VALUES ('USD', 'base', 'res.currency', true, '00000000-0000-0000-0000-000000000001');
-- select setval('res_currency_id_seq', 1);

insert into res_company (id, name, partner_id, currency_id, create_date) VALUES ('00000000-0000-0000-0000-000000000001', 'My Company', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', now() at time zone 'UTC');
insert into ir_model_data (name, module, model, noupdate, res_id) VALUES ('main_company', 'base', 'res.company', true, '00000000-0000-0000-0000-000000000001');
-- select setval('res_company_id_seq', 1);

insert into res_partner (id, name, company_id, create_date) VALUES ('00000000-0000-0000-0000-000000000001', 'My Company', '00000000-0000-0000-0000-000000000001', now() at time zone 'UTC');
insert into ir_model_data (name, module, model, noupdate, res_id) VALUES ('main_partner', 'base', 'res.partner', true, '00000000-0000-0000-0000-000000000001');
-- select setval('res_partner_id_seq', 1);

-- Demo Company (force multi-company baseline): always present as the 2nd company,
-- pinned to ...0002. Demo data is loaded into this company (see modules/loading.py).
insert into res_company (id, name, partner_id, currency_id, create_date) VALUES ('00000000-0000-0000-0000-000000000002', 'Demo Company', '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', now() at time zone 'UTC');
insert into ir_model_data (name, module, model, noupdate, res_id) VALUES ('demo_company', 'base', 'res.company', true, '00000000-0000-0000-0000-000000000002');
insert into res_partner (id, name, company_id, create_date) VALUES ('00000000-0000-0000-0000-000000000002', 'Demo Company', '00000000-0000-0000-0000-000000000002', now() at time zone 'UTC');
insert into ir_model_data (name, module, model, noupdate, res_id) VALUES ('demo_partner', 'base', 'res.partner', true, '00000000-0000-0000-0000-000000000002');

insert into res_users (id, login, password, active, partner_id, company_id, create_date) VALUES ('00000000-0000-0000-0000-000000000001', '__system__', NULL, false, '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', now() at time zone 'UTC');
insert into ir_model_data (name, module, model, noupdate, res_id) VALUES ('user_root', 'base', 'res.users', true, '00000000-0000-0000-0000-000000000001');
-- select setval('res_users_id_seq', 1);

insert into res_groups (id, name) VALUES ('00000000-0000-0000-0000-000000000001', '{"en_US": "Employee"}');
insert into ir_model_data (name, module, model, noupdate, res_id) VALUES ('group_user', 'base', 'res.groups', true, '00000000-0000-0000-0000-000000000001');
-- select setval('res_groups_id_seq', 1);
