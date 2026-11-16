# A small FastAPI app. Vercel runs it, and serves the page in the public/ folder.
import re

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Put the docs under /api, so all the app lives under /api.
app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json")

# ---------------------------------------------------------------------------
# Veículos: cadastrar, listar, consultar, atualizar e excluir.
# ---------------------------------------------------------------------------

# The vehicles live in memory, in a dict from id to vehicle.
# They are lost when the server restarts. A database comes later.
vehicles = {}
next_id = 1

# A plate is old style ABC1234 or Mercosul ABC1D23.
PLATE = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")

# The body of POST and PUT /api/veiculos, for example
# {"placa": "QRS4F21", "marca": "Volkswagen", "modelo": "Gol 1.6",
#  "ano": 2022, "quilometragem": 82300, "cliente_id": 1}
class Vehicle(BaseModel):
    placa: str
    marca: str
    modelo: str
    ano: int
    quilometragem: int = 0
    cliente_id: int | None = None


# Check the fields, and return the plate in upper case without "-".
def check_vehicle(data: Vehicle):
    plate = data.placa.upper().replace("-", "").strip()
    if not PLATE.match(plate):
        raise HTTPException(status_code=422, detail="Placa inválida. Use ABC1234 ou ABC1D23.")
    if data.marca.strip() == "" or data.modelo.strip() == "":
        raise HTTPException(status_code=422, detail="Marca e modelo são obrigatórios.")
    if data.ano < 1900 or data.ano > 2100:
        raise HTTPException(status_code=422, detail="Ano inválido.")
    if data.quilometragem < 0:
        raise HTTPException(status_code=422, detail="A quilometragem não pode ser negativa.")
    return plate


# Give the vehicle, or answer 404 if there is none with this id.
def find_vehicle(id: int):
    if id not in vehicles:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    return vehicles[id]


# GET /api/veiculos
@app.get("/api/veiculos")
def list_vehicles():
    return list(vehicles.values())


# GET /api/veiculos/1
@app.get("/api/veiculos/{id}")
def get_vehicle(id: int):
    return find_vehicle(id)


# POST /api/veiculos
@app.post("/api/veiculos", status_code=201)
def create_vehicle(data: Vehicle):
    global next_id
    plate = check_vehicle(data)
    for vehicle in vehicles.values():
        if vehicle["placa"] == plate:
            raise HTTPException(status_code=409, detail="Já existe um veículo com essa placa.")

    vehicle = {"id": next_id, **data.model_dump(), "placa": plate}
    vehicles[next_id] = vehicle
    next_id += 1
    return vehicle


# PUT /api/veiculos/1
@app.put("/api/veiculos/{id}")
def update_vehicle(id: int, data: Vehicle):
    find_vehicle(id)
    plate = check_vehicle(data)
    for vehicle in vehicles.values():
        if vehicle["placa"] == plate and vehicle["id"] != id:
            raise HTTPException(status_code=409, detail="Já existe um veículo com essa placa.")

    vehicle = {"id": id, **data.model_dump(), "placa": plate}
    vehicles[id] = vehicle
    return vehicle


# DELETE /api/veiculos/1
# When there are service orders, a vehicle with orders must not be deleted (409).
@app.delete("/api/veiculos/{id}", status_code=204)
def delete_vehicle(id: int):
    find_vehicle(id)
    del vehicles[id]
