create extension if not exists pgcrypto;

create table if not exists customers (
  id uuid primary key default gen_random_uuid(),
  phone text not null unique,
  name text not null,
  address text not null default '',
  lat numeric(10,8),
  lng numeric(11,8),
  created_at timestamptz not null default now()
);

create table if not exists workers (
  id uuid primary key default gen_random_uuid(),
  phone text not null unique,
  name text not null,
  service_type text not null,
  rating numeric(3,2) not null default 4.80 check (rating >= 0 and rating <= 5),
  is_verified boolean not null default false,
  is_flagged boolean not null default false,
  flag_reason text,
  current_lat numeric(10,8),
  current_lng numeric(11,8),
  created_at timestamptz not null default now()
);

create table if not exists pricing_config (
  id uuid primary key default gen_random_uuid(),
  service_type text not null unique,
  base_price numeric(10,2) not null,
  per_km_rate numeric(10,2) not null default 5.00,
  floor_price numeric(10,2),
  ceiling_price numeric(10,2),
  updated_at timestamptz not null default now()
);

create table if not exists tasks (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references customers(id) on delete cascade,
  worker_id uuid references workers(id) on delete set null,
  service_type text not null,
  status text not null default 'created' check (status in ('created', 'assigned', 'accepted', 'in_progress', 'completed', 'cancelled')),
  description text not null,
  price numeric(10,2) not null default 0,
  urgency numeric(3,2) not null default 1.00 check (urgency >= 1.00 and urgency <= 1.50),
  is_flagged boolean not null default false,
  flag_reason text,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists tracking (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references tasks(id) on delete cascade,
  worker_id uuid not null references workers(id) on delete cascade,
  lat numeric(10,8),
  lng numeric(11,8),
  event_type text not null,
  timestamp timestamptz not null default now()
);

create table if not exists payouts (
  id uuid primary key default gen_random_uuid(),
  worker_id uuid not null references workers(id) on delete cascade,
  task_id uuid not null references tasks(id) on delete cascade,
  amount numeric(10,2) not null,
  split_type text not null check (split_type in ('immediate', 'verification')),
  status text not null default 'pending' check (status in ('pending', 'released', 'failed')),
  is_flagged boolean not null default false,
  flag_reason text,
  released_at timestamptz
);

create table if not exists reviews (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references tasks(id) on delete cascade,
  customer_id uuid not null references customers(id) on delete cascade,
  worker_id uuid not null references workers(id) on delete cascade,
  rating integer not null check (rating between 1 and 5),
  comment text,
  is_flagged boolean not null default false,
  flag_reason text,
  created_at timestamptz not null default now()
);

create table if not exists whatsapp_messages (
  id uuid primary key default gen_random_uuid(),
  phone text not null,
  direction text not null check (direction in ('in', 'out')),
  message_type text not null,
  content text not null,
  task_id uuid references tasks(id) on delete set null,
  timestamp timestamptz not null default now()
);
