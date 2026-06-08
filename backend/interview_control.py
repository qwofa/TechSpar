"""Reusable interview control presets and payload helpers."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

RESUME_INTERVIEW_CONTROL_VERSION = "2026-03-p0-p1"
DEFAULT_RESUME_INTERVIEW_CONTROL_ID = "standard_interview"

CONTROL_AXES = [
    {"key": "persona", "label": "面试官人格"},
    {"key": "pressure", "label": "施压强度"},
    {"key": "verification", "label": "验证方式"},
    {"key": "pace", "label": "节奏密度"},
    {"key": "focus", "label": "考察重心"},
    {"key": "context_fit", "label": "上下文贴合"},
]

BEHAVIOR_BUDGETS = [
    {"key": "clarification", "label": "基础澄清"},
    {"key": "deep_followup", "label": "深度追问"},
    {"key": "lateral_solution", "label": "横向方案"},
    {"key": "tradeoff", "label": "方案取舍"},
    {"key": "optimization", "label": "优化扩展"},
    {"key": "authenticity", "label": "项目真实性验证"},
    {"key": "role_fit", "label": "岗位贴合"},
    {"key": "behavioral", "label": "行为验证"},
]

_RESUME_INTERVIEW_CONTROLS = [
    {
        "id": "friendly_training",
        "name": "友好训练",
        "short_name": "友好",
        "headline": "先把经历讲清楚",
        "description": "面试官更像教练，会先帮候选人把背景、概念和项目表达捋顺。",
        "best_for": "第一次练习、简历刚改完、表达还没收口",
        "pressure_label": "低压",
        "pace_label": "舒缓",
        "control_axes": {
            "persona": "耐心教练型",
            "pressure": "低",
            "verification": "先澄清，再轻度追问",
            "pace": "舒缓",
            "focus": "表达完整度、基础理解、岗位贴合",
            "context_fit": "强贴合简历和目标岗位",
        },
        "behavior_budgets": {
            "clarification": 24,
            "deep_followup": 14,
            "lateral_solution": 8,
            "tradeoff": 10,
            "optimization": 8,
            "authenticity": 14,
            "role_fit": 12,
            "behavioral": 10,
        },
        "visible_focus": ["表达梳理", "基础澄清", "轻度项目验证"],
        "prompt_directive": (
            "整体保持低压和引导感。优先确认候选人经历、术语和项目背景是否讲清楚。"
            "追问要具体但不要连续压迫；候选人答得浅时先给可回答的切入口。"
        ),
    },
    {
        "id": "standard_interview",
        "name": "标准面试",
        "short_name": "标准",
        "headline": "接近常规技术面",
        "description": "节奏、压力和追问深度保持均衡，用来建立一场正式面试基线。",
        "best_for": "正式投递前自测、建立能力基线",
        "pressure_label": "中等",
        "pace_label": "标准",
        "control_axes": {
            "persona": "常规技术面试官",
            "pressure": "中",
            "verification": "澄清、深挖、取舍均衡",
            "pace": "标准",
            "focus": "技术理解、项目细节、岗位匹配",
            "context_fit": "强贴合简历和目标岗位",
        },
        "behavior_budgets": {
            "clarification": 14,
            "deep_followup": 18,
            "lateral_solution": 12,
            "tradeoff": 14,
            "optimization": 12,
            "authenticity": 14,
            "role_fit": 10,
            "behavioral": 6,
        },
        "visible_focus": ["技术理解", "项目细节", "方案取舍"],
        "prompt_directive": (
            "整体模拟常规技术面。每个阶段都要有明确考察点，问题不要过度友好，"
            "也不要为了施压而施压；候选人回答后自然追到下一层原因、边界或项目落地。"
        ),
    },
    {
        "id": "deep_verification",
        "name": "深挖验证",
        "short_name": "深挖",
        "headline": "验证项目是不是真懂",
        "description": "明显提高项目真实性、技术细节、边界条件和取舍逻辑的追问比例。",
        "best_for": "项目经历强、担心被追问穿、准备中高级面试",
        "pressure_label": "中高",
        "pace_label": "偏紧",
        "control_axes": {
            "persona": "资深专家型",
            "pressure": "中高",
            "verification": "连续深挖和真实性验证",
            "pace": "偏紧",
            "focus": "项目细节、技术边界、方案取舍",
            "context_fit": "极强贴合简历项目",
        },
        "behavior_budgets": {
            "clarification": 8,
            "deep_followup": 24,
            "lateral_solution": 14,
            "tradeoff": 18,
            "optimization": 14,
            "authenticity": 16,
            "role_fit": 4,
            "behavioral": 2,
        },
        "visible_focus": ["项目真实性", "技术边界", "方案取舍"],
        "prompt_directive": (
            "整体偏专家深挖。候选人提到项目、架构、指标、性能、线上问题时，"
            "要继续追问他本人做了什么、为什么这么做、还有哪些替代方案和代价。"
        ),
    },
    {
        "id": "pressure_challenge",
        "name": "高压实战",
        "short_name": "高压",
        "headline": "更接近强压面试现场",
        "description": "节奏更紧，更多挑战、反问、横向迁移和方案取舍验证。",
        "best_for": "冲刺高强度面试、终面压力场、检验抗压表达",
        "pressure_label": "高",
        "pace_label": "紧凑",
        "control_axes": {
            "persona": "压力挑战型",
            "pressure": "高",
            "verification": "挑战假设、横向迁移、取舍压测",
            "pace": "紧凑",
            "focus": "抗压表达、方案判断、技术迁移",
            "context_fit": "围绕简历和岗位快速切换场景",
        },
        "behavior_budgets": {
            "clarification": 6,
            "deep_followup": 20,
            "lateral_solution": 18,
            "tradeoff": 20,
            "optimization": 16,
            "authenticity": 14,
            "role_fit": 2,
            "behavioral": 4,
        },
        "visible_focus": ["压力追问", "横向迁移", "方案取舍"],
        "prompt_directive": (
            "整体保持高压但专业，不要羞辱候选人。候选人回答含糊时直接指出不清楚的点并追问。"
            "多用如果场景变化、指标放大、资源受限、线上故障等方式压测方案。"
        ),
    },
]


def _index_controls() -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in _RESUME_INTERVIEW_CONTROLS}


def _extract_control_id(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("id") or value.get("preset_id") or value.get("interview_control_preset")
    return None


def resolve_resume_interview_control(preset_id: Any, *, strict: bool = False) -> dict[str, Any]:
    controls = _index_controls()
    raw_id = _extract_control_id(preset_id)
    normalized_id = (raw_id or DEFAULT_RESUME_INTERVIEW_CONTROL_ID).strip() or DEFAULT_RESUME_INTERVIEW_CONTROL_ID
    control = controls.get(normalized_id)
    if not control:
        if strict:
            raise ValueError(f"Unknown resume interview control preset: {normalized_id}")
        control = controls[DEFAULT_RESUME_INTERVIEW_CONTROL_ID]
    result = deepcopy(control)
    result["version"] = RESUME_INTERVIEW_CONTROL_VERSION
    return result


def public_resume_interview_control(control: dict[str, Any]) -> dict[str, Any]:
    result = {key: deepcopy(value) for key, value in control.items() if key != "prompt_directive"}
    result["version"] = RESUME_INTERVIEW_CONTROL_VERSION
    return result


def public_resume_interview_control_from(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        preset_id = value
    elif isinstance(value, dict):
        preset_id = value.get("id") or value.get("preset_id") or value.get("interview_control_preset")
    else:
        preset_id = None
    return public_resume_interview_control(resolve_resume_interview_control(preset_id))


def list_resume_interview_controls() -> list[dict[str, Any]]:
    return [public_resume_interview_control(resolve_resume_interview_control(item["id"])) for item in _RESUME_INTERVIEW_CONTROLS]


def build_resume_interview_control_prompt(value: Any) -> str:
    control = resolve_resume_interview_control(
        value.get("id") if isinstance(value, dict) else value,
    )
    budget_labels = {item["key"]: item["label"] for item in BEHAVIOR_BUDGETS}
    axis_labels = {item["key"]: item["label"] for item in CONTROL_AXES}
    axis_lines = [
        f"- {axis_labels.get(key, key)}: {text}"
        for key, text in control.get("control_axes", {}).items()
    ]
    budget_lines = [
        f"- {budget_labels.get(key, key)}: {value}%"
        for key, value in control.get("behavior_budgets", {}).items()
    ]
    focus = "、".join(control.get("visible_focus", [])) or "按当前阶段自然推进"
    return "\n".join([
        "## 本场面试控制挡位",
        f"- 挡位: {control['name']}（{control['headline']}）",
        f"- 适合场景: {control['best_for']}",
        f"- 对候选人可见重点: {focus}",
        "",
        "### 控制轴",
        *axis_lines,
        "",
        "### 行为预算倾向",
        *budget_lines,
        "",
        "### 执行要求",
        control.get("prompt_directive", "按标准面试节奏推进。"),
        "行为预算是提问倾向，不是机械配额；每次仍然只问一个清晰问题。",
    ])


def build_resume_interview_meta(target_role: str, preset_id: str | None) -> dict[str, Any]:
    control = public_resume_interview_control(resolve_resume_interview_control(preset_id))
    return {
        "target_role": target_role,
        "interview_control_preset": control["id"],
        "interview_control_version": RESUME_INTERVIEW_CONTROL_VERSION,
        "interview_control": control,
    }


def enrich_resume_session_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("mode") != "resume":
        return payload
    result = dict(payload)
    meta = dict(result.get("meta") or {})
    control_source = (
        result.get("interview_control")
        or result.get("interview_control_preset")
        or meta.get("interview_control")
        or meta.get("interview_control_preset")
    )
    control = public_resume_interview_control_from(control_source)
    meta.setdefault("interview_control_preset", control["id"])
    meta.setdefault("interview_control_version", RESUME_INTERVIEW_CONTROL_VERSION)
    meta["interview_control"] = control
    result["meta"] = meta
    result["target_role"] = meta.get("target_role", result.get("target_role", ""))
    result["interview_control"] = control
    result["interview_control_preset"] = control["id"]
    return result
