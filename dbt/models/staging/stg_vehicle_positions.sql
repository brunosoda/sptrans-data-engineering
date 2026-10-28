select
    request_uuid,
    fetched_at,
    cl as line_id,
    p as vehicle_id,
    a as accessible_vehicle,
    ta as update_time,
    px as longitude,
    py as latitude,
    loaded_at,
    trip_id
from {{ source('raw', 'raw_vehicle_positions') }}
