# Um app FastAPI pequeno. A Vercel roda ele e serve a página da pasta public/.
import re

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# A documentação fica em /api, assim todo o app mora em /api.
app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json")


# ---------------------------------------------------------------------------
# Veículos: cadastrar, listar, consultar, atualizar e excluir.
# ---------------------------------------------------------------------------

# Os veículos ficam na memória, num dicionário que liga o id ao veículo.
# Eles somem quando o servidor reinicia. O banco de dados vem depois.
veiculos = {}
proximo_id = 1

# Placa no formato antigo ABC1234 ou no Mercosul ABC1D23.
PLACA = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")


# O corpo de POST e PUT /api/veiculos, por exemplo
# {"placa": "QRS4F21", "marca": "Volkswagen", "modelo": "Gol 1.6",
#  "ano": 2022, "quilometragem": 82300, "cliente_id": 1}
class Veiculo(BaseModel):
    placa: str
    marca: str
    modelo: str
    ano: int
    quilometragem: int = 0
    cliente_id: int | None = None


# Confere os campos e devolve a placa em maiúsculas, sem "-".
def validar_veiculo(entrada: Veiculo):
    placa = entrada.placa.upper().replace("-", "").strip()
    if not PLACA.match(placa):
        raise HTTPException(status_code=422, detail="Placa inválida. Use ABC1234 ou ABC1D23.")
    if entrada.marca.strip() == "" or entrada.modelo.strip() == "":
        raise HTTPException(status_code=422, detail="Marca e modelo são obrigatórios.")
    if entrada.ano < 1900 or entrada.ano > 2100:
        raise HTTPException(status_code=422, detail="Ano inválido.")
    if entrada.quilometragem < 0:
        raise HTTPException(status_code=422, detail="A quilometragem não pode ser negativa.")
    return placa


# Devolve o veículo, ou responde 404 se não existe nenhum com esse id.
def buscar_veiculo(id: int):
    if id not in veiculos:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    return veiculos[id]


# GET /api/veiculos
@app.get("/api/veiculos")
def listar_veiculos():
    return list(veiculos.values())


# GET /api/veiculos/1
@app.get("/api/veiculos/{id}")
def consultar_veiculo(id: int):
    return buscar_veiculo(id)


# POST /api/veiculos
@app.post("/api/veiculos", status_code=201)
def cadastrar_veiculo(entrada: Veiculo):
    global proximo_id
    placa = validar_veiculo(entrada)
    for veiculo in veiculos.values():
        if veiculo["placa"] == placa:
            raise HTTPException(status_code=409, detail="Já existe um veículo com essa placa.")

    veiculo = {"id": proximo_id, **entrada.model_dump(), "placa": placa}
    veiculos[proximo_id] = veiculo
    proximo_id += 1
    return veiculo


# PUT /api/veiculos/1
@app.put("/api/veiculos/{id}")
def atualizar_veiculo(id: int, entrada: Veiculo):
    buscar_veiculo(id)
    placa = validar_veiculo(entrada)
    for veiculo in veiculos.values():
        if veiculo["placa"] == placa and veiculo["id"] != id:
            raise HTTPException(status_code=409, detail="Já existe um veículo com essa placa.")

    veiculo = {"id": id, **entrada.model_dump(), "placa": placa}
    veiculos[id] = veiculo
    return veiculo


# DELETE /api/veiculos/1
# Quando existirem ordens de serviço, um veículo com ordens não pode ser excluído (409).
@app.delete("/api/veiculos/{id}", status_code=204)
def excluir_veiculo(id: int):
    buscar_veiculo(id)
    del veiculos[id]
