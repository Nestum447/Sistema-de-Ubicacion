import streamlit as st
import pandas as pd
from io import BytesIO
from ortools.linear_solver import pywraplp

st.set_page_config(page_title="Sistema de Asignación de Bodega (Con Racks)", layout="wide")
st.title("📦 Sistema Automático de Asignación de Productos en Bodega (Con Racks)")

# --------------------------------------------------
# Selector de método
# --------------------------------------------------
metodo = st.radio(
    "🧠 Selecciona el método de asignación",
    ["Heurístico (actual)", "Matemático (optimización)"]
)

# --------------------------------------------------
# Subida de archivos
# --------------------------------------------------
st.sidebar.header("📂 Cargar archivos Excel")
file_ubicaciones = st.sidebar.file_uploader(
    "Cargar UBICACIONES.xlsx (con columna 'Rack')", type=["xlsx"]
)
file_productos = st.sidebar.file_uploader(
    "Cargar PRODUCTOS.xlsx", type=["xlsx"]
)

# ==================================================
# MÉTODO HEURÍSTICO (TU CÓDIGO ORIGINAL)
# ==================================================
def metodo_heuristico(productos, ubicaciones):
    asignaciones = []

    for idx, row in productos.iterrows():
        nombre = row["Producto"]
        altura = row["Altura"]
        cantidad = int(row["Existencia"])
        asignados = 0

        ubic_disponibles = ubicaciones[
            (ubicaciones["Disponible"] == True) &
            (ubicaciones["Altura_útil"] >= altura)
        ].copy()

        ubic_disponibles["Diferencia"] = ubic_disponibles["Altura_útil"] - altura
        ubic_disponibles = ubic_disponibles.sort_values(
            by=["Diferencia", "Rack", "Nivel", "Fila", "Posición"]
        )

        alturas_utilizadas = []
        niveles_asignados = []
        racks_asignados = []

        for i, ubic in ubic_disponibles.iterrows():
            if asignados >= cantidad:
                break

            ubicaciones.at[i, "Disponible"] = False
            ubicaciones.at[i, "Producto_asignado"] = nombre
            asignados += 1

            alturas_utilizadas.append(ubic["Altura_útil"])
            niveles_asignados.append(ubic["Nivel"])
            racks_asignados.append(ubic["Rack"])

            asignaciones.append({
                "Producto": nombre,
                "Rack": ubic["Rack"],
                "Nivel": ubic["Nivel"],
                "Fila": ubic["Fila"],
                "Posición": ubic["Posición"],
                "Altura_útil": ubic["Altura_útil"]
            })

        productos.loc[idx, "Asignado"] = asignados
        productos.loc[idx, "Pendiente"] = cantidad - asignados
        productos.loc[idx, "Alturas_útiles"] = ", ".join(map(str, sorted(set(alturas_utilizadas))))
        productos.loc[idx, "Niveles_asignados"] = ", ".join(map(str, sorted(set(niveles_asignados))))
        productos.loc[idx, "Racks_asignados"] = ", ".join(map(str, sorted(set(racks_asignados))))

    return productos, ubicaciones, pd.DataFrame(asignaciones)

# ==================================================
# MÉTODO MATEMÁTICO (OPTIMIZACIÓN)
# ==================================================
def metodo_matematico(productos, ubicaciones):
    solver = pywraplp.Solver.CreateSolver("SCIP")
    x = {}

    productos_idx = productos.index.tolist()
    ubic_idx = ubicaciones.index.tolist()

    # Variables binarias x[p,u]
    for p in productos_idx:
        for u in ubic_idx:
            if ubicaciones.at[u, "Disponible"] and \
               ubicaciones.at[u, "Altura_útil"] >= productos.at[p, "Altura"]:
                x[p, u] = solver.BoolVar(f"x_{p}_{u}")

    # Cada ubicación solo puede tener un producto
    for u in ubic_idx:
        solver.Add(
            sum(x[p, u] for p in productos_idx if (p, u) in x) <= 1
        )

    # Cumplir cantidad por producto
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

    df_asign = pd.DataFrame(asignaciones)

    resumen = df_asign.groupby("Producto").size().reset_index(name="Asignado")
    productos = productos.merge(resumen, on="Producto", how="left")
    productos["Asignado"] = productos["Asignado"].fillna(0).astype(int)
    productos["Pendiente"] = productos["Existencia"] - productos["Asignado"]

    return productos, ubicaciones, df_asign

# ==================================================
# EJECUCIÓN
# ==================================================
if file_ubicaciones and file_productos:
    ubicaciones = pd.read_excel(file_ubicaciones)
    productos = pd.read_excel(file_productos)

    if metodo == "Heurístico (actual)":
        productos, ubicaciones, df_asign = metodo_heuristico(productos, ubicaciones)
    else:
        productos, ubicaciones, df_asign = metodo_matematico(productos, ubicaciones)

    st.subheader("📊 Estado de las ubicaciones")
    st.dataframe(ubicaciones)

    st.subheader("📦 Estado de productos")
    st.dataframe(productos)

    st.subheader("✅ Ubicaciones asignadas")
    st.dataframe(df_asign)

    # Exportar resultados
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_asign.to_excel(writer, sheet_name="Asignaciones", index=False)
        productos.to_excel(writer, sheet_name="Resumen_Productos", index=False)
        ubicaciones.to_excel(writer, sheet_name="Ubicaciones_Final", index=False)
    output.seek(0)

    st.download_button(
        label="📥 Descargar archivo Excel con resultados",
        data=output,
        file_name="resultado_asignaciones.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("📑 Por favor carga los archivos de productos y ubicaciones desde la barra lateral.")
