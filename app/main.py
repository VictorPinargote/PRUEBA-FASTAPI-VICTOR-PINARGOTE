# app/salas.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.datos import SALAS
from app.esquemas import Sala, SalaActualizar, SalaCrear

router = APIRouter(prefix="/salas", tags=["salas"])


# --- DEPENDENCIA (404 centralizado) ---
def obtener_sala(codigo: str) -> dict:
    for sala in SALAS:
        if sala["codigo"] == codigo.upper():
            return sala
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No existe la sala '{codigo}'",
    )


SalaEncontrada = Annotated[dict, Depends(obtener_sala)]


# --- PREGUNTA 1: CRUD (Listar y Crear) ---
@router.get("", response_model=list[Sala])
def listar_salas(
    piso: Annotated[int | None, Query(ge=1, le=5)] = None,
    solo_3d: bool = False,
) -> list[dict]:
    resultado = SALAS
    if piso is not None:
        resultado = [s for s in resultado if s["piso"] == piso]
    if solo_3d:
        resultado = [s for s in resultado if s["es_3d"]]
    return resultado


@router.post("", response_model=Sala, status_code=status.HTTP_201_CREATED)
def crear_sala(nueva: SalaCrear) -> dict:
    if any(s["codigo"] == nueva.codigo for s in SALAS):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La sala '{nueva.codigo}' ya existe",
        )
    SALAS.append(nueva.model_dump())
    return SALAS[-1]


# --- PREGUNTA 2: Aforo vendible de una jornada (ANTES de /{codigo}) ---
@router.get("/aforo-jornada")
def aforo_jornada(
    funciones: Annotated[int, Query(ge=1, le=12)],
    piso: Annotated[int | None, Query(ge=1, le=5)] = None,
) -> dict:
    seleccion = [s for s in SALAS if piso is None or s["piso"] == piso]
    if not seleccion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay salas en el piso {piso}",
        )

    total_butacas = 0
    vendible_por_funcion = 0
    salas_3d = 0

    for sala in seleccion:
        total_butacas += sala["butacas"]
        # Regla: 10% reservado -> parte entera del 90% sala por sala
        vendible_por_funcion += int(sala["butacas"] * 0.9)
        if sala["es_3d"]:
            salas_3d += 1

    return {
        "salas": len(seleccion),
        "funciones": funciones,
        "butacas_promedio": round(total_butacas / len(seleccion), 2),
        "aforo_total": total_butacas * funciones,
        "aforo_vendible": vendible_por_funcion * funciones,
        "porcentaje_3d": round(salas_3d * 100 / len(seleccion), 1),
    }


# --- PREGUNTA 3: Salas en mantenimiento (ANTES de /{codigo}) ---
@router.get("/mantenimiento")
def estado_mantenimiento(
    en_mantenimiento: Annotated[list[str] | None, Query()] = None,
) -> dict:
    if not SALAS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay salas registradas",
        )

    codigos_fuera = {c.upper() for c in (en_mantenimiento or [])}
    total = 0
    fuera_count = 0
    operativas_count = 0
    aforo_operativo = 0
    mayor_sala: dict | None = None

    for sala in SALAS:
        total += 1
        if sala["codigo"] in codigos_fuera:
            fuera_count += 1
        else:
            operativas_count += 1
            aforo_operativo += sala["butacas"]
            if mayor_sala is None or sala["butacas"] > mayor_sala["butacas"]:
                mayor_sala = sala

    return {
        "total": total,
        "en_mantenimiento": fuera_count,
        "operativas": operativas_count,
        "porcentaje_fuera_de_servicio": round(fuera_count * 100 / total, 1),
        "aforo_operativo": aforo_operativo,
        "sala_operativa_mayor": mayor_sala["codigo"] if mayor_sala else None,
    }


# --- PREGUNTA 1: CRUD con /{codigo} ---
@router.get("/{codigo}", response_model=Sala)
def ver_sala(sala: SalaEncontrada) -> dict:
    return sala


@router.put("/{codigo}", response_model=Sala)
def actualizar_sala(cambios: SalaActualizar, sala: SalaEncontrada) -> dict:
    sala.update(cambios.model_dump(exclude_unset=True))
    return sala


@router.delete("/{codigo}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sala(sala: SalaEncontrada) -> None:
    SALAS.remove(sala)