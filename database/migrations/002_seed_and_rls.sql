-- Strategic indexes
create index if not exists idx_customers_phone on customers(phone);
create index if not exists idx_workers_phone on workers(phone);
create index if not exists idx_workers_service_type on workers(service_type);
create index if not exists idx_workers_verified_rating on workers(is_verified, rating desc);
create index if not exists idx_tasks_customer_status on tasks(customer_id, status);
create index if not exists idx_tasks_worker_status on tasks(worker_id, status);
create index if not exists idx_tasks_service_status on tasks(service_type, status);
create index if not exists idx_tracking_task_timestamp on tracking(task_id, timestamp desc);
create index if not exists idx_tracking_worker_timestamp on tracking(worker_id, timestamp desc);
create index if not exists idx_payouts_worker_status on payouts(worker_id, status);

-- Row level security
alter table customers enable row level security;
alter table workers enable row level security;
alter table tasks enable row level security;
alter table tracking enable row level security;
alter table payouts enable row level security;
alter table reviews enable row level security;
alter table pricing_config enable row level security;
alter table whatsapp_messages enable row level security;

-- Customers
drop policy if exists customers_select_own on customers;
create policy customers_select_own on customers
  for select using (auth.uid()::text = id::text or auth.role() = 'service_role');

drop policy if exists customers_insert_authenticated on customers;
create policy customers_insert_authenticated on customers
  for insert with check (auth.role() = 'authenticated' or auth.role() = 'service_role');

drop policy if exists customers_update_own on customers;
create policy customers_update_own on customers
  for update using (auth.uid()::text = id::text or auth.role() = 'service_role');

-- Workers
drop policy if exists workers_select_verified_or_own on workers;
create policy workers_select_verified_or_own on workers
  for select using (is_verified = true or auth.uid()::text = id::text or auth.role() = 'service_role');

drop policy if exists workers_insert_authenticated on workers;
create policy workers_insert_authenticated on workers
  for insert with check (auth.role() = 'authenticated' or auth.role() = 'service_role');

drop policy if exists workers_update_own on workers;
create policy workers_update_own on workers
  for update using (auth.uid()::text = id::text or auth.role() = 'service_role');

-- Tasks
drop policy if exists tasks_select_customer_or_worker on tasks;
create policy tasks_select_customer_or_worker on tasks
  for select using (
    auth.uid()::text = customer_id::text
    or auth.uid()::text = worker_id::text
    or auth.role() = 'service_role'
  );

drop policy if exists tasks_insert_customer on tasks;
create policy tasks_insert_customer on tasks
  for insert with check (auth.role() = 'authenticated' or auth.role() = 'service_role');

drop policy if exists tasks_update_customer_or_worker on tasks;
create policy tasks_update_customer_or_worker on tasks
  for update using (
    auth.uid()::text = customer_id::text
    or auth.uid()::text = worker_id::text
    or auth.role() = 'service_role'
  );

-- Tracking
drop policy if exists tracking_select_related on tracking;
create policy tracking_select_related on tracking
  for select using (
    auth.role() = 'service_role'
    or auth.uid()::text in (
      select customer_id::text from tasks where tasks.id = tracking.task_id
    )
    or auth.uid()::text = worker_id::text
  );

drop policy if exists tracking_insert_related on tracking;
create policy tracking_insert_related on tracking
  for insert with check (
    auth.role() = 'service_role'
    or auth.uid()::text = worker_id::text
  );

-- Payouts
drop policy if exists payouts_select_worker_or_service on payouts;
create policy payouts_select_worker_or_service on payouts
  for select using (
    auth.role() = 'service_role'
    or auth.uid()::text = worker_id::text
  );

drop policy if exists payouts_manage_service on payouts;
create policy payouts_manage_service on payouts
  for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

-- Reviews
drop policy if exists reviews_select_related on reviews;
create policy reviews_select_related on reviews
  for select using (
    auth.role() = 'service_role'
    or auth.uid()::text = customer_id::text
    or auth.uid()::text = worker_id::text
  );

drop policy if exists reviews_insert_customer on reviews;
create policy reviews_insert_customer on reviews
  for insert with check (
    auth.role() = 'service_role'
    or auth.uid()::text = customer_id::text
  );

-- Pricing config
drop policy if exists pricing_config_read_public on pricing_config;
create policy pricing_config_read_public on pricing_config
  for select using (true);

drop policy if exists pricing_config_manage_service on pricing_config;
create policy pricing_config_manage_service on pricing_config
  for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

-- WhatsApp messages
drop policy if exists whatsapp_messages_service_only on whatsapp_messages;
create policy whatsapp_messages_service_only on whatsapp_messages
  for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

-- Seed data
insert into pricing_config (service_type, base_price, per_km_rate)
values
  ('medicine', 120.00, 5.00),
  ('help', 150.00, 5.00),
  ('visit', 100.00, 5.00),
  ('cleaning', 200.00, 5.00),
  ('other', 130.00, 5.00)
on conflict (service_type) do update
set base_price = excluded.base_price,
    per_km_rate = excluded.per_km_rate,
    updated_at = now();

insert into customers (id, phone, name, address, lat, lng)
values
  ('00000000-0000-0000-0000-000000000001', '+919900000001', 'Asha Verma', '12 Lake View Road, Bengaluru', 12.97160000, 77.59460000),
  ('00000000-0000-0000-0000-000000000002', '+919900000002', 'Ramesh Iyer', '44 Palm Avenue, Chennai', 13.08270000, 80.27070000)
on conflict (id) do nothing;

insert into workers (id, phone, name, service_type, rating, is_verified, current_lat, current_lng)
values
  ('00000000-0000-0000-0000-000000000101', '+918800000101', 'Meena Sharma', 'medicine', 4.90, true, 12.97500000, 77.60000000),
  ('00000000-0000-0000-0000-000000000102', '+918800000102', 'Farhan Khan', 'help', 4.80, true, 12.98000000, 77.61000000),
  ('00000000-0000-0000-0000-000000000103', '+918800000103', 'Lakshmi Devi', 'cleaning', 4.70, false, 13.00000000, 80.25000000)
on conflict (id) do nothing;

insert into tasks (id, customer_id, worker_id, service_type, status, description, price, urgency, completed_at)
values
  ('00000000-0000-0000-0000-000000001001', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000101', 'medicine', 'in_progress', 'Morning medicine delivery', 180.00, 1.25, null),
  ('00000000-0000-0000-0000-000000001002', '00000000-0000-0000-0000-000000000002', null, 'help', 'created', 'Help with groceries and light support', 200.00, 1.00, null)
on conflict (id) do nothing;

insert into tracking (task_id, worker_id, lat, lng, event_type)
values
  ('00000000-0000-0000-0000-000000001001', '00000000-0000-0000-0000-000000000101', 12.97200000, 77.59500000, 'location_update')
on conflict do nothing;

insert into payouts (worker_id, task_id, amount, split_type, status, released_at)
values
  ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000001001', 135.00, 'immediate', 'released', now()),
  ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000001001', 45.00, 'verification', 'pending', null)
on conflict do nothing;

insert into reviews (task_id, customer_id, worker_id, rating, comment)
values
  ('00000000-0000-0000-0000-000000001001', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000101', 5, 'Punctual, polite, and careful.')
on conflict do nothing;

insert into whatsapp_messages (phone, direction, message_type, content, task_id)
values
  ('+919900000001', 'in', 'text', 'Need medicine delivered this morning', '00000000-0000-0000-0000-000000001001'),
  ('+919900000001', 'out', 'text', 'Your care request is confirmed and a worker is on the way.', '00000000-0000-0000-0000-000000001001')
on conflict do nothing;
