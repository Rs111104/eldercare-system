create or replace function calculate_task_price(
  p_service_type text,
  p_distance_km numeric,
  p_urgency numeric
) returns numeric language sql stable as $$
  select round((pc.base_price + (p_distance_km * pc.per_km_rate)) * p_urgency, 2)
  from pricing_config pc
  where pc.service_type = p_service_type
  limit 1;
$$;

create or replace function complete_task_and_create_payout(
  p_task_id uuid,
  p_amount numeric
) returns void language plpgsql as $$
declare
  v_worker_id uuid;
begin
  select worker_id into v_worker_id from tasks where id = p_task_id;

  update tasks
    set status = 'completed',
        completed_at = now(),
        price = p_amount
  where id = p_task_id;

  if v_worker_id is not null then
    insert into payouts (worker_id, task_id, amount, split_type, status, released_at)
    values
      (v_worker_id, p_task_id, round(p_amount * 0.75, 2), 'immediate', 'released', now()),
      (v_worker_id, p_task_id, round(p_amount * 0.25, 2), 'verification', 'pending', null);
  end if;
end;
$$;

create or replace function update_worker_location(
  p_worker_id uuid,
  p_lat numeric,
  p_lng numeric
) returns void language sql as $$
  update workers
    set current_lat = p_lat,
        current_lng = p_lng
  where id = p_worker_id;
$$;

create or replace function insert_whatsapp_message(
  p_phone text,
  p_direction text,
  p_message_type text,
  p_content text,
  p_task_id uuid default null
) returns uuid language plpgsql as $$
declare
  v_message_id uuid;
begin
  insert into whatsapp_messages (phone, direction, message_type, content, task_id)
  values (p_phone, p_direction, p_message_type, p_content, p_task_id)
  returning id into v_message_id;

  return v_message_id;
end;
$$;
