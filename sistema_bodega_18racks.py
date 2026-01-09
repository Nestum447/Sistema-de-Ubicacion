import streamlit as st
import pandas as pd
from ortools.linear_solver import pywraplp

# ----------------------------------
# Configuración Streamlit
# ----------------------------------
st.set_page_config(page_title="Sistema de Asignación de Bodega", layout="wide")
st.title("📦 Sistema Automático de Asignación de Productos en Bodega")

# ----------------------------------
# Carga de archivos
# ----------------------------------
st.header("📂 Cargar archivos Excel")

file_ubic = st.file_uploader("Cargar UBICACIONES.xlsx", type=["xlsx"])
file_prod = st.file_uploader("Cargar PRODUCTOS.xlsx", type=["xlsx"])

if not file_ubic or not file_prod:
    st.stop()

ubicaciones = pd.read_excel(file_ubic)
productos = pd.read_excel(file_prod)

# Normalizar columnas (MUY IMPORTANTE)
ubicaciones.columns = ubicaciones.columns.str.strip()
productos.columns = productos.columns.str.strip()

# Validaciones mínimas
required_prod = ["Producto", "Cantidad"]
required_ubic = ["Ubicacion"]

for col in required_prod:
    if col not in productos.columns:
        st.error(f"Falta columna '{col}' en PRODUCTOS.xlsx")
        st.stop()

for col in required_ubic:
    if col not in ubicaciones.columns:
        st.error(f"Falta columna '{col}' en UBICACIONES.xlsx")
        st.stop()

# ----------------------------------
# MÉTODO HEURÍSTICO
# ----------------------------------
def asignar_heuristico(productos, ubicaciones):
    asignaciones = []
    u = 0

    for _, prod in productos.iterrows():
        for _ in range(int(prod["Cantidad"])):
            if u >= len(ubicaciones):
                break
            asignaciones.append({
                "Producto": prod["Producto"],
                "Ubicacion": ubicaciones.loc[u, "Ubicacion"]
            })
            u += 1

    df_asig = pd.DataFrame(asignaciones)
    return df_asig


# ----------------------------------
# MÉTODO MATEMÁTICO (OR-TOOLS)
# ----------------------------------
def asignar_matematico(productos, ubicaciones):
    solver = pywraplp.Solver.CreateSolver("SCIP")

    P = range(len(productos))
    U = range(len(ubicaciones))

    # Variables binarias
    x = {}
    for i in P:
        for j in U:
            x[i, j] = solver.BoolVar(f"x_{i}_{j}")

    # Restricción: cada ubicación solo 1 producto
    for j in U:
        solver.Add(sum(x[i, j] for i in P) <= 1)

    # Restricción: respetar cantidad por producto
    for i in P:
        solver.Add(sum(x[i, j] for j in U) == int(productos.loc[i, "Cantidad"]))

    # Función objetivo simple
    solver.Maximize(sum(x[i, j] for i in P for j in U))

    status = solver.Solve()

    if status != pywraplp.Solver.OPTIMAL:
        st.error("No se encontró solución óptima")
        return pd.DataFrame()

    # Construcción CORRECTA del DataFrame
    asignaciones = []

    for i in P:
        for j in U:
            if x[i, j].solution_value() > 0.5:
                asignaciones.append({
                    "Producto": productos.loc[i, "Producto"],
                    "Ubicacion": ubicaciones.loc[j, "Ubicacion"]
                })

    df_asig = pd.DataFrame(asignaciones)

    # Blindaje
    assert "Producto" in df_asig.columns
    assert "Ubicacion" in df_asig.columns

    return df_asig


# ----------------------------------
# Selección de método
# ----------------------------------
st.header("⚙️ Método de asignación")

metodo = st.radio(
    "Selecciona el método",
    ["Heurístico (actual)", "Matemático (óptimo)"]
)

if st.button("🚀 Ejecutar asignación"):
    if metodo == "Heurístico (actual)":
        df_asig = asignar_heuristico(productos, ubicaciones)
    else:
        df_asig = asignar_matematico(productos, ubicaciones)

    st.success("Asignación realizada correctamente")

    # Mostrar asignaciones
    st.subheader("📋 Asignaciones")
    st.dataframe(df_asig, use_container_width=True)

    # Resumen (YA NO FALLA)
    st.subheader("📊 Resumen por producto")
    resumen = (
        df_asig
        .groupby("Producto")
        .size()
        .reset_index(name="Asignado")
    )
    st.dataframe(resumen, use_container_width=True)
