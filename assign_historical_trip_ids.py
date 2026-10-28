"""
Script para calcular e atribuir retroativamente o trip_id
para os dados existentes na tabela raw.raw_vehicle_positions.

Critérios para início de uma nova viagem:
1. Mudança no prefixo do veículo (p != LAG(p)), OU
2. Intervalo de tempo superior a 10 minutos (600s) entre leituras consecutivas
   (cobrindo casos em que o mesmo veículo rodou em dias/horários distintos).
"""

import duckdb

DB_PATH = "sptrans.duckdb"


def assign_historical_trip_ids():
    print(f"Conectando ao banco DuckDB: {DB_PATH}...")
    con = duckdb.connect(DB_PATH)

    # 1. Verificar registros totais e nulos
    total_records = con.execute("SELECT COUNT(*) FROM raw.raw_vehicle_positions").fetchone()[0]
    null_trip_ids = con.execute("SELECT COUNT(*) FROM raw.raw_vehicle_positions WHERE trip_id IS NULL").fetchone()[0]
    print(f"Total de registros na tabela: {total_records}")
    print(f"Registros com trip_id nulo: {null_trip_ids}")

    if total_records == 0:
        print("Tabela vazia. Nenhuma atualização necessária.")
        con.close()
        return

    # 2. Query que identifica os limites das viagens usando Window Functions
    # Usamos fetched_at como linha temporal principal.
    query_preview = """
    WITH ordered_positions AS (
        SELECT 
            request_uuid,
            p,
            fetched_at,
            ta,
            LAG(p) OVER (ORDER BY fetched_at ASC) AS prev_p,
            LAG(fetched_at) OVER (ORDER BY fetched_at ASC) AS prev_fetched_at
        FROM raw.raw_vehicle_positions
    ),
    trip_markers AS (
        SELECT 
            request_uuid,
            p,
            fetched_at,
            ta,
            CASE 
                -- Primeira linha é início de viagem
                WHEN prev_p IS NULL THEN 1
                -- Mudança de veículo
                WHEN p != prev_p THEN 1
                -- Gap de mais de 10 minutos (600 segundos)
                WHEN epoch(fetched_at) - epoch(prev_fetched_at) > 600 THEN 1
                ELSE 0
            END AS is_new_trip
        FROM ordered_positions
    ),
    calculated_trips AS (
        SELECT 
            request_uuid,
            p,
            fetched_at,
            ta,
            SUM(is_new_trip) OVER (ORDER BY fetched_at ASC) AS calc_trip_id
        FROM trip_markers
    )
    SELECT 
        calc_trip_id,
        p,
        MIN(fetched_at)::VARCHAR AS trip_started_at,
        MAX(fetched_at)::VARCHAR AS trip_ended_at,
        MIN(ta) AS min_ta,
        MAX(ta) AS max_ta,
        COUNT(*) AS total_points,
        ROUND((epoch(MAX(fetched_at)) - epoch(MIN(fetched_at))) / 60, 2) AS duration_minutes
    FROM calculated_trips
    GROUP BY calc_trip_id, p
    ORDER BY calc_trip_id;
    """

    print("\n--- Viagens identificadas nos dados históricos ---")
    trips_summary = con.execute(query_preview).fetchall()
    for row in trips_summary:
        trip_id, p, start_dt, end_dt, min_ta, max_ta, points, dur = row
        print(
            f"Trip ID: {trip_id:2d} | Ônibus: {p:6s} | "
            f"Início: {start_dt} | Fim: {end_dt} | "
            f"Pontos: {points:3d} | Duração: {dur:5.2f} min"
        )

    # 3. Atualizar a tabela raw.raw_vehicle_positions
    print("\nAtualizando coluna trip_id na tabela raw.raw_vehicle_positions...")
    update_query = """
    WITH ordered_positions AS (
        SELECT 
            request_uuid,
            p,
            fetched_at,
            LAG(p) OVER (ORDER BY fetched_at ASC) AS prev_p,
            LAG(fetched_at) OVER (ORDER BY fetched_at ASC) AS prev_fetched_at
        FROM raw.raw_vehicle_positions
    ),
    trip_markers AS (
        SELECT 
            request_uuid,
            CASE 
                WHEN prev_p IS NULL THEN 1
                WHEN p != prev_p THEN 1
                WHEN epoch(fetched_at) - epoch(prev_fetched_at) > 600 THEN 1
                ELSE 0
            END AS is_new_trip,
            fetched_at
        FROM ordered_positions
    ),
    calculated_trips AS (
        SELECT 
            request_uuid,
            SUM(is_new_trip) OVER (ORDER BY fetched_at ASC) AS calc_trip_id
        FROM trip_markers
    )
    UPDATE raw.raw_vehicle_positions
    SET trip_id = calculated_trips.calc_trip_id
    FROM calculated_trips
    WHERE raw.raw_vehicle_positions.request_uuid = calculated_trips.request_uuid;
    """

    con.execute(update_query)

    # 4. Validação final
    remaining_nulls = con.execute("SELECT COUNT(*) FROM raw.raw_vehicle_positions WHERE trip_id IS NULL").fetchone()[0]
    max_trip_id = con.execute("SELECT MAX(trip_id) FROM raw.raw_vehicle_positions").fetchone()[0]
    print(f"\nAtualização concluída!")
    print(f"Maior trip_id atribuído: {max_trip_id}")
    print(f"Registros com trip_id nulo restantes: {remaining_nulls}")

    con.close()


if __name__ == "__main__":
    assign_historical_trip_ids()
