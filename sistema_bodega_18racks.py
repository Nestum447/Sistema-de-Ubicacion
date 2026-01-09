import streamlit as st
import pandas as pd
from ortools.linear_solver import pywraplp

# =====================================================
# CONFIGURACIÓN
# =====================================================
st.set_page_config(
    page_title="Sistema de Asignación de Bodega",
    layout="wide"
)

st.title("📦 Sistema Automático de Asignación de Productos en Bodega")

# =====================================================
# SELECCIÓN DE MÉTODO (PRIMERO)
# =====================================================
st.header("⚙️ Selección de método")

metodo = st.selectbox(
    "¿Qué método deseas utilizar?",
    (
        "Heurístico (rápido, actual)",
        "Matemático (óptimo, OR-Tools)"
    )
)

st.info(
    "🔹 Heurístico: asignación secuencial simple\n"
    "🔹 Matemático: optimización exacta usando programación lineal"
)

st.divider()

# =====================================================
# CARGA DE ARCHIVOS
# =====================================================
st.header("📂 Cargar archivos Excel")

file_ubic = st.file_uploader("Cargar UBICACIONES.xlsx", type=["xlsx"])
file_prod = st.file_uploader("Cargar PRODUCTOS.xlsx", type=["xlsx"])

if not file_ubic or not file_prod:
    st.warning("Cargue ambos archivos para continuar")
    st.stop()

ubicaciones = pd.read_excel(file_ubic)
productos = pd.read_excel(file_prod)

# Normalizar columnas
ubicaciones.columns = ubicaciones.columns.str.strip()
productos.columns = productos.columns.str.strip()

# =====================================================
# VALIDACIONES
# =====================================================
if "Producto" not in productos.columns or "Cantidad" not in productos.columns:
    st.error("PRODUCTOS.xlsx debe contener columnas: Producto, Cantidad")
    st.stop()

if "Ubicacion" not in ubicaciones.columns:
    st.error("UBICACIONES.xlsx debe contener la columna: Ubicacion")
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
# MÉTODO MATEMÁTICO
# =====================================================
def metodo_matematico(productos, ubicaciones):
    solver = pywraplp.Solver.CreateSolver("SCIP")

    P = range(len(productos))
    U = range(len(ubicaciones))

    x = {}
    for i in P:
        for j in U:
            x[i, j] = solver.BoolVar(f"x_{i}_{j}")

    for j in U:
        solver.Add(sum(x[i, j] for i in P) <= 1)

    for i in P:
        solver.Add(
            sum(x[i, j] for j in U) == int(productos.loc[i, "Cantidad"])
        )

    solver.Maximize(sum(x[i, j] for i in P for j in U))

    status = solver.Solve()

    if status != pywraplp.Solver.OPTIMAL:
        return pd.DataFrame(columns=["Producto", "Ubicacion"])

    asignaciones = []

    for i in P:
        for j in U:
            if x[i, j].solution_value() > 0.5:
                asignaciones.append({
                    "Producto": productos.loc[i, "Producto"],
                    "Ubicacion": ubicaciones.loc[j, "Ubicacion"]
                })

    return pd.DataFrame(asignaciones)

# =====================================================
# EJECUCIÓN
# =====================================================
st.divider()

if st.button("🚀 Ejecutar asignación", use_container_width=True):

    if metodo.startswith("Heurístico"):
        df_asign = metodo_heuristico(productos, ubicaciones)
    else:
        df_asign = metodo_matematico(productos, ubicaciones)

    if df_asign.empty:
        st.error("No se pudo generar la asignación")
        st.stop()

    st.success("✅ Asignación realizada correctamente")

    # Resultados
    st.subheader("📋 Asignaciones")
    st.dataframe(df_asign, use_container_width=True)

    st.subheader("📊 Resumen por producto")
    resumen = (
        df_asign
        .groupby("Producto")
        .size()
        .reset_index(name="Asignado")
    )
    st.dataframe(resumen, use_container_width=True)
