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
# SELECCIÓN DE MÉTODO
# =====================================================
st.header("⚙️ Selección de método")

metodo = st.selectbox(
    "¿Qué método deseas utilizar?",
    (
        "Heurístico (rápido)",
        "Matemático (óptimo - OR-Tools)"
    )
)

st.divider()

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

# =====================================================
# NORMALIZAR COLUMNAS (ADAPTADO A TU EXCEL)
# =====================================================
productos.columns = productos.columns.str.strip().str.lower()
ubicaciones.columns = ubicaciones.columns.str.strip().str.lower()

map_productos = {
    "producto": "Producto",
    "productos": "Producto",
    "descripcion": "Producto",
    "sku": "Producto",
    "nombre": "Producto",

    "cantidad": "Cantidad",
    "cant": "Cantidad",
    "qty": "Cantidad",
    "unidades": "Cantidad",
    "existencia": "Cantidad"   # 👈 CLAVE PARA TU CASO
}

map_ubicaciones = {
    "ubicacion": "Ubicacion",
    "ubicaciones": "Ubicacion",
    "posicion": "Ubicacion",
    "location": "Ubicacion",
    "slot": "Ubicacion"
}

productos = productos.rename(
    columns={c: map_productos[c] for c in productos.columns if c in map_productos}
)

ubicaciones = ubicaciones.rename(
    columns={c: map_ubicaciones[c] for c in ubicaciones.columns if c in map_ubicaciones}
)

# =====================================================
# VALIDACIONES
# =====================================================
if "Producto" not in productos.columns or "Cantidad" not in productos.columns:
    st.error(
        "❌ No se reconocen columnas en PRODUCTOS.xlsx\n"
        f"Columnas encontradas: {list(productos.columns)}"
    )
    st.stop()

if "Ubicacion" not in ubicaciones.columns:
    st.error(
        "❌ No se reconoce columna en UBICACIONES.xlsx\n"
        f"Columnas encontradas: {list(ubicaciones.columns)}"
    )
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
        solver.Add(sum(x[i, j] for j in U) == int(productos.loc[i, "Cantidad"]))

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
if st.button("🚀 Ejecutar asignación", use_container_width=True):

    if metodo.startswith("Heurístico"):
        df_asign = metodo_heuristico(productos, ubicaciones)
    else:
        df_asign = metodo_matematico(productos, ubicaciones)

    if df_asign.empty:
        st.error("No se generaron asignaciones")
        st.stop()

    st.success("✅ Asignación realizada correctamente")

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
