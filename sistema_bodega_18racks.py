import streamlit as st
import pandas as pd
from io import BytesIO
from ortools.linear_solver import pywraplp

st.set_page_config(page_title="Sistema de Asignación de Bodega", layout="wide")
st.title("📦 Sistema Automático de Asignación de Productos en Bodega")

# --- Selector de método ---
metodo = st.radio(
    "🧠 Método de asignación",
    ["Método actual (heurístico)", "Método matemático (optimización)"]
)

# --- Subida de archivos ---
st.sidebar.header("📂 Cargar archivos Excel")
file_ubicaciones = st.sidebar.file_uploader("Cargar UBICACIONES.xlsx", type=["xlsx"])
file_productos = st.sidebar.file_uploader("Cargar PRODUCTOS.xlsx", type=["xlsx"])

# =========================================================
# MÉTODO 1: HEURÍSTICO (TU MODELO ACTUAL)
# =========================================================
def asignar_heuristico(productos, ubicaciones):
    asignaciones = []

    for idx, row in productos.iterrows():
        nombre = row["Producto"]
        altura = row["Altura"]
        cantidad = int(row["Existencia"])
        asignados = 0

        disponibles = ubicaciones[
            (ubicaciones["Disponible"] == True) &
            (ubicaciones["Altura_útil"] >= altura)
        ].copy()

        disponibles["Diferencia"] = disponibles["Altura_útil"] - altura
        disponibles = disponibles.sort_values(
            by=["Diferencia", "Rack", "Nivel", "Fila", "Posición"]
        )

        for i, u in disponibles.iterrows():
            if asignados >= cantidad:
                break
            ubicaciones.at[i, "Disponible"] = False
            ubicaciones.at[i, "Producto_asignado"] = nombre
            asignados += 1

            asignaciones.append({
                "Producto": nombre,
                "Rack": u["Rack"],
                "Nivel": u["Nivel"],
                "Fila": u["Fila"],
                "Posición": u["Posición"],
                "Altura_útil": u["Altura_útil"]
            })

        productos.loc[idx, "Asignado"] = asignados
        productos.loc[idx, "Pendiente"] = cantidad - asignados

    return productos, ubicaciones, pd.DataFrame(asignaciones)

# =========================================================
# MÉTODO 2: MATEMÁTICO (OPTIMIZACIÓN)
# =========================================================
def asignar_matematico(productos, ubicaciones):
    solver = pywraplp.Solver.CreateSolver("SCIP")
    x = {}

    productos_idx = productos.index.tolist()
    ubic_idx = ubicaciones.index.tolist()

    # Variables binarias
    for p in productos_idx:
        for u in ubic_idx:
            if ubicaciones.at[u, "Altura_útil"] >= productos.at[p, "Altura"]:
                x[p, u] = solver.BoolVar(f"x_{p}_{u}")

    # Restricción: una ubicación solo un producto
    for u in ubic_idx:
        solver.Add(
            sum(x[p, u] for p in productos_idx if (p, u) in x) <= 1
        )

    # Restricción: cumplir cantidad por producto
    for p in productos_idx:
        solver.Add(
            sum(x[p, u] for u in ubic_idx if (p, u) in x)
            <= int(productos.at[p, "Existencia"])
        )

    # Función objetivo: minimizar desperdicio de altura
    solver.Minimize(
        sum(
            (ubicaciones.at[u, "Altura_útil"] - productos.at[p, "Altura"]) * x[p, u]
            for (p, u) in x
        )
    )

    solver.Solve()

    asignaciones = []

    for (p, u), var in x.items():
        if var.solution_value() == 1:
            ubicaciones.at[u, "Disponible"] = False
            ubicaciones.at[u, "Producto_asignado"] = productos.at[p, "Producto"]

            asignaciones.append({
                "Producto": productos.at[p, "Producto"],
                "Rack": ubicaciones.at[u, "Rack"],
                "Nivel": ubicaciones.at[u, "Nivel"],
                "Fila": ubicaciones.at[u, "Fila"],
                "Posición": ubicaciones.at[u, "Posición"],
                "Altura_útil": ubicaciones.at[u, "Altura_útil"]
            })

    df_asig = pd.DataFrame(asignaciones)
    resumen = df_asig.groupby("Producto").size().reset_index(name="Asignado")
    productos = productos.merge(resumen, on="Producto", how="left")
    productos["Asignado"] = productos["Asignado"].fillna(0).astype(int)
    productos["Pendiente"] = productos["Existencia"] - productos["Asignado"]

    return productos, ubicaciones, df_asig

# =========================================================
# EJECUCIÓN
# =========================================================
if file_ubicaciones and file_productos:
    ubicaciones = pd.read_excel(file_ubicaciones)
    productos = pd.read_excel(file_productos)

    if metodo == "Método actual (heurístico)":
        productos, ubicaciones, df_asign = asignar_heuristico(productos, ubicaciones)
    else:
        productos, ubicaciones, df_asign = asignar_matematico(productos, ubicaciones)

    st.subheader("📊 Estado de ubicaciones")
    st.dataframe(ubicaciones)

    st.subheader("📦 Estado de productos")
    st.dataframe(productos)

    st.subheader("✅ Asignaciones")
    st.dataframe(df_asign)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_asign.to_excel(writer, sheet_name="Asignaciones", index=False)
        productos.to_excel(writer, sheet_name="Productos", index=False)
        ubicaciones.to_excel(writer, sheet_name="Ubicaciones", index=False)
    output.seek(0)

    st.download_button(
        "📥 Descargar resultados",
        data=output,
        file_name="resultado_asignaciones.xlsx"
    )
else:
    st.info("📑 Carga los archivos para iniciar.")
