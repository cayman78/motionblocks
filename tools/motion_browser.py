"""
MotionBlocks — Motion Browser v2
tools/motion_browser.py

Запуск:
    streamlit run tools/motion_browser.py

Режимы:
    1. Обзор        — таблица экспериментов и сессий
    2. Просмотр     — графики сигналов для выбранной сессии
    3. Редактор     — редактирование полей сессии / эксперимента
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# ------------------------------------------------------------
# Конфигурация
# ------------------------------------------------------------

METADATA_DIR            = Path("data/metadata")
RAW_DIR                 = Path("data/raw")
EXPERIMENTS_PATH        = METADATA_DIR / "experiments.json"
SESSIONS_PATH           = METADATA_DIR / "recording_sessions.json"
SUBJECTS_PATH           = METADATA_DIR / "subjects.json"

STATUS_OPTIONS = ["draft", "raw", "checked", "bad", "archived"]

MOVEMENT_TYPE_OPTIONS = [
    "unknown", "idle", "walking", "running", "jumping",
    "shaking", "stairs_up", "stairs_down", "falling_like",
    "sitting_down", "standing_up", "device_test",
]

WRIST_OPTIONS = ["left", "right", "unknown"]

SUBJECT_OPTIONS_DEFAULT = ["unknown", "child_01", "child_02", "adult_01", "mentor_01"]


# ------------------------------------------------------------
# Загрузка / сохранение JSON
# ------------------------------------------------------------

def load_json_list(path: Path) -> list:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    return json.loads(text)


def save_json_list(path: Path, data: list) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@st.cache_data
def load_experiments_cached() -> list:
    return load_json_list(EXPERIMENTS_PATH)


@st.cache_data
def load_sessions_cached() -> list:
    return load_json_list(SESSIONS_PATH)


@st.cache_data
def load_subjects_cached() -> list:
    return load_json_list(SUBJECTS_PATH)


@st.cache_data
def load_csv(file_path: str) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def reload_all():
    """Сбросить кэш и перечитать все файлы."""
    st.cache_data.clear()


# ------------------------------------------------------------
# Вспомогательные функции
# ------------------------------------------------------------

def status_emoji(status: str) -> str:
    return {
        "draft":    "🔴 draft",
        "raw":      "🟡 raw",
        "checked":  "🟢 checked",
        "bad":      "⛔ bad",
        "archived": "📦 archived",
    }.get(status, status)


def get_subject_ids() -> list[str]:
    subjects = load_subjects_cached()
    ids = [s.get("subject_id", "") for s in subjects if s.get("subject_id")]
    return sorted(ids) if ids else SUBJECT_OPTIONS_DEFAULT


def sessions_to_df(sessions: list) -> pd.DataFrame:
    if not sessions:
        return pd.DataFrame()
    return pd.DataFrame(sessions)


def experiments_to_df(experiments: list) -> pd.DataFrame:
    if not experiments:
        return pd.DataFrame()
    return pd.DataFrame(experiments)


# ------------------------------------------------------------
# Страница: Обзор коллекции
# ------------------------------------------------------------

def page_overview():
    st.header("Коллекция записей")

    experiments = load_experiments_cached()
    sessions    = load_sessions_cached()

    if not sessions:
        st.warning("Файл recording_sessions.json не найден или пустой.")
        return

    sessions_df    = sessions_to_df(sessions)
    experiments_df = experiments_to_df(experiments)

    # --- Таблица экспериментов ---
    st.subheader("Эксперименты")

    exp_agg = (
        sessions_df.groupby("experiment_id")
        .agg(
            сессий=("session_uid", "count") if "session_uid" in sessions_df.columns
                   else ("device_session_id", "count"),
            движений=("movement_type", lambda x: x[x != "unknown"].nunique()),
            гц=("sample_rate_hz", lambda x: ", ".join(
                sorted(set(str(int(v)) for v in x.dropna()))
            )),
            draft=("status", lambda x: (x == "draft").sum()),
            checked=("status", lambda x: (x == "checked").sum()),
        )
        .reset_index()
    )

    if not experiments_df.empty and "experiment_id" in experiments_df.columns:
        exp_meta = experiments_df[
            ["experiment_id", "short_name", "title", "location", "status"]
        ].rename(columns={"status": "статус"})
        exp_agg = exp_agg.merge(exp_meta, on="experiment_id", how="left")

    st.dataframe(exp_agg, use_container_width=True, hide_index=True)

    st.divider()

    # --- Фильтры сессий ---
    st.subheader("Сессии")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        exp_options = ["Все"] + sorted(sessions_df["experiment_id"].unique().tolist())
        selected_exp = st.selectbox("Эксперимент", exp_options)

    with col2:
        movement_vals = sessions_df["movement_type"].dropna().unique().tolist()
        movement_options = ["Все"] + sorted(movement_vals)
        selected_movement = st.selectbox("Движение", movement_options)

    with col3:
        status_vals = sessions_df["status"].dropna().unique().tolist()
        status_options = ["Все"] + sorted(status_vals)
        selected_status = st.selectbox("Статус", status_options)

    with col4:
        subject_vals = sessions_df["subject_id"].dropna().unique().tolist() \
            if "subject_id" in sessions_df.columns else []
        subject_options = ["Все"] + sorted(subject_vals)
        selected_subject = st.selectbox("Субъект", subject_options)

    # Применяем фильтры
    filtered = sessions_df.copy()
    if selected_exp      != "Все": filtered = filtered[filtered["experiment_id"] == selected_exp]
    if selected_movement != "Все": filtered = filtered[filtered["movement_type"] == selected_movement]
    if selected_status   != "Все": filtered = filtered[filtered["status"] == selected_status]
    if selected_subject  != "Все" and "subject_id" in filtered.columns:
        filtered = filtered[filtered["subject_id"] == selected_subject]

    # Колонки для таблицы
    display_cols = [c for c in [
        "experiment_id", "session_uid", "device_id", "recording_run_id",
        "device_session_id", "movement_type", "movement_label",
        "subject_id", "wrist", "sample_rate_hz", "started_at", "status", "file_name",
    ] if c in filtered.columns]

    st.dataframe(
        filtered[display_cols].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(f"Показано {len(filtered)} из {len(sessions_df)} сессий")

    # --- Удаление эксперимента ---
    st.divider()
    with st.expander("⚠️ Удалить эксперимент"):
        if experiments:
            exp_to_delete = st.selectbox(
                "Выбери эксперимент для удаления",
                [e["experiment_id"] for e in experiments],
                key="del_exp_select",
            )
            st.warning(
                f"Удалит запись **{exp_to_delete}** из experiments.json. "
                "CSV файлы не удаляются."
            )
            if st.button("Удалить эксперимент", type="primary", key="del_exp_btn"):
                new_experiments = [e for e in experiments
                                   if e["experiment_id"] != exp_to_delete]
                save_json_list(EXPERIMENTS_PATH, new_experiments)
                reload_all()
                st.success(f"Эксперимент {exp_to_delete} удалён.")
                st.rerun()


# ------------------------------------------------------------
# Страница: Просмотр сессии
# ------------------------------------------------------------

def page_session_viewer():
    st.header("Просмотр сессии")

    sessions = load_sessions_cached()
    if not sessions:
        st.warning("Нет данных.")
        return

    sessions_df = sessions_to_df(sessions)

    def session_label(row) -> str:
        uid      = row.get("session_uid") or row.get("device_session_id", "?")
        movement = row.get("movement_type", "?")
        rate     = row.get("sample_rate_hz", "?")
        status   = row.get("status", "?")
        return f"{uid}  |  {movement}  |  {rate}Hz  |  {status_emoji(status)}"

    labels = sessions_df.apply(session_label, axis=1).tolist()
    selected_label = st.selectbox("Выбери сессию", labels)

    if not selected_label:
        return

    idx     = labels.index(selected_label)
    session = sessions_df.iloc[idx].to_dict()

    # --- Карточка ---
    st.subheader("Информация о сессии")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Эксперимент",  session.get("experiment_id", "—"))
        st.metric("Устройство",   session.get("device_id", "—"))
        st.metric("Частота",      f"{session.get('sample_rate_hz', '—')} Hz")
    with c2:
        st.metric("Движение",     session.get("movement_type", "—"))
        st.metric("Субъект",      session.get("subject_id", "—"))
        st.metric("Запястье",     session.get("wrist", "—"))
    with c3:
        st.metric("Статус",       status_emoji(session.get("status", "—")))
        st.metric("Run ID",       session.get("recording_run_id", "—"))
        st.metric("Файл",         session.get("file_name", "—"))

    if session.get("comment"):
        st.info(f"💬 {session['comment']}")

    st.divider()

    # --- CSV ---
    file_path = session.get("file_path", "")
    if not file_path:
        st.warning("Путь к файлу не указан в metadata.")
        return

    df = load_csv(file_path)
    if df.empty:
        st.error(f"Файл не найден или пустой: `{file_path}`")
        return

    if "row_type" in df.columns:
        data_df = df[df["row_type"] == "DATA"].copy()
    else:
        data_df = df.copy()

    if data_df.empty:
        st.warning("В файле нет DATA строк.")
        return

    for col in ["device_timestamp_ms", "ax", "ay", "az", "gx", "gy", "gz", "acc_norm"]:
        if col in data_df.columns:
            data_df[col] = pd.to_numeric(data_df[col], errors="coerce")

    # --- Статистика ---
    st.subheader("Статистика")

    s1, s2, s3, s4 = st.columns(4)

    with s1:
        st.metric("Сэмплов", len(data_df))
    with s2:
        records = data_df["record_id"].nunique() if "record_id" in data_df.columns else "—"
        st.metric("Записей", records)
    with s3:
        if "device_timestamp_ms" in data_df.columns:
            t = data_df["device_timestamp_ms"].dropna()
            if len(t) > 1:
                st.metric("Длительность", f"{(t.max()-t.min())/1000:.1f} s")
        else:
            st.metric("Длительность", "—")
    with s4:
        if "device_timestamp_ms" in data_df.columns:
            t = data_df["device_timestamp_ms"].dropna().sort_values()
            if len(t) > 1:
                st.metric("Эфф. частота", f"{1000/t.diff().dropna().mean():.1f} Hz")
        else:
            st.metric("Эфф. частота", "—")

    st.divider()

    # --- Графики ---
    st.subheader("Графики")

    chart_options = st.multiselect(
        "Показать",
        options=["acc_norm", "ax / ay / az", "gx / gy / gz", "dt_ms"],
        default=["acc_norm", "ax / ay / az"],
    )

    show_records = st.checkbox("Разделять по record_id", value=True)

    if "device_timestamp_ms" in data_df.columns:
        if show_records and "record_id" in data_df.columns:
            data_df["t_rel_ms"] = data_df.groupby("record_id")["device_timestamp_ms"].transform(
                lambda x: x - x.min()
            )
            x_col, x_label = "t_rel_ms", "Время от начала записи (ms)"
        else:
            x_col, x_label = "device_timestamp_ms", "Время (ms)"
    else:
        data_df["_idx"] = range(len(data_df))
        x_col, x_label = "_idx", "Индекс сэмпла"

    record_ids = sorted(data_df["record_id"].unique()) \
        if "record_id" in data_df.columns else [None]

    for chart in chart_options:

        if chart == "acc_norm" and "acc_norm" in data_df.columns:
            fig, ax = plt.subplots(figsize=(12, 3))
            ax.set_title("acc_norm")
            ax.set_xlabel(x_label); ax.set_ylabel("g")
            ax.axhline(1.0, color="grey", lw=0.8, ls="--", label="1g")
            if show_records and "record_id" in data_df.columns:
                for rid in record_ids:
                    sub = data_df[data_df["record_id"] == rid]
                    ax.plot(sub[x_col], sub["acc_norm"], lw=0.8, label=f"R{rid}")
                ax.legend(fontsize=7)
            else:
                ax.plot(data_df[x_col], data_df["acc_norm"], lw=0.8, color="steelblue")
            plt.tight_layout(); st.pyplot(fig); plt.close(fig)

        if chart == "ax / ay / az":
            avail = [c for c in ["ax", "ay", "az"] if c in data_df.columns]
            if avail:
                fig, ax = plt.subplots(figsize=(12, 3))
                ax.set_title("Акселерометр"); ax.set_xlabel(x_label); ax.set_ylabel("g")
                colors = {"ax": "tomato", "ay": "steelblue", "az": "seagreen"}
                if show_records and "record_id" in data_df.columns:
                    for rid in record_ids:
                        sub = data_df[data_df["record_id"] == rid]
                        for ch in avail:
                            ax.plot(sub[x_col], sub[ch], lw=0.8,
                                    color=colors[ch], alpha=0.8,
                                    label=ch if rid == record_ids[0] else "")
                else:
                    for ch in avail:
                        ax.plot(data_df[x_col], data_df[ch], lw=0.8,
                                color=colors[ch], label=ch)
                ax.legend(fontsize=7); plt.tight_layout(); st.pyplot(fig); plt.close(fig)

        if chart == "gx / gy / gz":
            avail = [c for c in ["gx", "gy", "gz"] if c in data_df.columns]
            if avail:
                fig, ax = plt.subplots(figsize=(12, 3))
                ax.set_title("Гироскоп"); ax.set_xlabel(x_label); ax.set_ylabel("deg/s")
                colors = {"gx": "tomato", "gy": "steelblue", "gz": "seagreen"}
                if show_records and "record_id" in data_df.columns:
                    for rid in record_ids:
                        sub = data_df[data_df["record_id"] == rid]
                        for ch in avail:
                            ax.plot(sub[x_col], sub[ch], lw=0.8, color=colors[ch], alpha=0.8)
                else:
                    for ch in avail:
                        ax.plot(data_df[x_col], data_df[ch], lw=0.8,
                                color=colors[ch], label=ch)
                ax.legend(fontsize=7); plt.tight_layout(); st.pyplot(fig); plt.close(fig)

        if chart == "dt_ms" and "device_timestamp_ms" in data_df.columns:
            fig, ax = plt.subplots(figsize=(12, 3))
            ax.set_title("dt_ms"); ax.set_xlabel("Индекс сэмпла"); ax.set_ylabel("ms")
            hz = session.get("sample_rate_hz")
            if hz:
                ax.axhline(1000/hz, color="grey", lw=0.8, ls="--",
                           label=f"ожидаемый {1000/hz:.0f}ms")
            if show_records and "record_id" in data_df.columns:
                for rid in record_ids:
                    sub = data_df[data_df["record_id"] == rid].copy()
                    sub["dt"] = sub["device_timestamp_ms"].diff()
                    ax.plot(sub["dt"].values, lw=0.8, label=f"R{rid}")
                ax.legend(fontsize=7)
            else:
                ax.plot(data_df["device_timestamp_ms"].diff().values, lw=0.8, color="steelblue")
            plt.tight_layout(); st.pyplot(fig); plt.close(fig)

    with st.expander("Сырые данные (первые 100 строк)"):
        st.dataframe(df.head(100), use_container_width=True)


# ------------------------------------------------------------
# Страница: Редактор
# ------------------------------------------------------------

def page_editor():
    st.header("Редактор метаданных")

    sessions = load_json_list(SESSIONS_PATH)
    if not sessions:
        st.warning("Нет данных.")
        return

    subject_ids = get_subject_ids()

    # --- Выбор сессии ---
    def session_label(s: dict) -> str:
        uid      = s.get("session_uid") or s.get("device_session_id", "?")
        movement = s.get("movement_type", "?")
        status   = s.get("status", "?")
        return f"{uid}  |  {movement}  |  {status_emoji(status)}"

    labels = [session_label(s) for s in sessions]
    selected_label = st.selectbox("Выбери сессию для редактирования", labels)
    idx = labels.index(selected_label)
    session = sessions[idx]

    st.divider()

    st.subheader("Редактировать поля")
    st.caption(f"session_uid: `{session.get('session_uid', '?')}`  |  файл: `{session.get('file_name', '?')}`")

    col1, col2 = st.columns(2)

    with col1:
        # movement_type — свободный ввод + подсказки из списка
        mt_current = session.get("movement_type", "unknown")
        new_movement_type = st.text_input(
            "movement_type",
            value=mt_current,
            help="Введи вручную или выбери из подсказок ниже",
        )
        mt_suggestion = st.selectbox(
            "Подсказки movement_type",
            ["— выбрать из списка —"] + MOVEMENT_TYPE_OPTIONS,
            key="mt_suggestion",
        )
        if mt_suggestion != "— выбрать из списка —":
            new_movement_type = mt_suggestion

        # movement_label
        new_movement_label = st.text_input(
            "movement_label",
            value=session.get("movement_label", "unknown"),
        )

        # subject_id
        subj_current = session.get("subject_id", "unknown")
        subj_options = subject_ids.copy()
        if subj_current not in subj_options:
            subj_options.insert(0, subj_current)
        new_subject_id = st.selectbox(
            "subject_id",
            subj_options,
            index=subj_options.index(subj_current),
        )

        # wrist
        wrist_current = session.get("wrist") or "unknown"
        new_wrist = st.selectbox(
            "wrist",
            WRIST_OPTIONS,
            index=WRIST_OPTIONS.index(wrist_current) if wrist_current in WRIST_OPTIONS else 2,
        )

    with col2:
        # status
        status_current = session.get("status", "draft")
        new_status = st.selectbox(
            "status",
            STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(status_current) if status_current in STATUS_OPTIONS else 0,
        )

        # records_actual
        new_records_actual = st.number_input(
            "records_actual",
            min_value=0,
            value=int(session["records_actual"]) if session.get("records_actual") is not None else 0,
            step=1,
        )

        # comment
        new_comment = st.text_area(
            "comment",
            value=session.get("comment", ""),
            height=120,
        )

    st.divider()

    col_save, col_delete = st.columns([3, 1])

    with col_save:
        if st.button("💾 Сохранить", type="primary"):
            sessions[idx] = {
                **session,
                "movement_type":   new_movement_type,
                "movement_label":  new_movement_label,
                "subject_id":      new_subject_id,
                "wrist":           new_wrist,
                "status":          new_status,
                "records_actual":  new_records_actual if new_records_actual > 0 else None,
                "comment":         new_comment,
            }
            save_json_list(SESSIONS_PATH, sessions)
            reload_all()
            st.success("Сохранено.")
            st.rerun()

    with col_delete:
        with st.expander("⚠️ Удалить сессию"):
            st.warning("Удалит запись из JSON. CSV файл не удаляется.")
            if st.button("Удалить", type="primary", key="del_session_btn"):
                uid = session.get("session_uid", "?")
                sessions.pop(idx)
                save_json_list(SESSIONS_PATH, sessions)
                reload_all()
                st.success(f"Сессия {uid} удалена.")
                st.rerun()

    # --- Удаление отдельных записей из CSV ---
    st.divider()
    st.subheader("Удалить записи из CSV")

    file_path = Path(session.get("file_path", ""))
    if not file_path.exists():
        st.warning(f"CSV файл не найден: {file_path}")
    else:
        csv_df = pd.read_csv(file_path)
        data_rows = csv_df[csv_df["row_type"] == "DATA"].copy() \
            if "row_type" in csv_df.columns else csv_df.copy()
        data_rows["record_id"] = pd.to_numeric(
            data_rows.get("record_id", pd.Series(dtype=float)), errors="coerce"
        )

        if "record_id" not in data_rows.columns or data_rows["record_id"].isna().all():
            st.info("Нет record_id в файле.")
        else:
            record_ids = sorted(data_rows["record_id"].dropna().unique())

            # Таблица записей с количеством сэмплов
            record_info = []
            for rid in record_ids:
                n = (data_rows["record_id"] == rid).sum()
                record_info.append({"record_id": int(rid), "сэмплов": n})
            st.dataframe(pd.DataFrame(record_info), use_container_width=True,
                         hide_index=True)

            records_to_delete = st.multiselect(
                "Выбери record_id для удаления",
                options=[int(r) for r in record_ids],
                help="Можно выбрать несколько. Строки будут удалены из CSV."
            )

            if records_to_delete:
                st.warning(
                    f"Будут удалены записи {records_to_delete} "
                    f"из {file_path.name}"
                )
                if st.button("🗑 Удалить выбранные записи", type="primary",
                             key="del_records_btn"):
                    # Удаляем DATA строки выбранных записей
                    # EVENT строки (START/STOP) для этих record_id тоже удаляем
                    if "row_type" in csv_df.columns and "record_id" in csv_df.columns:
                        csv_df["record_id_num"] = pd.to_numeric(
                            csv_df["record_id"], errors="coerce"
                        )
                        mask_delete = (
                            csv_df["record_id_num"].isin(records_to_delete)
                        )
                        csv_cleaned = csv_df[~mask_delete].drop(
                            columns=["record_id_num"]
                        )
                    else:
                        csv_df["record_id_num"] = pd.to_numeric(
                            csv_df.get("record_id", pd.Series(dtype=float)),
                            errors="coerce"
                        )
                        mask_delete = csv_df["record_id_num"].isin(records_to_delete)
                        csv_cleaned = csv_df[~mask_delete].drop(
                            columns=["record_id_num"]
                        )

                    csv_cleaned.to_csv(file_path, index=False, encoding="utf-8")
                    reload_all()
                    st.success(
                        f"Записи {records_to_delete} удалены. "
                        f"Осталось строк: {len(csv_cleaned)}"
                    )
                    st.rerun()


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

    sessions    = load_sessions_cached()
    experiments = load_experiments_cached()

    page = st.sidebar.radio(
        "Режим",
        ["🗂 Обзор", "📈 Просмотр", "✏️ Редактор"],
    )

    st.sidebar.divider()
    st.sidebar.caption(f"Экспериментов: {len(experiments)}")
    st.sidebar.caption(f"Сессий: {len(sessions)}")

    if sessions:
        df = sessions_to_df(sessions)
        draft_count = (df["status"] == "draft").sum() if "status" in df.columns else 0
        if draft_count > 0:
            st.sidebar.warning(f"{draft_count} сессий ждут описания")

    st.sidebar.divider()
    if st.sidebar.button("🔄 Обновить данные"):
        reload_all()
        st.rerun()

    if page == "🗂 Обзор":
        page_overview()
    elif page == "📈 Просмотр":
        page_session_viewer()
    else:
        page_editor()


if __name__ == "__main__":
    main()
