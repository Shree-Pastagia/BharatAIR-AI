"""Presentation navigation, chapter progress indicator, and controls."""

import streamlit as st
from bharatair.dashboard.config import CHAPTERS


def render_presentation_header(current_chapter_idx: int) -> None:
    """Render top presentation banner with chapter progress indicator."""
    chapter = CHAPTERS[current_chapter_idx]
    pct = int(((current_chapter_idx + 1) / len(CHAPTERS)) * 100)

    # Progress bar and presentation state bar
    st.markdown(
        f"""
        <div class="presentation-bar">
            <div class="progress-indicator">
                <span class="chapter-number-pill">Chapter {chapter['id']} of 5</span>
                <span style="font-weight: 700; color: #FFFFFF; font-size: 1.05rem;">{chapter['title']}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 14px;">
                <span style="font-size: 0.8rem; color: #94A3B8; font-weight: 600;">{pct}% Complete</span>
                <div style="width: 140px; height: 7px; background: rgba(255,255,255,0.1); border-radius: 9999px; overflow: hidden;">
                    <div style="width: {pct}%; height: 100%; background: linear-gradient(90deg, #38BDF8, #2DD4BF); border-radius: 9999px;"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chapter_buttons(current_chapter_idx: int) -> None:
    """Render sleek Previous and Next navigation buttons at the bottom of the chapter."""
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    col_prev, col_center, col_next = st.columns([1.5, 1, 1.5])

    total_chapters = len(CHAPTERS)

    with col_prev:
        if current_chapter_idx > 0:
            prev_ch = CHAPTERS[current_chapter_idx - 1]
            if st.button(f"◀ Chapter {prev_ch['id']}: {prev_ch['title']}", use_container_width=True, key=f"btn_prev_{current_chapter_idx}"):
                st.session_state["chapter_index"] = current_chapter_idx - 1
                st.rerun()

    with col_center:
        st.markdown(
            f"<div style='text-align: center; color: #64748B; font-size: 0.825rem; padding-top: 8px;'>Chapter {current_chapter_idx + 1} / {total_chapters}</div>",
            unsafe_allow_html=True,
        )

    with col_next:
        if current_chapter_idx < total_chapters - 1:
            next_ch = CHAPTERS[current_chapter_idx + 1]
            if st.button(f"Chapter {next_ch['id']}: {next_ch['title']} ▶", use_container_width=True, key=f"btn_next_{current_chapter_idx}"):
                st.session_state["chapter_index"] = current_chapter_idx + 1
                st.rerun()
        else:
            if st.button("↺ Restart Presentation (Chapter 1)", use_container_width=True, key="btn_restart"):
                st.session_state["chapter_index"] = 0
                st.rerun()

