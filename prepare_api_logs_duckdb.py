"""
Módulo para preparação e inserção de dados no DuckDB:
1. Logs de requisição HTTP (raw.api_request_logs)
2. Posições de veículos observadas (raw.raw_vehicle_positions)
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import duckdb


def _parse_datetime(value: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Normaliza o valor para um objeto datetime compatível com TIMESTAMPTZ do DuckDB.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        val_clean = value.strip()
        if not val_clean or val_clean.upper() == "NULL":
            return None
        try:
            return datetime.fromisoformat(val_clean)
        except ValueError:
            raise ValueError(f"Formato de datetime inválido: {value}")

    raise TypeError(f"Tipo não suportado para datetime: {type(value)}")


def _parse_uuid(value: Any) -> Optional[str]:
    """Valida e normaliza o UUID para formato string."""
    if value is None:
        return None
    val_str = str(value).strip()
    if not val_str or val_str.upper() == "NULL":
        return None
    return str(uuid.UUID(val_str))


def prepare_log_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepara e tipifica um dicionário de log bruto para inserção na raw.api_request_logs.
    """
    req_uuid_raw = raw.get("request_uuid") or raw.get("request_id")
    request_uuid_val = _parse_uuid(req_uuid_raw)

    started_at = _parse_datetime(raw.get("request_started_at"))
    finished_at = _parse_datetime(raw.get("request_finished_at"))

    duration_val = raw.get("request_duration_ms")
    if duration_val is not None and str(duration_val).strip().upper() != "NULL":
        request_duration_ms = int(duration_val)
    else:
        request_duration_ms = None

    status_val = raw.get("status")
    status = str(status_val) if status_val is not None and str(status_val).strip().upper() != "NULL" else None

    error_type_val = raw.get("error_type")
    error_type = str(error_type_val) if error_type_val is not None and str(error_type_val).strip().upper() != "NULL" else None

    code_val = raw.get("http_status_code")
    if code_val is not None and str(code_val).strip().upper() != "NULL":
        http_status_code = int(code_val)
    else:
        http_status_code = None

    return {
        "request_uuid": request_uuid_val,
        "request_started_at": started_at,
        "request_finished_at": finished_at,
        "request_duration_ms": request_duration_ms,
        "status": status,
        "error_type": error_type,
        "http_status_code": http_status_code,
    }


def insert_log(con: duckdb.DuckDBPyConnection, log_record: Dict[str, Any]) -> None:
    """Insere um registro único na tabela raw.api_request_logs."""
    item = prepare_log_record(log_record)
    query = """
    INSERT INTO raw.api_request_logs (
        request_uuid,
        request_started_at,
        request_finished_at,
        request_duration_ms,
        status,
        error_type,
        http_status_code
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    con.execute(
        query,
        [
            item["request_uuid"],
            item["request_started_at"],
            item["request_finished_at"],
            item["request_duration_ms"],
            item["status"],
            item["error_type"],
            item["http_status_code"],
        ],
    )


def insert_logs(con: duckdb.DuckDBPyConnection, logs: List[Dict[str, Any]]) -> None:
    """Prepara uma lista de logs brutos e insere na tabela raw.api_request_logs."""
    prepared = [prepare_log_record(log) for log in logs]
    if not prepared:
        return

    query = """
    INSERT INTO raw.api_request_logs (
        request_uuid,
        request_started_at,
        request_finished_at,
        request_duration_ms,
        status,
        error_type,
        http_status_code
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    rows = [
        (
            item["request_uuid"],
            item["request_started_at"],
            item["request_finished_at"],
            item["request_duration_ms"],
            item["status"],
            item["error_type"],
            item["http_status_code"],
        )
        for item in prepared
    ]
    con.executemany(query, rows)


def prepare_vehicle_position(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepara um registro de posição de veículo para a tabela raw.raw_vehicle_positions.
    Preserva os nomes de coluna originais da API SPTrans (p, a, ta, py, px).
    """
    req_uuid_raw = raw.get("request_uuid") or raw.get("request_id")
    request_uuid_val = _parse_uuid(req_uuid_raw)

    fetched_at = raw.get("fetched_at")
    if isinstance(fetched_at, str):
        fetched_at = datetime.fromisoformat(fetched_at)

    cl = raw.get("cl")
    if cl is not None and str(cl).strip().upper() != "NULL":
        cl = int(cl)
    else:
        cl = None

    p = raw.get("p")
    p = str(p) if p is not None else None

    a_val = raw.get("a")
    a = bool(a_val) if a_val is not None else False

    ta = raw.get("ta")
    ta = str(ta) if ta is not None else None

    py = raw.get("py")
    py = float(py) if py is not None else None

    px = raw.get("px")
    px = float(px) if px is not None else None

    return {
        "request_uuid": request_uuid_val,
        "fetched_at": fetched_at,
        "cl": cl,
        "p": p,
        "a": a,
        "ta": ta,
        "py": py,
        "px": px,
    }


def insert_vehicle_position(con: duckdb.DuckDBPyConnection, raw_pos: Dict[str, Any]) -> None:
    """Insere um registro de veículo na tabela raw.raw_vehicle_positions."""
    item = prepare_vehicle_position(raw_pos)
    query = """
    INSERT INTO raw.raw_vehicle_positions (
        request_uuid,
        fetched_at,
        cl,
        p,
        a,
        ta,
        py,
        px
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    con.execute(
        query,
        [
            item["request_uuid"],
            item["fetched_at"],
            item["cl"],
            item["p"],
            item["a"],
            item["ta"],
            item["py"],
            item["px"],
        ],
    )
