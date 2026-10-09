import streamlit as st
import pandas as pd
import re
from collections import Counter
from datetime import datetime, timedelta

st.set_page_config(
    page_title="INDIVIDUAL",
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

HORAS_RANGO = list(range(8, 20))  # 8 AM a 7 PM


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


def obtener_semana_actual(hoy):
    dia_semana = hoy.weekday()
    lunes = hoy - timedelta(days=dia_semana)
    dias = []
    for j in range(7):
        d = lunes + timedelta(days=j)
        if d <= hoy:
            dias.append(d)
    return dias


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


def analizar_semana(df_g, df_l, dias_semana):
    """Analiza toda la semana: cuántas veces salió cada animalito."""
    fechas_str = [d.strftime("%d/%m/%Y") for d in dias_semana]
    g = df_g[df_g["fecha"].isin(fechas_str)]
    l = df_l[df_l["fecha"].isin(fechas_str)]
    comb = pd.concat([g, l], ignore_index=True)

    if comb.empty:
        return Counter(), comb

    conteo = Counter(comb["numero"].tolist())
    return conteo, comb


def elegir_por_hora(df_g, df_l, dias_semana, conteo_semana, hora):
    """Elige los animalitos para una hora específica."""
    fechas_str = [d.strftime("%d/%m/%Y") for d in dias_semana]

    # Filtrar por hora
    g_h = df_g[(df_g["fecha"].isin(fechas_str)) & (df_g["hora_num"] == hora)]
    l_h = df_l[(df_l["fecha"].isin(fechas_str)) & (df_l["hora_num"] == hora)]
    comb_h = pd.concat([g_h, l_h], ignore_index=True)

    if comb_h.empty:
        # Si no hay data de esa hora, usar los más activos de la semana
        top = [n for n, _ in conteo_semana.most_common(2)]
        return top, "Sin data de esta hora — usando los más activos de la semana"

    # Contar cuántas veces salió cada uno en esa hora
    conteo_hora = Counter(comb_h["numero"].tolist())

    # Combinar: cuántas veces en esa hora + cuántas veces en la semana (para darle peso)
    scores = {}
    for num in ANIMALITOS_DICT.keys():
        v_hora = conteo_hora.get(num, 0)
        v_semana = conteo_semana.get(num, 0)
        # Peso: 70% hora específica + 30% semana
        scores[num] = v_hora * 3 + v_semana * 0.5

    ordenados = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top = [n for n, _ in ordenados[:3] if scores[n] > 0]

    if not top:
        top = [n for n, _ in conteo_semana.most_common(2)]

    # Decidir cuántos dar
    # Si el #1 tiene mucho más que el #2 → 1 solo (muy fuerte)
    if len(top) >= 2:
        s1 = scores.get(top[0], 0)
        s2 = scores.get(top[1], 0)
        if s1 >= s2 * 1.8 and s1 >= 4:  # Muy fuerte
            return [top[0]], f"🔥 {fmt_num(top[0])} {ANIMALITOS_DICT[top[0]]} MUY FUERTE a esta hora"
        elif len(top) >= 3:
            s3 = scores.get(top[2], 0)
            if s3 >= s2 * 0.9 and s3 >= 3:
                return top[:3], f"3 animalitos con buen patrón"
        return top[:2], "2 animalitos con buen patrón"

    return top[:2], "2 animalitos"


def main():
    st.title("🎯 INDIVIDUAL")
    st.caption("2 animalitos por hora · Granjita + Lotto · Análisis semanal")

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

    # SEMANA ACTUAL
    hoy = datetime.now().date()
    dias_semana = obtener_semana_actual(hoy)

    st.markdown("---")
    st.markdown("## 🎯 ANIMALITOS POR HORA — HOY")

    conteo_semana, comb_semana = analizar_semana(df_g, df_l, dias_semana)

    if not conteo_semana:
        st.warning("No hay datos esta semana.")
        return

    # Para cada hora, elegir
    for hora in HORAS_RANGO:
        elegidos, razon = elegir_por_hora(df_g, df_l, dias_semana, conteo_semana, hora)
        hora_str = formatear_hora(hora)

        if len(elegidos) == 1:
            num = elegidos[0]
            st.success(f"**🕐 {hora_str}** → 🔥 **{fmt_num(num)} {ANIMALITOS_DICT[num]}** (1 solo — MUY FUERTE)")
        elif len(elegidos) == 3:
            linea = " + ".join([f"{fmt_num(n)} {ANIMALITOS_DICT[n]}" for n in elegidos])
            st.warning(f"**🕐 {hora_str}** → **{linea}** (3 animalitos)")
        else:
            linea = " + ".join([f"{fmt_num(n)} {ANIMALITOS_DICT[n]}" for n in elegidos])
            st.info(f"**🕐 {hora_str}** → **{linea}**")

    st.markdown("---")

    # VISTA DÍA POR DÍA
    st.markdown("## 📅 ANÁLISIS DÍA POR DÍA (SEMANA ACTUAL)")
    st.caption("(G) Granjita · (L) Lotto")

    for dia in dias_semana:
        fecha_str = dia.strftime("%d/%m/%Y")
        nombre = DIAS[dia.weekday()]
        mostrar_dia(df_g, df_l, fecha_str, nombre)

    st.markdown("---")

    # TABLA DE 38 ANIMALITOS
    st.markdown("## 📊 COMPORTAMIENTO DE LOS 38 ANIMALITOS")
    st.caption(f"Semana: {dias_semana[0].strftime('%d/%m')} al {dias_semana[-1].strftime('%d/%m')}")

    fechas_str = [d.strftime("%d/%m/%Y") for d in dias_semana]

    # Headers
    headers = "| Animalito | " + " | ".join([DIAS[d.weekday()][:3] for d in dias_semana]) + " | Total |"
    st.markdown(headers)
    st.markdown("|" + "---|" * (len(dias_semana) + 2))

    totales = {}
    for num in ANIMALITOS_DICT.keys():
        totales[num] = conteo_semana.get(num, 0)

    ordenados_tabla = sorted(totales.items(), key=lambda x: x[1], reverse=True)

    for num, total in ordenados_tabla:
        fila = f"| {fmt_num(num)} {ANIMALITOS_DICT[num]} |"
        for d in dias_semana:
            f_str = d.strftime("%d/%m/%Y")
            g_d = df_g[(df_g["fecha"] == f_str) & (df_g["numero"] == num)]
            l_d = df_l[(df_l["fecha"] == f_str) & (df_l["numero"] == num)]
            v = len(g_d) + len(l_d)
            fila += f" {'✅' if v > 0 else '❌'} |"
        fila += f" {total} |"
        st.markdown(fila)

    st.markdown("---")
    st.caption("🎯 Análisis por hora · Granjita + Lotto · Semana actual")


if __name__ == "__main__":
    main()
