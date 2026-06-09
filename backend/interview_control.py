"""Reusable interview control presets and payload helpers."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
import re
from typing import Any

from backend.config import settings

RESUME_INTERVIEW_CONTROL_VERSION = "2026-03-p3"
DEFAULT_RESUME_INTERVIEW_CONTROL_ID = "standard_interview"

DIY_PRESSURE_TUNING_OPTIONS = [
    {"id": "same", "label": "保持当前压力", "description": "沿用当前挡位的压力和节奏。"},
    {"id": "lighter", "label": "更友好一点", "description": "先帮我把表达讲顺，再逐步进入追问。"},
    {"id": "stronger", "label": "更严格一点", "description": "更快进入深挖、取舍和挑战场景。"},
]

DIY_FOLLOWUP_STYLE_OPTIONS = [
    {"id": "balanced", "label": "均衡推进", "description": "按当前挡位默认节奏推进。"},
    {"id": "clarify_first", "label": "先澄清再下钻", "description": "先确认背景和职责，再做深追问。"},
    {"id": "deep_dive", "label": "更早进入深挖", "description": "更快追到底层细节、边界和本人贡献。"},
]

DIY_FOCUS_BOOST_OPTIONS = [
    {"id": "", "label": "不额外加码", "description": "先按当前挡位默认重心推进。"},
    {"id": "authenticity", "label": "多验项目真实性", "description": "更关注你本人做过什么、证据和线上结果。"},
    {"id": "deep_followup", "label": "多做技术深挖", "description": "更关注实现细节、链路和边界。"},
    {"id": "tradeoff", "label": "多问方案取舍", "description": "更关注为什么这样选、代价和替代方案。"},
    {"id": "optimization", "label": "多问优化扩展", "description": "更关注性能、稳定性、规模化和维护性。"},
    {"id": "role_fit", "label": "多贴目标岗位", "description": "更关注你的经历怎么映射到目标岗位。"},
    {"id": "behavioral", "label": "多验协作复盘", "description": "更关注沟通、推进、冲突和复盘能力。"},
]

DEFAULT_RESUME_INTERVIEW_OVERRIDES = {
    "pressure_tuning": "same",
    "followup_style": "balanced",
    "focus_boost": "",
}

RESUME_INTERVIEW_DIY_OPTIONS = {
    "pressure_tuning": DIY_PRESSURE_TUNING_OPTIONS,
    "followup_style": DIY_FOLLOWUP_STYLE_OPTIONS,
    "focus_boost": DIY_FOCUS_BOOST_OPTIONS,
}

_DIY_OPTION_IDS = {
    key: {item["id"] for item in options}
    for key, options in RESUME_INTERVIEW_DIY_OPTIONS.items()
}
_DIY_OPTION_LABELS = {
    key: {item["id"]: item["label"] for item in options}
    for key, options in RESUME_INTERVIEW_DIY_OPTIONS.items()
}
_CONTROL_OVERLAY_KEYS = {
    "id",
    "name",
    "short_name",
    "headline",
    "description",
    "best_for",
    "pressure_label",
    "pace_label",
    "control_axes",
    "behavior_budgets",
    "visible_focus",
    "difference_note",
    "preview_highlight_keys",
    "prompt_directive",
    "base_preset_id",
    "base_preset_name",
    "is_diy_adjusted",
    "diy_overrides",
    "diy_summary",
    "origin",
}
_RESUME_PREVIEW_CACHE_NAME = "resume_interview_preview.json"
_PRESSURE_LABEL_ORDER = ["低压", "中等", "中高", "高"]
_PRESSURE_AXIS_ORDER = ["低", "中", "中高", "高"]
_PACE_LABEL_ORDER = ["舒缓", "标准", "偏紧", "紧凑"]

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

_BEHAVIOR_LABELS = {item["key"]: item["label"] for item in BEHAVIOR_BUDGETS}
_BEHAVIOR_HINTS = {
    "clarification": "先确认背景、上下文和候选人的真实表述。",
    "deep_followup": "沿着一个回答继续往细节、机制和边界下钻。",
    "lateral_solution": "把问题切到替代方案、迁移场景或变化条件。",
    "tradeoff": "追问为什么这样选，以及为此承担了什么代价。",
    "optimization": "继续问性能、稳定性、规模化和可维护性。",
    "authenticity": "验证项目是否真做过、关键细节是否自洽。",
    "role_fit": "把经历拉回目标岗位能力模型和业务场景。",
    "behavioral": "用真实经历看协作、抗压、推进和复盘能力。",
}

_BEHAVIOR_PRIORITY = [
    "authenticity",
    "tradeoff",
    "lateral_solution",
    "optimization",
    "behavioral",
    "role_fit",
    "deep_followup",
    "clarification",
]

_BEHAVIOR_PRIORITY_INDEX = {key: index for index, key in enumerate(_BEHAVIOR_PRIORITY)}

_BEHAVIOR_CLASSIFIER_RULES = {
    "clarification": [
        ("自我介绍", 5),
        ("介绍一下", 4),
        ("先讲讲", 3),
        ("先说说", 3),
        ("简单说说", 3),
        ("背景", 2),
        ("负责什么", 2),
        ("是什么意思", 2),
        ("怎么理解", 2),
        ("是什么", 1),
    ],
    "deep_followup": [
        ("为什么", 2),
        ("具体", 2),
        ("展开", 2),
        ("细节", 2),
        ("怎么实现", 3),
        ("底层", 3),
        ("原理", 2),
        ("链路", 2),
        ("流程", 2),
        ("一步一步", 3),
        ("拆开", 2),
        ("再讲讲", 2),
    ],
    "lateral_solution": [
        ("还有什么方案", 4),
        ("替代方案", 4),
        ("换一种", 3),
        ("迁移", 3),
        ("对比", 3),
        ("比较", 3),
        ("另一种", 2),
        ("如果换成", 4),
        ("还有别的", 2),
    ],
    "tradeoff": [
        ("为什么选", 4),
        ("为什么不用", 4),
        ("取舍", 4),
        ("权衡", 4),
        ("代价", 3),
        ("优缺点", 3),
        ("收益", 2),
        ("成本", 2),
        ("平衡", 2),
        ("牺牲", 3),
        ("保住", 3),
        ("优先", 2),
    ],
    "optimization": [
        ("优化", 4),
        ("性能", 3),
        ("稳定性", 3),
        ("扩展", 2),
        ("高并发", 3),
        ("吞吐", 3),
        ("延迟", 3),
        ("容量", 2),
        ("监控", 2),
        ("降级", 2),
        ("容灾", 3),
        ("可维护", 2),
    ],
    "authenticity": [
        ("你本人", 5),
        ("你亲自", 5),
        ("你负责", 4),
        ("谁做的", 4),
        ("怎么证明", 4),
        ("线上", 2),
        ("真实", 2),
        ("指标", 2),
        ("落地", 2),
        ("具体做过", 4),
        ("亲手", 3),
    ],
    "role_fit": [
        ("目标岗位", 5),
        ("这个岗位", 5),
        ("岗位", 3),
        ("为什么适合", 4),
        ("为什么想做", 3),
        ("业务场景", 2),
        ("团队", 2),
        ("公司", 2),
        ("匹配", 3),
    ],
    "behavioral": [
        ("冲突", 4),
        ("协作", 4),
        ("压力", 3),
        ("复盘", 4),
        ("沟通", 3),
        ("推进", 3),
        ("困难", 2),
        ("失败", 3),
        ("反馈", 3),
        ("说服", 3),
        ("合作", 3),
    ],
}

_PRESET_SAMPLE_PREVIEWS = {
    "friendly_training": [
        {
            "budget_key": "clarification",
            "prompt": "你先别急着讲结果，按背景、目标、你的职责和最终产出，把这个项目顺一遍。",
        },
        {
            "budget_key": "authenticity",
            "prompt": "这个优化里你本人亲自负责的是哪一段？如果把你抽掉，最难复现的部分是什么？",
        },
    ],
    "standard_interview": [
        {
            "budget_key": "deep_followup",
            "prompt": "你刚才提到用了缓存，那我继续追一层：一致性、失效和击穿分别怎么处理？",
        },
        {
            "budget_key": "tradeoff",
            "prompt": "当时为什么选这个方案，而不是另一个更常见的做法？你接受了哪些代价？",
        },
    ],
    "deep_verification": [
        {
            "budget_key": "deep_followup",
            "prompt": "你说这条链路是你主导的，那我们把请求路径拆开，从入口到落库一步一步讲。",
        },
        {
            "budget_key": "authenticity",
            "prompt": "这个指标提升是你真实在线上拿到的吗？观测口径、实验对照和回滚预案分别是什么？",
        },
    ],
    "pressure_challenge": [
        {
            "budget_key": "tradeoff",
            "prompt": "如果现在延迟翻倍但预算不能加，你优先牺牲什么、保住什么？为什么？",
        },
        {
            "budget_key": "lateral_solution",
            "prompt": "假设现有技术栈突然不能用，你给我一个替代方案，并说清迁移代价。",
        },
    ],
}

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
        "difference_note": "这档会先帮你把叙述讲顺，再慢慢进入验证，不会一上来就连续施压。",
        "preview_highlight_keys": ["clarification", "authenticity"],
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
        "difference_note": "这档会在深挖、取舍和岗位匹配之间保持均衡，更接近多数正式技术面。",
        "preview_highlight_keys": ["deep_followup", "tradeoff"],
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
        "difference_note": "这档会连续追项目细节和本人贡献，核心目标是验证你是不是真的做过、真的想明白了。",
        "preview_highlight_keys": ["deep_followup", "authenticity"],
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
        "difference_note": "这档会更快切场景、更频繁压条件，逼你当场做判断和取舍。",
        "preview_highlight_keys": ["tradeoff", "lateral_solution"],
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


def _normalize_percent(value: float) -> float | int:
    rounded = round(float(value), 1)
    return int(rounded) if rounded.is_integer() else rounded


def _sample_preview_for(control_id: str) -> list[dict[str, Any]]:
    items = []
    for sample in _PRESET_SAMPLE_PREVIEWS.get(control_id, []):
        budget_key = sample.get("budget_key") or "clarification"
        items.append({
            "budget_key": budget_key,
            "label": _BEHAVIOR_LABELS.get(budget_key, budget_key),
            "hint": _BEHAVIOR_HINTS.get(budget_key, ""),
            "prompt": sample.get("prompt", ""),
        })
    return items


def build_behavior_budget_profile(control: dict[str, Any]) -> list[dict[str, Any]]:
    budgets = control.get("behavior_budgets", {}) or {}
    total = sum(max(0.0, float(value or 0)) for value in budgets.values()) or 1.0
    items = []
    for item in BEHAVIOR_BUDGETS:
        raw_value = max(0.0, float(budgets.get(item["key"], 0) or 0))
        items.append({
            "key": item["key"],
            "label": item["label"],
            "weight": _normalize_percent(raw_value),
            "percent": _normalize_percent(raw_value / total * 100),
            "hint": _BEHAVIOR_HINTS.get(item["key"], ""),
        })
    items.sort(key=lambda entry: (-float(entry["percent"]), entry["label"]))
    for index, item in enumerate(items, start=1):
        item["rank"] = index
        item["emphasis"] = "high" if index <= 2 else "medium" if float(item["percent"]) >= 12 else "low"
    return items


def build_behavior_budget_highlights(control: dict[str, Any], *, limit: int = 2) -> list[dict[str, Any]]:
    profile = build_behavior_budget_profile(control)
    by_key = {item["key"]: item for item in profile}
    ordered_keys = list(control.get("preview_highlight_keys") or [])
    selected: list[dict[str, Any]] = []

    for key in ordered_keys:
        item = by_key.get(key)
        if item and item not in selected:
            selected.append(item)
        if len(selected) >= limit:
            break

    for item in profile:
        if len(selected) >= limit:
            break
        if item not in selected:
            selected.append(item)

    return [
        {
            "key": item["key"],
            "label": item["label"],
            "percent": item["percent"],
            "hint": item["hint"],
            "rank": item["rank"],
        }
        for item in selected[:limit]
    ]


def _highlight_summary(highlights: list[dict[str, Any]]) -> str:
    if not highlights:
        return ""
    if len(highlights) == 1:
        return f"本档更常出现{highlights[0]['label']}类问题。"
    first, second = highlights[0], highlights[1]
    return f"本档更常出现{first['label']}和{second['label']}类问题。"


def _normalize_behavior_budgets(weights: dict[str, Any]) -> dict[str, int]:
    keys = [item["key"] for item in BEHAVIOR_BUDGETS]
    cleaned = {key: max(0.0, float(weights.get(key, 0) or 0)) for key in keys}
    total = sum(cleaned.values()) or 1.0
    normalized = {key: cleaned[key] / total * 100 for key in keys}
    rounded = {key: int(round(value)) for key, value in normalized.items()}
    delta = 100 - sum(rounded.values())

    if delta:
        remainders = sorted(
            keys,
            key=lambda key: normalized[key] - rounded[key],
            reverse=delta > 0,
        )
        while delta and remainders:
            for key in remainders:
                if not delta:
                    break
                step = 1 if delta > 0 else -1
                if rounded[key] + step < 0:
                    continue
                rounded[key] += step
                delta -= step
                if not delta:
                    break
    return rounded


def _merge_control_overlay(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in overlay.items():
        if key not in _CONTROL_OVERLAY_KEYS:
            continue
        if key == "control_axes" and isinstance(value, dict):
            merged = deepcopy(result.get("control_axes") or {})
            merged.update(deepcopy(value))
            result["control_axes"] = merged
            continue
        if key == "behavior_budgets" and isinstance(value, dict):
            merged = deepcopy(result.get("behavior_budgets") or {})
            merged.update(deepcopy(value))
            result["behavior_budgets"] = _normalize_behavior_budgets(merged)
            continue
        result[key] = deepcopy(value)
    result["version"] = RESUME_INTERVIEW_CONTROL_VERSION
    return result


def _ensure_public_control_shape(control: dict[str, Any]) -> dict[str, Any]:
    result = {key: deepcopy(value) for key, value in control.items() if key != "prompt_directive"}
    result["version"] = RESUME_INTERVIEW_CONTROL_VERSION
    result["behavior_budget_profile"] = build_behavior_budget_profile(result)
    result["behavior_budget_highlights"] = build_behavior_budget_highlights(result)
    result["budget_preview_summary"] = _highlight_summary(result["behavior_budget_highlights"])
    result["sample_preview"] = _sample_preview_for(result.get("id", ""))
    return result


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
    if isinstance(preset_id, dict):
        result = _merge_control_overlay(result, preset_id)
        result.setdefault("base_preset_id", control["id"])
        result.setdefault("base_preset_name", control["name"])
    result["version"] = RESUME_INTERVIEW_CONTROL_VERSION
    return result


def public_resume_interview_control(control: dict[str, Any]) -> dict[str, Any]:
    return _ensure_public_control_shape(resolve_resume_interview_control(control))


def public_resume_interview_control_from(value: Any) -> dict[str, Any]:
    return public_resume_interview_control(resolve_resume_interview_control(value))


def list_resume_interview_controls() -> list[dict[str, Any]]:
    return [public_resume_interview_control(resolve_resume_interview_control(item["id"])) for item in _RESUME_INTERVIEW_CONTROLS]


def normalize_resume_interview_overrides(value: Any) -> dict[str, str]:
    raw = value if isinstance(value, dict) else {}
    normalized: dict[str, str] = {}
    for key, default in DEFAULT_RESUME_INTERVIEW_OVERRIDES.items():
        candidate = raw.get(key, default)
        candidate = "" if candidate is None else str(candidate)
        if candidate not in _DIY_OPTION_IDS[key]:
            candidate = default
        normalized[key] = candidate
    return normalized


def _shift_scale_label(current: str, order: list[str], step: int) -> str:
    if current not in order:
        return current
    index = order.index(current)
    index = max(0, min(len(order) - 1, index + step))
    return order[index]


def _append_visible_focus(control: dict[str, Any], *items: str) -> None:
    ordered = []
    seen = set()
    for item in list(control.get("visible_focus") or []) + [text for text in items if text]:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    control["visible_focus"] = ordered[:4]


def _apply_pressure_tuning(control: dict[str, Any], option_id: str) -> None:
    budgets = deepcopy(control.get("behavior_budgets") or {})
    if option_id == "lighter":
        budgets["clarification"] = budgets.get("clarification", 0) + 6
        budgets["role_fit"] = budgets.get("role_fit", 0) + 3
        budgets["tradeoff"] = max(0, budgets.get("tradeoff", 0) - 3)
        budgets["lateral_solution"] = max(0, budgets.get("lateral_solution", 0) - 3)
        budgets["optimization"] = max(0, budgets.get("optimization", 0) - 3)
        control["pressure_label"] = _shift_scale_label(control.get("pressure_label", "中等"), _PRESSURE_LABEL_ORDER, -1)
        control["pace_label"] = _shift_scale_label(control.get("pace_label", "标准"), _PACE_LABEL_ORDER, -1)
        axes = deepcopy(control.get("control_axes") or {})
        axes["pressure"] = _shift_scale_label(axes.get("pressure", "中"), _PRESSURE_AXIS_ORDER, -1)
        axes["pace"] = _shift_scale_label(axes.get("pace", "标准"), _PACE_LABEL_ORDER, -1)
        axes["verification"] = "先让候选人把背景说清，再逐步进入验证"
        control["control_axes"] = axes
        control["prompt_directive"] = (
            f"{control.get('prompt_directive', '')} 额外要求：整体再友好一点，先给候选人可回答的切入口，再逐步追问。"
        ).strip()
        _append_visible_focus(control, "先讲顺再验证")
    elif option_id == "stronger":
        budgets["deep_followup"] = budgets.get("deep_followup", 0) + 4
        budgets["tradeoff"] = budgets.get("tradeoff", 0) + 3
        budgets["lateral_solution"] = budgets.get("lateral_solution", 0) + 3
        budgets["clarification"] = max(0, budgets.get("clarification", 0) - 4)
        budgets["role_fit"] = max(0, budgets.get("role_fit", 0) - 3)
        budgets["behavioral"] = max(0, budgets.get("behavioral", 0) - 3)
        control["pressure_label"] = _shift_scale_label(control.get("pressure_label", "中等"), _PRESSURE_LABEL_ORDER, 1)
        control["pace_label"] = _shift_scale_label(control.get("pace_label", "标准"), _PACE_LABEL_ORDER, 1)
        axes = deepcopy(control.get("control_axes") or {})
        axes["pressure"] = _shift_scale_label(axes.get("pressure", "中"), _PRESSURE_AXIS_ORDER, 1)
        axes["pace"] = _shift_scale_label(axes.get("pace", "标准"), _PACE_LABEL_ORDER, 1)
        axes["verification"] = "更快进入深挖、取舍和条件压测"
        control["control_axes"] = axes
        control["prompt_directive"] = (
            f"{control.get('prompt_directive', '')} 额外要求：更快进入深挖和取舍，不要在浅层澄清停留太久。"
        ).strip()
        _append_visible_focus(control, "更快进入深挖")
    control["behavior_budgets"] = _normalize_behavior_budgets(budgets)


def _apply_followup_style(control: dict[str, Any], option_id: str) -> None:
    budgets = deepcopy(control.get("behavior_budgets") or {})
    axes = deepcopy(control.get("control_axes") or {})
    if option_id == "clarify_first":
        budgets["clarification"] = budgets.get("clarification", 0) + 6
        budgets["deep_followup"] = max(0, budgets.get("deep_followup", 0) - 3)
        budgets["authenticity"] = max(0, budgets.get("authenticity", 0) - 2)
        budgets["tradeoff"] = max(0, budgets.get("tradeoff", 0) - 1)
        axes["verification"] = "先澄清角色、背景和职责，再往细节下钻"
        control["prompt_directive"] = (
            f"{control.get('prompt_directive', '')} 额外要求：每次先确认背景和职责，再进入更深一层的技术或项目追问。"
        ).strip()
        _append_visible_focus(control, "先澄清再下钻")
    elif option_id == "deep_dive":
        budgets["clarification"] = max(0, budgets.get("clarification", 0) - 4)
        budgets["deep_followup"] = budgets.get("deep_followup", 0) + 4
        budgets["authenticity"] = budgets.get("authenticity", 0) + 2
        budgets["tradeoff"] = budgets.get("tradeoff", 0) + 2
        axes["verification"] = "更早进入底层细节、边界和本人贡献验证"
        control["prompt_directive"] = (
            f"{control.get('prompt_directive', '')} 额外要求：遇到项目和方案时更早进入细节、边界和本人贡献验证。"
        ).strip()
        _append_visible_focus(control, "更早进入深挖")
    control["control_axes"] = axes
    control["behavior_budgets"] = _normalize_behavior_budgets(budgets)


def _apply_focus_boost(control: dict[str, Any], focus_key: str) -> None:
    if not focus_key:
        return
    budgets = {key: float(value) for key, value in (control.get("behavior_budgets") or {}).items()}
    budgets[focus_key] = budgets.get(focus_key, 0) + 8
    remaining = 8.0
    donor_order = [
        "clarification",
        "role_fit",
        "behavioral",
        "lateral_solution",
        "optimization",
        "tradeoff",
        "authenticity",
        "deep_followup",
    ]
    for donor in donor_order:
        if donor == focus_key or remaining <= 0:
            continue
        available = max(0.0, budgets.get(donor, 0) - 1.0)
        take = min(available, remaining)
        budgets[donor] = budgets.get(donor, 0) - take
        remaining -= take
    control["behavior_budgets"] = _normalize_behavior_budgets(budgets)
    _append_visible_focus(control, _BEHAVIOR_LABELS.get(focus_key, focus_key))
    axes = deepcopy(control.get("control_axes") or {})
    axes["focus"] = f"在当前挡位基础上，额外提高{_BEHAVIOR_LABELS.get(focus_key, focus_key)}比重"
    control["control_axes"] = axes
    control["prompt_directive"] = (
        f"{control.get('prompt_directive', '')} 额外要求：适度提高“{_BEHAVIOR_LABELS.get(focus_key, focus_key)}”相关问题的出现频率。"
    ).strip()


def _summarize_diy_overrides(overrides: dict[str, str]) -> str:
    labels = []
    for key in ("pressure_tuning", "followup_style", "focus_boost"):
        option_id = overrides.get(key, DEFAULT_RESUME_INTERVIEW_OVERRIDES[key])
        if option_id == DEFAULT_RESUME_INTERVIEW_OVERRIDES[key]:
            continue
        label = _DIY_OPTION_LABELS.get(key, {}).get(option_id)
        if label:
            labels.append(label)
    if not labels:
        return "沿用固定挡位默认节奏。"
    return "本场在固定挡位底座上额外调整为：" + " / ".join(labels) + "。"


def build_diy_resume_interview_control(preset_id: Any, overrides: Any = None) -> dict[str, Any]:
    base = resolve_resume_interview_control(preset_id, strict=True)
    normalized_overrides = normalize_resume_interview_overrides(overrides)
    control = deepcopy(base)
    control["base_preset_id"] = base["id"]
    control["base_preset_name"] = base["name"]
    control["diy_overrides"] = normalized_overrides

    changed = any(
        normalized_overrides[key] != DEFAULT_RESUME_INTERVIEW_OVERRIDES[key]
        for key in DEFAULT_RESUME_INTERVIEW_OVERRIDES
    )
    control["is_diy_adjusted"] = changed
    control["origin"] = "diy" if changed else "preset"

    if normalized_overrides["pressure_tuning"] != "same":
        _apply_pressure_tuning(control, normalized_overrides["pressure_tuning"])
    if normalized_overrides["followup_style"] != "balanced":
        _apply_followup_style(control, normalized_overrides["followup_style"])
    if normalized_overrides["focus_boost"]:
        _apply_focus_boost(control, normalized_overrides["focus_boost"])

    control["diy_summary"] = _summarize_diy_overrides(normalized_overrides)
    if changed:
        control["headline"] = f"{base['headline']} · 有限 DIY"
        control["difference_note"] = f"{base.get('difference_note', '')} {control['diy_summary']}".strip()
        control["description"] = f"{base.get('description', '')} 这场额外做了有限 DIY 调整。".strip()
    control["behavior_budgets"] = _normalize_behavior_budgets(control.get("behavior_budgets") or base.get("behavior_budgets") or {})
    control["version"] = RESUME_INTERVIEW_CONTROL_VERSION
    return control


def _resume_preview_cache_path(user_id: str):
    path = settings.user_profile_dir(user_id) / _RESUME_PREVIEW_CACHE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _read_resume_preview_cache(user_id: str) -> dict[str, Any] | None:
    path = _resume_preview_cache_path(user_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_resume_preview_cache(user_id: str, payload: dict[str, Any]) -> None:
    path = _resume_preview_cache_path(user_id)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


_PREVIEW_STACK_KEYWORDS = [
    "Python", "Java", "Go", "C++", "Rust", "React", "Vue", "Node", "TypeScript", "JavaScript",
    "MySQL", "PostgreSQL", "Redis", "Kafka", "Docker", "Kubernetes", "LangChain", "RAG", "LLM",
]


def _extract_resume_preview_lines(resume_text: str) -> list[str]:
    lines = []
    for raw in re.split(r"[\r\n]+", resume_text or ""):
        line = re.sub(r"\s+", " ", raw).strip(" -•·\t")
        if len(line) < 6:
            continue
        if line in lines:
            continue
        lines.append(line)
    return lines


def _extract_resume_preview_signals(resume_text: str) -> dict[str, Any]:
    lines = _extract_resume_preview_lines(resume_text)
    project_lines = [line for line in lines if any(token in line for token in ("项目", "系统", "平台", "负责", "优化", "搭建", "设计"))][:4]
    metric_lines = [line for line in lines if re.search(r"\d+\s*(%|ms|s|年|月|人|次|万|w|k|qps|tps)", line, re.IGNORECASE)][:3]
    stack_tags = [keyword for keyword in _PREVIEW_STACK_KEYWORDS if keyword.lower() in (resume_text or "").lower()][:8]
    return {
        "project_lines": project_lines,
        "metric_lines": metric_lines,
        "stack_tags": stack_tags,
        "headline_lines": lines[:3],
    }


def _pick_recommended_control_id(target_role: str, signals: dict[str, Any]) -> tuple[str, str]:
    role = (target_role or "").lower()
    if any(token in role for token in ("实习", "校招", "应届", "junior", "intern")):
        return "friendly_training", "目标岗位更偏初阶表达校准，先把叙事讲顺更划算。"
    if any(token in role for token in ("leader", "manager", "负责人", "主管", "lead")):
        return "pressure_challenge", "目标岗位更看重现场判断、抗压和取舍，高压实战更贴近真实场景。"
    if any(token in role for token in ("架构", "专家", "资深", "高级", "principal", "staff", "senior")):
        return "deep_verification", "目标岗位对项目真实性和技术边界要求更高，适合深挖验证。"
    if len(signals.get("metric_lines", [])) >= 2 or len(signals.get("project_lines", [])) >= 3:
        return "deep_verification", "简历里可深挖的项目和结果信号比较多，适合直接做真实性和细节验证。"
    return "standard_interview", "先建立一场标准技术面基线，更方便后续再做压力或深挖加码。"


def _suggest_resume_interview_overrides(target_role: str, signals: dict[str, Any], preset_id: str) -> dict[str, str]:
    role = (target_role or "").lower()
    overrides = dict(DEFAULT_RESUME_INTERVIEW_OVERRIDES)
    if preset_id in {"deep_verification", "pressure_challenge"}:
        overrides["followup_style"] = "deep_dive"
    elif preset_id == "friendly_training":
        overrides["followup_style"] = "clarify_first"

    if any(token in role for token in ("后端", "架构", "平台", "infra", "算法", "ai", "开发")):
        overrides["focus_boost"] = "deep_followup"
    elif any(token in role for token in ("产品", "pm", "solution", "架构师", "规划")):
        overrides["focus_boost"] = "tradeoff"
    elif any(token in role for token in ("leader", "manager", "负责人", "主管", "lead")):
        overrides["focus_boost"] = "behavioral"
    elif signals.get("metric_lines"):
        overrides["focus_boost"] = "authenticity"

    if preset_id == "friendly_training":
        overrides["pressure_tuning"] = "same"
    elif preset_id == "pressure_challenge":
        overrides["pressure_tuning"] = "stronger"
    return normalize_resume_interview_overrides(overrides)


def build_resume_interview_preview_package(user_id: str, target_role: str, *, profile: dict[str, Any] | None = None) -> dict[str, Any]:
    from backend.indexer import read_resume_text

    role = (target_role or "").strip() or ((profile or {}).get("target_role") or "").strip()
    if not role:
        raise ValueError("请先填写目标岗位")

    resume_text = read_resume_text(user_id).strip()
    if not resume_text:
        raise ValueError("请先上传简历")

    resume_hash = hashlib.sha1(resume_text.encode("utf-8")).hexdigest()[:16]
    package_seed = f"{RESUME_INTERVIEW_CONTROL_VERSION}|{role}|{resume_hash}"
    package_id = hashlib.sha1(package_seed.encode("utf-8")).hexdigest()[:12]

    cached = _read_resume_preview_cache(user_id)
    if isinstance(cached, dict) and cached.get("id") == package_id:
        return cached

    signals = _extract_resume_preview_signals(resume_text)
    preset_id, reason = _pick_recommended_control_id(role, signals)
    suggested_overrides = _suggest_resume_interview_overrides(role, signals, preset_id)
    recommended_control = public_resume_interview_control(resolve_resume_interview_control(preset_id, strict=True))
    suggested_control = public_resume_interview_control(build_diy_resume_interview_control(preset_id, suggested_overrides))

    package = {
        "id": package_id,
        "version": RESUME_INTERVIEW_CONTROL_VERSION,
        "generated_at": datetime.now().isoformat(),
        "target_role": role,
        "resume_hash": resume_hash,
        "source": {
            "resume_length": len(resume_text),
            "target_role": role,
        },
        "resume_signals": signals,
        "recommended_preset_id": preset_id,
        "recommended_reason": reason,
        "recommended_control": recommended_control,
        "available_controls": list_resume_interview_controls(),
        "diy_options": deepcopy(RESUME_INTERVIEW_DIY_OPTIONS),
        "default_overrides": deepcopy(DEFAULT_RESUME_INTERVIEW_OVERRIDES),
        "suggested_overrides": suggested_overrides,
        "suggested_control": suggested_control,
        "notes": [
            "DIY 只在固定挡位底座上做有限调整，不会脱离当前预设的面试边界。",
            "如果你替换了简历或目标岗位变化较大，需要重新生成预览包。",
        ],
    }
    _write_resume_preview_cache(user_id, package)
    return package


def build_resume_interview_control_prompt(value: Any) -> str:
    control = resolve_resume_interview_control(value)
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
    diy_summary = control.get("diy_summary")
    lines = [
        "## 本场面试控制挡位",
        f"- 挡位: {control['name']}（{control['headline']}）",
        f"- 适合场景: {control['best_for']}",
        f"- 对候选人可见重点: {focus}",
    ]
    if diy_summary:
        lines.append(f"- DIY 调整: {diy_summary}")
    lines.extend([
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
    return "\n".join(lines)


def build_resume_interview_meta(
    target_role: str,
    preset_id: str | None,
    *,
    interview_control: dict[str, Any] | None = None,
    preview_package: dict[str, Any] | None = None,
) -> dict[str, Any]:
    control = public_resume_interview_control(interview_control or resolve_resume_interview_control(preset_id))
    meta = {
        "target_role": target_role,
        "interview_control_preset": control.get("base_preset_id") or control["id"],
        "interview_control_version": RESUME_INTERVIEW_CONTROL_VERSION,
        "interview_control": control,
    }
    if preview_package:
        meta["preview_package_id"] = preview_package.get("id")
        meta["preview_package"] = deepcopy(preview_package)
    return meta


def _message_role(message: Any) -> str:
    if isinstance(message, dict):
        return str(message.get("role") or "")
    return str(getattr(message, "type", "") or getattr(message, "role", "") or "")


def _message_content(message: Any) -> str:
    if isinstance(message, dict):
        return str(message.get("content") or "")
    return str(getattr(message, "content", "") or "")


def _looks_like_interviewer_prompt(text: str) -> bool:
    compact = re.sub(r"\s+", "", text or "")
    if not compact or len(compact) < 4:
        return False
    markers = ("？", "?", "请", "讲讲", "介绍", "为什么", "怎么", "如何", "如果", "假设", "是否", "有没有", "谈谈", "复盘")
    return any(marker in compact for marker in markers)


def _normalize_for_classification(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").lower())


def classify_resume_interviewer_prompt(text: str) -> tuple[str, dict[str, int]]:
    normalized = _normalize_for_classification(text)
    scores = {key: 0 for key in _BEHAVIOR_LABELS}

    for key, rules in _BEHAVIOR_CLASSIFIER_RULES.items():
        for keyword, weight in rules:
            if keyword in normalized:
                scores[key] += weight

    if any(marker in normalized for marker in ("如果", "假设", "要是")):
        scores["lateral_solution"] += 2
    if "为什么" in normalized and not any(marker in normalized for marker in ("为什么选", "为什么不用")):
        scores["deep_followup"] += 1
    if any(marker in normalized for marker in ("为什么选", "为什么不用", "值不值", "值得吗")):
        scores["tradeoff"] += 2
    if any(marker in normalized for marker in ("你本人", "你亲自", "你负责", "亲手")):
        scores["authenticity"] += 2
    if "项目" in normalized and any(marker in normalized for marker in ("指标", "上线", "落地", "数据")):
        scores["authenticity"] += 1
    if any(marker in normalized for marker in ("岗位", "团队", "业务", "公司")):
        scores["role_fit"] += 1
    if any(marker in normalized for marker in ("冲突", "协作", "复盘", "压力", "反馈")):
        scores["behavioral"] += 1

    best_key = max(
        scores,
        key=lambda key: (scores[key], -_BEHAVIOR_PRIORITY_INDEX.get(key, 999)),
    )
    if scores[best_key] <= 0:
        best_key = "clarification"
    return best_key, scores


def summarize_resume_interview_behavior(messages: list, interview_control: Any) -> dict[str, Any]:
    control = public_resume_interview_control(resolve_resume_interview_control(interview_control))
    target_profile = build_behavior_budget_profile(control)
    target_by_key = {item["key"]: item for item in target_profile}
    grouped_examples = {item["key"]: [] for item in target_profile}
    counts = {item["key"]: 0 for item in target_profile}
    prompts = []

    for message in messages or []:
        role = _message_role(message)
        if role not in ("ai", "assistant"):
            continue
        content = _message_content(message).strip()
        if not _looks_like_interviewer_prompt(content):
            continue
        prompts.append(content)
        bucket, _ = classify_resume_interviewer_prompt(content)
        counts[bucket] += 1
        if len(grouped_examples[bucket]) < 2:
            grouped_examples[bucket].append(content)

    total_prompts = len(prompts)
    distribution = []
    for item in target_profile:
        count = counts[item["key"]]
        actual_percent = _normalize_percent(count / total_prompts * 100) if total_prompts else 0
        delta = _normalize_percent(float(actual_percent) - float(item["percent"])) if total_prompts else _normalize_percent(-float(item["percent"]))
        alignment = "on_track"
        if total_prompts:
            if float(delta) >= 8:
                alignment = "above"
            elif float(delta) <= -8:
                alignment = "below"
        distribution.append({
            "key": item["key"],
            "label": item["label"],
            "count": count,
            "actual_percent": actual_percent,
            "target_percent": item["percent"],
            "delta": delta,
            "alignment": alignment,
            "examples": grouped_examples[item["key"]],
            "hint": item["hint"],
            "rank": item["rank"],
        })

    distribution.sort(
        key=lambda entry: (-entry["count"], -float(entry["target_percent"]), entry["label"]),
    )

    dominant_behaviors = [item for item in distribution if item["count"] > 0][:3]
    target_highlights = control.get("behavior_budget_highlights", [])
    target_highlight_keys = {item["key"] for item in target_highlights}
    matched_highlights = [item for item in dominant_behaviors if item["key"] in target_highlight_keys][:2]
    unexpected_highlights = [item for item in dominant_behaviors if item["key"] not in target_highlight_keys][:2]
    underplayed = [
        item for item in distribution
        if item["key"] in target_highlight_keys and item["count"] > 0 and item["alignment"] == "below"
    ][:2]

    if not total_prompts:
        alignment_summary = f"本场未捕获到足够的面试官追问样本，暂时无法判断「{control['name']}」的实际动作分布。"
    else:
        actual_labels = "、".join(item["label"] for item in dominant_behaviors[:2]) or "基础澄清"
        target_labels = "、".join(item["label"] for item in target_highlights[:2]) or "当前挡位重点"
        if matched_highlights:
            alignment_summary = (
                f"本场实际更常出现{actual_labels}，和「{control['name']}」预期的{target_labels}基本一致。"
            )
        else:
            alignment_summary = (
                f"本场实际更常出现{actual_labels}，相较「{control['name']}」预期的{target_labels}，"
                f"问法重心有明显偏移。"
            )

    notes = []
    if matched_highlights:
        notes.append(
            "命中的挡位重点：" + "、".join(item["label"] for item in matched_highlights)
        )
    if unexpected_highlights:
        notes.append(
            "实际比预期更突出的动作：" + "、".join(item["label"] for item in unexpected_highlights)
        )
    if underplayed:
        notes.append(
            "本场相对少一些的挡位重点：" + "、".join(item["label"] for item in underplayed)
        )

    return {
        "preset_id": control["id"],
        "preset_name": control["name"],
        "question_count": total_prompts,
        "budget_preview_summary": control.get("budget_preview_summary", ""),
        "budget_highlights": target_highlights,
        "sample_preview": control.get("sample_preview", []),
        "alignment_summary": alignment_summary,
        "dominant_behaviors": dominant_behaviors,
        "unexpected_highlights": unexpected_highlights,
        "notes": notes,
        "distribution": distribution,
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