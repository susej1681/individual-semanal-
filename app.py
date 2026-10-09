import streamlit as st
import pandas as pd
import re
from collections import Counter
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Individual",
    page_icon="🎯",
    layout="centered"
)

GRANJITA_ID = "1JpJgdyqu3HP4TlNyDocQ7WQjnsDfkUMP4Aj3q97TmHY"
LOTTO_ID = "1Wm31ULE_YckLHEaek8Kre42UMdglkli-QeLpHxzFf-I"

ANIMALITOS_DICT = {
    0: "Delfín", 1: "Carnero", 2: "Toro", 3: "Ciempiés", 4: "Alacrán",
    5: "León", 6: "Rana", 7: "Perico", 8: "Ratón", 9: "Águila",
    10: "Tigre", 11: "Gato", 12: "Caballo", 13: "Mono", 14: "Paloma",
    15: "Zorro", 16: "Oso", 17: "Pavo", 18: "Burro", 19: "Chivo",
    20: "Cochino", 21: "Gallo", 22: "Camello", 23: "Cebra", 24: "Iguana",
    25: "Gallina", 26: "Vaca", 27: "Perro", 28: "Zamuro", 29: "Elefante",
    30: "Caimán", 31: "Lapa", 32: "Ardilla", 33: "Pescado", 34: "Venado",
    35: "Jirafa", 36: "Culebra", 100: "Ballena"
}

DIAS = {0: "LUNES", 1: "MARTES", 2: "MIÉRCOLES", 3: "JUEVES", 4: "VIERNES", 5: "SÁBADO", 6: "DOMINGO"}


def fmt_num(n):
    if n == 100: return "00"
    if n == 0: return "0"
    return f"{n:02d}"


def extraer_hora(hora_str):
    m = re.match(r'^(\d+):(\d+)\s*(AM|PM)$', str(hora_str).strip().upper())
    if not m: return 99
    h = int(m.group(1))
    suf = m.group(3)
    if suf == "AM":
        if h == 12: h = 0
    else:
        if h != 12: h += 12
    return h


def formatear_hora(hora_num):
    if hora_num == 0: return "12:00 AM"
    if hora_num < 12: return f"{hora_num:02d}:00 AM"
    if hora_num == 12: return "12:00 PM"
    return f"{hora_num-12:02d}:00 PM"


@st.cache_data(ttl=120)
def cargar_hoja(sheet_id, nombre):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df_raw = pd.read_csv(url, header=None)
        filas_enc = []
        for f in range(len(df_raw)):
            v = str(df_raw.iloc[f, 0]).strip().lower()
            if v == "hora":
                filas_enc.append(f)
        registros = []
        for idx, fe in enumerate(filas_enc):
            ff = filas_enc[idx + 1] if idx + 1 < len(filas_enc) else len(df_raw)
            fechas_col = {}
            for col in range(1, len(df_raw.columns)):
                v = str(df_raw.iloc[fe, col]).strip()
                if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', v):
                    try:
                        fd = pd.to_datetime(v, format="%d/%m/%Y", errors="coerce")
                        if pd.notna(fd): fechas_col[col] = fd
                    except: pass
            ffd = min(ff, fe + 13)
            for col, fd in fechas_col.items():
                for fila in range(fe + 1, ffd):
                    hv = str(df_raw.iloc[fila, 0]).strip()
                    v = str(df_raw.iloc[fila, col]).strip()
                    if not v or v.lower() == "nan" or v.lower() == "hora":
                        continue
                    m = re.search(r'\((\d+)\)', v)
                    if m:
                        ns = m.group(1)
                        n = 100 if ns == "00" else int(ns)
                        hora_n = extraer_hora(hv)
                        if hora_n == 99:
                            continue
                        registros.append({
                            "fecha_dt": fd,
                            "fecha": fd.strftime("%d/%m/%Y"),
                            "hora_num": hora_n,
                            "numero": n,
                            "loteria": nombre
                        })
        df = pd.DataFrame(registros)
        if not df.empty:
            df = df.sort_values(["fecha_dt", "hora_num"], kind="stable").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error {nombre}: {e}")
        return pd.DataFrame()


def obtener_semanas(hoy):
    """Devuelve las fechas de las últimas 3 semanas (lunes a domingo cada una)."""
    dia_semana = hoy.weekday()
    lunes_esta = hoy - timedelta(days=dia_semana)
    semanas = []
    for i in range(3):
        lunes = lunes_esta - timedelta(weeks=i)
        dias = []
        for j in range(7):
            d = lunes + timedelta(days=j)
            if d <= hoy:
                dias.append(d)
        semanas.append({
            "num": i + 1,
            "lunes": lunes,
            "dias": dias,
            "fechas_str": [d.strftime("%d/%m/%Y") for d in dias]
        })
    return semanas


def mostrar_dia(df_g, df_l, fecha_str, nombre_dia):
    g_dia = df_g[df_g["fecha"] == fecha_str]
    l_dia = df_l[df_l["fecha"] == fecha_str]
    if g_dia.empty and l_dia.empty:
        return False
    st.markdown(f"**{nombre_dia} {fecha_str}**")
    horas = set()
    for df_dia in [g_dia, l_dia]:
        if not df_dia.empty:
            horas.update(df_dia["hora_num"].unique())
    for hora_num in sorted(horas):
        lineas = []
        for df_dia, letra in [(g_dia, "G"), (l_dia, "L")]:
            if not df_dia.empty:
                fila = df_dia[df_dia["hora_num"] == hora_num]
                if not fila.empty:
                    num = int(fila.iloc[0]["numero"])
                    lineas.append(f"{fmt_num(num)} {ANIMALITOS_DICT[num]} ({letra})")
        if lineas:
            st.write(f"**{formatear_hora(hora_num)}** → {' · '.join(lineas)}")
    st.markdown("")
    return True


def analizar_semana_actual(df_g, df_l, semanas):
    """Analiza la semana actual (la primera)."""
    semana = semanas[0]
    fechas_str = semana["fechas_str"]

    g = df_g[df_g["fecha"].isin(fechas_str)]
    l = df_l[df_l["fecha"].isin(fechas_str)]

    comb = pd.concat([g, l], ignore_index=True)

    if comb.empty:
        return [], []

    conteo = Counter(comb["numero"].tolist())
    ordenados = sorted(conteo.items(), key=lambda x: x[1], reverse=True)

    return ordenados, comb


def armar_individual_y_tripleta(ordenados):
    """Da 2 individuales y 1 tripleta."""
    if len(ordenados) < 3:
        return [], []

    nums = [n for n, _ in ordenados]

    # Los 2 individuales: los más fuertes
    individuales = nums[:2]

    # La tripleta: los 3 más fuertes
    tripleta = nums[:3]

    return individuales, tripleta


def tabla_38(df_g, df_l, fechas_str):
    """Tabla de los 38 animalitos con ✅/❌ por día."""
    g = df_g[df_g["fecha"].isin(fechas_str)]
    l = df_l[df_l["fecha"].isin(fechas_str)]
    comb = pd.concat([g, l], ignore_index=True)

    tabla = {}
    for num in ANIMALITOS_DICT.keys():
        tabla[num] = {}
        for f_str in fechas_str:
            dias_apariciones = comb[(comb["numero"] == num) & (comb["fecha"] == f_str)]
            tabla[num][f_str] = len(dias_apariciones)
    return tabla


def main():
    st.title("🎯 INDIVIDUAL")
    st.caption("2 individuales + 1 tripleta · Granjita + Lotto · Semanal")

    if st.button("🔄 Recargar datos"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Leyendo las 2 loterías..."):
        df_g = cargar_hoja(GRANJITA_ID, "G")
        df_l = cargar_hoja(LOTTO_ID, "L")

    if df_g.empty or df_l.empty:
        st.error("No se pudieron cargar las loterías.")
        return

    # ÚLTIMO RESULTADO
    comb_ultimo = pd.concat([df_g, df_l], ignore_index=True)
    comb_ultimo = comb_ultimo.sort_values(["fecha_dt", "hora_num"], kind="stable")
    ultimo = comb_ultimo.iloc[-1]

    st.markdown("## 🎯 ÚLTIMO RESULTADO")
    st.markdown(f"# {fmt_num(int(ultimo['numero']))} - {ANIMALITOS_DICT[int(ultimo['numero'])]}")
    st.caption(f"📅 Fecha: {ultimo['fecha']} · 🕐 Hora: {formatear_hora(int(ultimo['hora_num']))} · 🏦 {ultimo['loteria']}")

    total_sorteos = len(comb_ultimo)
    st.info(f"📊 Data cargada: {total_sorteos} sorteos · Última actualización: {ultimo['fecha']}")

    # SEMANAS
    hoy = datetime.now().date()
    semanas = obtener_semanas(hoy)

    st.markdown("---")
    st.markdown("## 🎯 INDIVIDUALES Y TRIPLETA PARA HOY")

    ordenados_actual, comb_actual = analizar_semana_actual(df_g, df_l, semanas)

    if not ordenados_actual:
        st.warning("No hay datos suficientes esta semana.")
        return

    individuales, tripleta = armar_individual_y_tripleta(ordenados_actual)

    st.markdown("### 🎯 2 ANIMALITOS INDIVIDUALES")
    for i, num in enumerate(individuales, 1):
        veces = dict(ordenados_actual).get(num, 0)
        st.success(f"**#{i}: {fmt_num(num)} {ANIMALITOS_DICT[num]}** — {veces} apariciones esta semana")

    st.markdown("### 🎲 1 TRIPLETA")
    nombres_trip = " + ".join([f"{fmt_num(n)} {ANIMALITOS_DICT[n]}" for n in tripleta])
    st.info(f"**{nombres_trip}**")

    st.markdown("---")

    # VISTA DÍA POR DÍA (semana actual)
    st.markdown("## 📅 ANÁLISIS DÍA POR DÍA (SEMANA ACTUAL)")
    st.caption("(G) Granjita · (L) Lotto")

    for dia in semanas[0]["dias"]:
        fecha_str = dia.strftime("%d/%m/%Y")
        nombre = DIAS[dia.weekday()]
        mostrar_dia(df_g, df_l, fecha_str, nombre)

    st.markdown("---")

    # TABLA DE 38 ANIMALITOS
    st.markdown("## 📊 COMPORTAMIENTO DE LOS 38 ANIMALITOS")
    st.caption(f"Semana actual: {semanas[0]['lunes'].strftime('%d/%m')} al {hoy.strftime('%d/%m')}")

    tabla = tabla_38(df_g, df_l, semanas[0]["fechas_str"])

    # Headers
    headers = "| Animalito | " + " | ".join([DIAS[d.weekday()][:3] for d in semanas[0]["dias"]]) + " | Total |"
    st.markdown(headers)
    st.markdown("|" + "---|" * (len(semanas[0]["dias"]) + 2))

    # Ordenar por total
    totales = {num: sum(tabla[num].values()) for num in tabla}
    ordenados_tabla = sorted(totales.items(), key=lambda x: x[1], reverse=True)

    for num, total in ordenados_tabla:
        fila = f"| {fmt_num(num)} {ANIMALITOS_DICT[num]} |"
        for d in semanas[0]["dias"]:
            f_str = d.strftime("%d/%m/%Y")
            v = tabla[num][f_str]
            fila += f" {'✅' if v > 0 else '❌'} |"
        fila += f" {total} |"
        st.markdown(fila)

    st.markdown("---")

    # REFERENCIA: 2 SEMANAS ANTERIORES
    st.markdown("## 📅 REFERENCIA: SEMANAS ANTERIORES")
    st.caption("Solo para ver patrones · NO se usa para jugar")

    for i, semana in enumerate(semanas[1:], 1):
        with st.expander(f"📅 Semana hace {i} semana(s) — {semana['lunes'].strftime('%d/%m')} al {(semana['lunes'] + timedelta(days=6)).strftime('%d/%m')}"):
            fechas_str = semana["fechas_str"]
            g = df_g[df_g["fecha"].isin(fechas_str)]
            l = df_l[df_l["fecha"].isin(fechas_str)]
            comb_sem = pd.concat([g, l], ignore_index=True)

            if comb_sem.empty:
                st.write("Sin datos")
                continue

            conteo = Counter(comb_sem["numero"].tolist())
            top10 = sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:10]
            for num, veces in top10:
                st.write(f"- **{fmt_num(num)} {ANIMALITOS_DICT[num]}** — {veces} veces")

    st.markdown("---")
    st.caption("🎯 2 individuales + 1 tripleta · Basado en la semana actual")


if __name__ == "__main__":
    main()
