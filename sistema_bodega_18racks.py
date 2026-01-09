import streamlit as st
import pandas as pd
from ortools.linear_solver import pywraplp

# =====================================================
# CONFIGURACIÓN STREAMLIT
# =====================================================
st.set_page_config(
    page_title="Sistema de Asignación de Bodega",
    layout="wide"
)

st.title("📦 Sistema Automático de Asignación de Productos en Bodega")

# =====================================================
# CARGA DE ARCHIVOS
# =====================================================
st.header("📂 Cargar archivos Excel")

file_ubic = st.file_uploader("Cargar UBICACIONES.xlsx", type=["xlsx"])
file_prod = st.file_uploader("Cargar PRODUCTOS.xlsx", type=["xlsx"])

if not file_ubic or not file_prod:
    st.info("Cargue ambos archivos para continuar")
    st.stop()

ubicaciones = pd.read_excel(file_ubic)
productos = pd.read_excel(file_prod)

# Normalizar nombres de columnas (CRÍTICO)
ubicaciones.columns = ubicaciones.columns.str.strip()
productos.columns = productos.columns.str.strip()

# =====================================================
# VALIDACIONES
# =====================================================
required_prod = ["Producto", "Cantidad"]
required_ubic = ["Ubicacion"]

for col in required_prod:
    if col not in productos.columns:
        st.error(f"❌ Falta columna '{col}' en PRODUCTOS.xlsx")
        st.stop()

for col in required_ubic:
    if col not in ubicaciones.columns:
        st.error(f"❌ Falta columna '{col}' en UBICACIONES.xlsx")
        st.stop()

# =====================================================
# MÉTODO HEURÍSTICO
# =====================================================
def metodo_heuristico(productos, ubicaciones):
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

    return pd.DataFrame(asignaciones)


# =====================================================
# MÉTODO MATEMÁTICO (OR-TOOLS)
# =====================================================
def metodo_matematico(productos, ubicaciones):
    solver = pywraplp.Solver.CreateSolver("SCIP")

    P = range(len(productos))
    U = range(len(ubicaciones))

    # Variables binarias
    x = {}
    for i in P:
        for j in U:
            x[i, j] = solver.BoolVar(f"x_{i}_{j}")

    # Cada ubicación solo puede tener un producto
    for j in U:
        solver.Add(sum(x[i, j] for i in P) <= 1)

    # Respetar cantidad de cada producto
    for i in P:
        solver.Add(
            sum(x[i, j] for j in U) == int(productos.loc[i, "Cantidad"])
        )

    # Función objetivo (simple)
    solver.Maximize(sum(x[i, j] for i in P for j in U))

    status = solver.Solve()

    if status != pywraplp.Solver.OPTIMAL:
        st.error("❌ No se encontró solución óptima")
        return pd.DataFrame(columns=["Producto", "Ubicacion"])

    asignaciones = []

    for i in P:
        for j in U:
            if x[i, j].solution_value() > 0.5:
                asignaciones.append({
                    "Producto": productos.loc[i, "Producto"],
                    "Ubicacion": ubicaciones.loc[j, "Ubicacion"]
                })

    df_asign = pd.DataFrame(asignaciones)

    return df_asign


# =====================================================
# SELECCIÓN DE MÉTODO
# =====================================================
st.header("⚙️ Método de asignación")

metodo = st.radio(
    "Selecciona el método",
    ["Heurístico (actual)", "Matemático (óptimo)"]
)

# =====================================================
# EJECUCIÓN
# =====================================================
if st.button("🚀 Ejecutar asignación"):

    if metodo == "Heurístico (actual)":
        df_asign = metodo_heuristico(productos, ubicaciones)
    else:
        df_asign = metodo_matematico(productos, ubicaciones)

    if df_asign.empty:
        st.warning("No se generaron asignaciones")
        st.stop()

    st.success("✅ Asignación realizada correctamente")

    # ---------------------------
    # RESULTADOS
    # ---------------------------
    st.subheader("📋 Asignaciones")
    st.dataframe(df_asign, use_container_width=True)

    # ---------------------------
    # RESUMEN (FUERA DEL MÉTODO)
    # ---------------------------
    st.subheader("📊 Resumen por producto")

    resumen = (
        df_asign
        .groupby("Producto")
        .size()
        .reset_index(name="Asignado")
    )

    st.dataframe(resumen, use_container_width=True)
