"""复盘系统：面试结束后生成复盘报告。"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from backend.interview_control import public_resume_interview_control_from
from backend.llm_provider import get_langchain_llm
from backend.prompts.reviewer import REVIEW_SYSTEM
from backend.models import InterviewMode


def _fmt_percent(value) -> str:
    if isinstance(value, int):
        return f"{value}%"
    if isinstance(value, float):
        rounded = round(value, 1)
        return f"{int(rounded)}%" if rounded.is_integer() else f"{rounded}%"
    return f"{value}%"


def _build_control_review_context(control_review: dict | None) -> str:
    if not control_review:
        return ""

    lines = ["## 本场实际动作分布"]
    if control_review.get("preset_name"):
        lines.append(f"- 挡位: {control_review['preset_name']}")
    if control_review.get("question_count") is not None:
        lines.append(f"- 识别到的面试官问题数: {control_review['question_count']}")
    if control_review.get("alignment_summary"):
        lines.append(f"- 对齐判断: {control_review['alignment_summary']}")

    target = control_review.get("budget_highlights") or []
    if target:
        lines.append(
            "- 预期高亮动作: " + "、".join(
                f"{item.get('label', item.get('key', '?'))}（{_fmt_percent(item.get('percent', 0))}）"
                for item in target
            )
        )

    actual = control_review.get("dominant_behaviors") or []
    if actual:
        lines.append(
            "- 实际高亮动作: " + "、".join(
                f"{item.get('label', item.get('key', '?'))}（{item.get('count', 0)}次）"
                for item in actual
            )
        )

    distribution = control_review.get("distribution") or []
    if distribution:
        lines.append("")
        lines.append("### 重点动作组统计")
        for item in distribution[:4]:
            example = (item.get("examples") or [""])[0]
            segment = (
                f"- {item.get('label', item.get('key', '?'))}: 实际 {item.get('count', 0)} 次 / "
                f"{_fmt_percent(item.get('actual_percent', 0))}，挡位预算 {_fmt_percent(item.get('target_percent', 0))}"
            )
            if item.get("alignment") == "above":
                segment += "，比预期更强"
            elif item.get("alignment") == "below":
                segment += "，比预期更弱"
            else:
                segment += "，和预期接近"
            if example:
                segment += f"。示例问法：{example}"
            lines.append(segment)

    return "\n".join(lines) + "\n"


def generate_review(
    mode: InterviewMode,
    messages: list,
    scores: list[dict] | None = None,
    weak_points: list[str] | None = None,
    topic: str | None = None,
    eval_history: list[dict] | None = None,
    resume_context: str | None = None,
    interview_control: dict | None = None,
    control_review: dict | None = None,
    user_id: str | None = None,
) -> str:
    """Generate a structured review report from interview transcript."""

    # Build transcript from messages
    transcript_lines = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            transcript_lines.append(f"**候选人**: {msg.content}")
        elif isinstance(msg, AIMessage):
            transcript_lines.append(f"**面试官**: {msg.content}")
    transcript = "\n\n".join(transcript_lines)

    # Build extra context
    extra = ""
    if mode == InterviewMode.TOPIC_DRILL:
        if scores:
            score_summary = "\n".join(
                f"- Q: {s.get('question', '?')} → {s.get('score', '?')}/10 ({s.get('assessment', '')})"
                for s in scores
            )
            extra += f"\n## 各题评分记录\n{score_summary}\n"
        if weak_points:
            extra += f"\n## 已识别的薄弱点\n{', '.join(weak_points)}\n"
        if topic:
            extra += f"\n## 训练领域: {topic}\n"

    # Resume mode: use inline eval history if available
    if mode == InterviewMode.RESUME and eval_history:
        eval_lines = []
        for e in eval_history:
            score = e.get("score", "?")
            brief = e.get("brief", "")
            phase = e.get("phase", "")
            line = f"- [{phase}] {score}/10 — {brief}"
            evidence = e.get("evidence")
            if evidence:
                line += f"（原话：{evidence}）"
            eval_lines.append(line)
        scored = [e["score"] for e in eval_history if isinstance(e.get("score"), (int, float))]
        avg = round(sum(scored) / len(scored), 1) if scored else None
        extra += f"\n## 面试过程评分记录\n" + "\n".join(eval_lines) + "\n"
        if avg:
            extra += f"\n平均分: {avg}/10\n"

    # Resume mode: feed the resume so the review can cross-check claims vs answers,
    # and ask for resume-consistency + model-answer sections on top of the base structure.
    if mode == InterviewMode.RESUME:
        control = public_resume_interview_control_from(interview_control)
        profile_lines = "\n".join(
            f"- {item.get('label', item.get('key', '?'))}: {_fmt_percent(item.get('percent', 0))}"
            for item in control.get("behavior_budget_profile", [])
        )
        highlight_labels = "、".join(
            item.get("label", item.get("key", "?"))
            for item in control.get("behavior_budget_highlights", [])
        )
        extra += (
            f"\n## 本场所选挡位\n"
            f"- 挡位: {control.get('name', '标准面试')}\n"
            f"- 可见重点: {'、'.join(control.get('visible_focus', [])) or '按阶段推进'}\n"
            f"- 预算高亮: {highlight_labels or '未标注'}\n"
            f"- 预算摘要: {control.get('budget_preview_summary', '')}\n"
            f"\n### 挡位预算画像\n{profile_lines}\n"
        )
        extra += "\n" + _build_control_review_context(control_review)
        if resume_context:
            extra += f"\n## 候选人简历（用于核验简历声称与面试表现是否一致）\n{resume_context}\n"
        extra += (
            "\n## 本次复盘的额外要求（简历面试）\n"
            "- 在标准复盘结构之外，额外加一段「## 挡位执行解释」：不要只说压力高或节奏快，"
            "要明确解释本场更偏哪些动作组、哪些和所选挡位一致、哪些比预期更强或更弱，并优先引用面试官原问题做举证。\n"
            "- 再加一段「## 简历印证」：逐条对比简历里的关键声称"
            "（技能/项目/成果）与候选人实际回答——哪些得到印证、哪些存疑（简历写了但答得浅、"
            "答不上或前后矛盾）。存疑的要点明确标出并引用对应原话，没有可核验的点就说明无明显出入。\n"
            "- 再加一段「## 更好的答法」：挑本场表现最弱的 2-3 个问题，给出更好的回答示范"
            "（每个 150 字以内，口语化、像真在面试里答），让候选人有可直接对照的范本。\n"
        )

    prompt = REVIEW_SYSTEM.format(
        mode=mode.value,
        transcript=transcript,
        extra_context=extra,
    )

    llm = get_langchain_llm(user_id)
    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content="请生成复盘报告。"),
    ])

    return response.content
