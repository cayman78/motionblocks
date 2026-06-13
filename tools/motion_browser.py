"""
MotionBlocks — Motion Browser
tools/motion_browser.py

Запуск:
    streamlit run tools/motion_browser.py

Назначение:
    Обзор коллекции записей и просмотр сигналов внутри отдельных сессий.

Режимы:
    1. Обзор    — таблица экспериментов и сессий, агрегированная статистика
    2. Просмотр — графики сигналов для выбранной сессии
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# ------------------------------------------------------------
# Конфигурация
# ------------------------------------------------------------

METADATA_DIR   = Path("data/metadata")
RAW_DIR        = Path("data/raw")
EXPERIMENTS_PATH      = METADATA_DIR / "experiments.json"
RECORDING_SESSIONS_PATH = METADATA_DIR / "recording_sessions.json"


# ------------------------------------------------------------
# Загрузка данных
# ------------------------------------------------------------

@st.cache_data
def load_experiments() -> pd.DataFrame:
    if not EXPERIMENTS_PATH.exists():
        return pd.DataFrame()

    data = json.loads(EXPERIMENTS_PATH.read_text(encoding="utf-8"))
    df = pd.DataFrame(data)

    # Оставляем только нужные колонки для отображения
    cols = ["experiment_id", "short_name", "title", "status",
            "started_at", "location", "participants", "tags"]
    cols = [c for c in cols if c in df.columns]
    return df[cols]


@st.cache_data
def load_sessions() -> pd.DataFrame:
    if not RECORDING_SESSIONS_PATH.exists():
        return pd.DataFrame()

    data = json.loads(RECORDING_SESSIONS_PATH.read_text(encoding="utf-8"))
    df = pd.DataFrame(data)
    return df


@st.cache_data
def load_csv(file_path: str) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


# ------------------------------------------------------------
# Вспомогательные функции
# ------------------------------------------------------------

def count_data_rows(file_path: str) -> int:
    """Посчитать количество DATA строк в CSV файле."""
    df = load_csv(file_path)
    if df.empty:
        return 0
    if "row_type" in df.columns:
        return int((df["row_type"] == "DATA").sum())
    return len(df)


def get_file_size_kb(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        return "—"
    return f"{path.stat().st_size / 1024:.1f} KB"


def status_badge(status: str) -> str:
    """Превратить статус в читаемый текст с эмодзи."""
    if status == "raw":
        return "🟡 raw"
    if status == "auto created. needs description.":
        return "🔴 needs description"
    if status == "checked":
        return "🟢 checked"
    if status == "bad":
        return "⛔ bad"
    return status


# ------------------------------------------------------------
# Страница: Обзор коллекции
# ------------------------------------------------------------

def page_overview(sessions_df: pd.DataFrame, experiments_df: pd.DataFrame):
    st.header("Коллекция записей")

    if sessions_df.empty:
        st.warning("Файл recording_sessions.json не найден или пустой.")
        return

    # --- Агрегат по экспериментам ---
    st.subheader("Эксперименты")

    exp_agg = (
        sessions_df.groupby("experiment_id")
        .agg(
            сессий=("session_uid", "count") if "session_uid" in sessions_df.columns
                   else ("session_id", "count"),
            движений=("movement_type", lambda x: x[x != "unknown"].nunique()),
            частота_гц=("sample_rate_hz", lambda x: ", ".join(
                sorted(set(str(int(v)) for v in x.dropna()))
            )),
        )
        .reset_index()
    )

    # Добавляем short_name из experiments.json если есть
    if not experiments_df.empty and "experiment_id" in experiments_df.columns:
        exp_agg = exp_agg.merge(
            experiments_df[["experiment_id", "short_name", "status"]].rename(
                columns={"status": "статус_эксп"}
            ),
            on="experiment_id",
            how="left",
        )

    st.dataframe(exp_agg, use_container_width=True, hide_index=True)

    st.divider()

    # --- Фильтры ---
    st.subheader("Сессии")

    col1, col2, col3 = st.columns(3)

    with col1:
        exp_options = ["Все"] + sorted(sessions_df["experiment_id"].unique().tolist())
        selected_exp = st.selectbox("Эксперимент", exp_options)

    with col2:
        movement_options = ["Все"] + sorted(
            sessions_df["movement_type"].dropna().unique().tolist()
        )
        selected_movement = st.selectbox("Тип движения", movement_options)

    with col3:
        status_options = ["Все"] + sorted(
            sessions_df["status"].dropna().unique().tolist()
        )
        selected_status = st.selectbox("Статус", status_options)

    # Применяем фильтры
    filtered = sessions_df.copy()

    if selected_exp != "Все":
        filtered = filtered[filtered["experiment_id"] == selected_exp]

    if selected_movement != "Все":
        filtered = filtered[filtered["movement_type"] == selected_movement]

    if selected_status != "Все":
        filtered = filtered[filtered["status"] == selected_status]

    # Колонки для таблицы
    display_cols = []
    for col in ["experiment_id", "session_uid", "device_id", "recording_run_id",
                "device_session_id", "session_id", "movement_type", "movement_label",
                "subject_id", "sample_rate_hz", "started_at", "status", "file_name"]:
        if col in filtered.columns:
            display_cols.append(col)

    st.dataframe(
        filtered[display_cols].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(f"Показано {len(filtered)} из {len(sessions_df)} сессий")


# ------------------------------------------------------------
# Страница: Просмотр сессии
# ------------------------------------------------------------

def page_session_viewer(sessions_df: pd.DataFrame):
    st.header("Просмотр сессии")

    if sessions_df.empty:
        st.warning("Нет данных.")
        return

    # Выбор сессии
    # Строим читаемый лейбл для selectbox
    def session_label(row) -> str:
        uid = row.get("session_uid") or row.get("session_id", "?")
        movement = row.get("movement_type", "?")
        rate = row.get("sample_rate_hz", "?")
        fname = row.get("file_name", "?")
        return f"{uid}  |  {movement}  |  {rate}Hz  |  {fname}"

    labels = sessions_df.apply(session_label, axis=1).tolist()
    selected_label = st.selectbox("Выбери сессию", labels)

    if not selected_label:
        return

    selected_idx = labels.index(selected_label)
    session = sessions_df.iloc[selected_idx]

    # --- Карточка сессии ---
    st.subheader("Информация о сессии")

    info_cols = st.columns(3)

    with info_cols[0]:
        st.metric("Эксперимент", session.get("experiment_id", "—"))
        st.metric("Устройство", session.get("device_id", "—"))
        st.metric("Частота", f"{session.get('sample_rate_hz', '—')} Hz")

    with info_cols[1]:
        st.metric("Движение", session.get("movement_type", "—"))
        st.metric("Субъект", session.get("subject_id", "—"))
        st.metric("Статус", session.get("status", "—"))

    with info_cols[2]:
        st.metric("Файл", session.get("file_name", "—"))
        if "recording_run_id" in session:
            st.metric("Run ID", session.get("recording_run_id", "—"))
        st.metric("Дата", str(session.get("started_at", "—"))[:10])

    if session.get("comment"):
        st.info(f"Комментарий: {session['comment']}")

    st.divider()

    # --- Загрузка CSV ---
    file_path = session.get("file_path", "")

    if not file_path:
        st.warning("Путь к файлу не указан в metadata.")
        return

    df = load_csv(file_path)

    if df.empty:
        st.error(f"Файл не найден или пустой: `{file_path}`")
        return

    # Разделяем EVENT и DATA строки
    if "row_type" in df.columns:
        data_df   = df[df["row_type"] == "DATA"].copy()
        events_df = df[df["row_type"] == "EVENT"].copy()
    else:
        data_df   = df.copy()
        events_df = pd.DataFrame()

    if data_df.empty:
        st.warning("В файле нет DATA строк.")
        return

    # Числовые колонки
    for col in ["device_timestamp_ms", "ax", "ay", "az", "gx", "gy", "gz", "acc_norm"]:
        if col in data_df.columns:
            data_df[col] = pd.to_numeric(data_df[col], errors="coerce")

    # Базовая статистика
    st.subheader("Статистика записи")

    stat_cols = st.columns(4)

    total_samples = len(data_df)
    records = data_df["record_id"].nunique() if "record_id" in data_df.columns else "—"

    with stat_cols[0]:
        st.metric("Сэмплов", total_samples)

    with stat_cols[1]:
        st.metric("Записей (record_id)", records)

    with stat_cols[2]:
        if "device_timestamp_ms" in data_df.columns:
            t = data_df["device_timestamp_ms"].dropna()
            if len(t) > 1:
                duration = (t.max() - t.min()) / 1000
                st.metric("Длительность", f"{duration:.1f} s")
        else:
            st.metric("Длительность", "—")

    with stat_cols[3]:
        if "device_timestamp_ms" in data_df.columns:
            t = data_df["device_timestamp_ms"].dropna().sort_values()
            if len(t) > 1:
                dt = t.diff().dropna()
                effective_hz = 1000 / dt.mean()
                st.metric("Эффективная частота", f"{effective_hz:.1f} Hz")
        else:
            st.metric("Эффективная частота", "—")

    st.divider()

    # --- Графики ---
    st.subheader("Графики")

    # Выбор что показывать
    chart_options = st.multiselect(
        "Показать графики",
        options=["acc_norm", "ax / ay / az", "gx / gy / gz", "dt_ms"],
        default=["acc_norm", "ax / ay / az"],
    )

    # Разбивка по record_id
    show_records = st.checkbox("Разделять по record_id", value=True)

    if "device_timestamp_ms" in data_df.columns:
        x_col = "device_timestamp_ms"
        x_label = "Время (ms)"
        # Нормируем время от нуля для каждой записи если нужно
        if show_records and "record_id" in data_df.columns:
            data_df = data_df.copy()
            data_df["t_rel_ms"] = data_df.groupby("record_id")["device_timestamp_ms"].transform(
                lambda x: x - x.min()
            )
            x_col = "t_rel_ms"
            x_label = "Время от начала записи (ms)"
    else:
        data_df["_idx"] = range(len(data_df))
        x_col = "_idx"
        x_label = "Индекс сэмпла"

    record_ids = sorted(data_df["record_id"].unique()) if "record_id" in data_df.columns else [None]

    for chart_name in chart_options:

        if chart_name == "acc_norm" and "acc_norm" in data_df.columns:
            fig, ax = plt.subplots(figsize=(12, 3))
            ax.set_title("acc_norm (норма ускорения)")
            ax.set_xlabel(x_label)
            ax.set_ylabel("g")
            ax.axhline(1.0, color="grey", linewidth=0.8, linestyle="--", label="1g (покой)")

            if show_records and "record_id" in data_df.columns:
                for rid in record_ids:
                    sub = data_df[data_df["record_id"] == rid]
                    ax.plot(sub[x_col], sub["acc_norm"], linewidth=0.8, label=f"R{rid}")
                ax.legend(fontsize=7)
            else:
                ax.plot(data_df[x_col], data_df["acc_norm"], linewidth=0.8, color="steelblue")

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        if chart_name == "ax / ay / az":
            available = [c for c in ["ax", "ay", "az"] if c in data_df.columns]
            if available:
                fig, ax = plt.subplots(figsize=(12, 3))
                ax.set_title("Акселерометр (ax / ay / az)")
                ax.set_xlabel(x_label)
                ax.set_ylabel("g")
                colors = {"ax": "tomato", "ay": "steelblue", "az": "seagreen"}

                if show_records and "record_id" in data_df.columns:
                    for rid in record_ids:
                        sub = data_df[data_df["record_id"] == rid]
                        for ch in available:
                            ax.plot(sub[x_col], sub[ch], linewidth=0.8,
                                    color=colors.get(ch), alpha=0.8,
                                    label=f"{ch}/R{rid}" if rid == record_ids[0] else "")
                else:
                    for ch in available:
                        ax.plot(data_df[x_col], data_df[ch], linewidth=0.8,
                                color=colors.get(ch), label=ch)

                ax.legend(fontsize=7)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

        if chart_name == "gx / gy / gz":
            available = [c for c in ["gx", "gy", "gz"] if c in data_df.columns]
            if available:
                fig, ax = plt.subplots(figsize=(12, 3))
                ax.set_title("Гироскоп (gx / gy / gz)")
                ax.set_xlabel(x_label)
                ax.set_ylabel("deg/s")
                colors = {"gx": "tomato", "gy": "steelblue", "gz": "seagreen"}

                if show_records and "record_id" in data_df.columns:
                    for rid in record_ids:
                        sub = data_df[data_df["record_id"] == rid]
                        for ch in available:
                            ax.plot(sub[x_col], sub[ch], linewidth=0.8,
                                    color=colors.get(ch), alpha=0.8)
                else:
                    for ch in available:
                        ax.plot(data_df[x_col], data_df[ch], linewidth=0.8,
                                color=colors.get(ch), label=ch)

                ax.legend(fontsize=7)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

        if chart_name == "dt_ms" and "device_timestamp_ms" in data_df.columns:
            fig, ax = plt.subplots(figsize=(12, 3))
            ax.set_title("dt_ms (интервал между сэмплами)")
            ax.set_xlabel("Индекс сэмпла")
            ax.set_ylabel("ms")

            configured_hz = session.get("sample_rate_hz")
            if configured_hz:
                expected_dt = 1000 / configured_hz
                ax.axhline(expected_dt, color="grey", linewidth=0.8,
                           linestyle="--", label=f"ожидаемый {expected_dt:.0f}ms")

            if show_records and "record_id" in data_df.columns:
                for rid in record_ids:
                    sub = data_df[data_df["record_id"] == rid].copy()
                    sub["dt"] = sub["device_timestamp_ms"].diff()
                    ax.plot(sub["dt"].values, linewidth=0.8, label=f"R{rid}")
                ax.legend(fontsize=7)
            else:
                dt = data_df["device_timestamp_ms"].diff()
                ax.plot(dt.values, linewidth=0.8, color="steelblue")

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    # --- Сырые данные ---
    with st.expander("Сырые данные (первые 100 строк)"):
        st.dataframe(df.head(100), use_container_width=True)


# ------------------------------------------------------------
# Главная функция
# ------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="MotionBlocks Browser",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 MotionBlocks Browser")
    st.caption("Stofendez Lab")

    # Загружаем данные
    experiments_df = load_experiments()
    sessions_df    = load_sessions()

    # Навигация
    page = st.sidebar.radio(
        "Режим",
        ["🗂 Обзор коллекции", "📈 Просмотр сессии"],
    )

    st.sidebar.divider()
    st.sidebar.caption(f"Экспериментов: {len(experiments_df)}")
    st.sidebar.caption(f"Сессий: {len(sessions_df)}")
    st.sidebar.caption(f"Данные: {RAW_DIR}")

    if page == "🗂 Обзор коллекции":
        page_overview(sessions_df, experiments_df)
    else:
        page_session_viewer(sessions_df)


if __name__ == "__main__":
    main()
