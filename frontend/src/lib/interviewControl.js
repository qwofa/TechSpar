export const DEFAULT_RESUME_INTERVIEW_CONTROL_ID = "standard_interview";
export const DEFAULT_RESUME_INTERVIEW_OVERRIDES = {
  pressure_tuning: "same",
  followup_style: "balanced",
  focus_boost: "",
};

export const RESUME_INTERVIEW_DIY_OPTIONS = {
  pressure_tuning: [
    { id: "same", label: "保持当前压力", description: "沿用当前挡位的压力和节奏。" },
    { id: "lighter", label: "更友好一点", description: "先帮我把表达讲顺，再逐步进入追问。" },
    { id: "stronger", label: "更严格一点", description: "更快进入深挖、取舍和挑战场景。" },
  ],
  followup_style: [
    { id: "balanced", label: "均衡推进", description: "按当前挡位默认节奏推进。" },
    { id: "clarify_first", label: "先澄清再下钻", description: "先确认背景和职责，再做深追问。" },
    { id: "deep_dive", label: "更早进入深挖", description: "更快追到底层细节、边界和本人贡献。" },
  ],
  focus_boost: [
    { id: "", label: "不额外加码", description: "先按当前挡位默认重心推进。" },
    { id: "authenticity", label: "多验项目真实性", description: "更关注你本人做过什么、证据和线上结果。" },
    { id: "deep_followup", label: "多做技术深挖", description: "更关注实现细节、链路和边界。" },
    { id: "tradeoff", label: "多问方案取舍", description: "更关注为什么这样选、代价和替代方案。" },
    { id: "optimization", label: "多问优化扩展", description: "更关注性能、稳定性、规模化和维护性。" },
    { id: "role_fit", label: "多贴目标岗位", description: "更关注你的经历怎么映射到目标岗位。" },
    { id: "behavioral", label: "多验协作复盘", description: "更关注沟通、推进、冲突和复盘能力。" },
  ],
};

const BEHAVIOR_HINTS = {
  clarification: "先确认背景、上下文和候选人的真实表述。",
  deep_followup: "沿着一个回答继续往细节、机制和边界下钻。",
  lateral_solution: "把问题切到替代方案、迁移场景或变化条件。",
  tradeoff: "追问为什么这样选，以及为此承担了什么代价。",
  optimization: "继续问性能、稳定性、规模化和可维护性。",
  authenticity: "验证项目是否真做过、关键细节是否自洽。",
  role_fit: "把经历拉回目标岗位能力模型和业务场景。",
  behavioral: "用真实经历看协作、抗压、推进和复盘能力。",
};

const BEHAVIOR_BUDGETS = [
  { key: "clarification", label: "基础澄清" },
  { key: "deep_followup", label: "深度追问" },
  { key: "lateral_solution", label: "横向方案" },
  { key: "tradeoff", label: "方案取舍" },
  { key: "optimization", label: "优化扩展" },
  { key: "authenticity", label: "项目真实性验证" },
  { key: "role_fit", label: "岗位贴合" },
  { key: "behavioral", label: "行为验证" },
];

const SAMPLE_PREVIEWS = {
  friendly_training: [
    {
      budget_key: "clarification",
      prompt: "你先别急着讲结果，按背景、目标、你的职责和最终产出，把这个项目顺一遍。",
    },
    {
      budget_key: "authenticity",
      prompt: "这个优化里你本人亲自负责的是哪一段？如果把你抽掉，最难复现的部分是什么？",
    },
  ],
  standard_interview: [
    {
      budget_key: "deep_followup",
      prompt: "你刚才提到用了缓存，那我继续追一层：一致性、失效和击穿分别怎么处理？",
    },
    {
      budget_key: "tradeoff",
      prompt: "当时为什么选这个方案，而不是另一个更常见的做法？你接受了哪些代价？",
    },
  ],
  deep_verification: [
    {
      budget_key: "deep_followup",
      prompt: "你说这条链路是你主导的，那我们把请求路径拆开，从入口到落库一步一步讲。",
    },
    {
      budget_key: "authenticity",
      prompt: "这个指标提升是你真实在线上拿到的吗？观测口径、实验对照和回滚预案分别是什么？",
    },
  ],
  pressure_challenge: [
    {
      budget_key: "tradeoff",
      prompt: "如果现在延迟翻倍但预算不能加，你优先牺牲什么、保住什么？为什么？",
    },
    {
      budget_key: "lateral_solution",
      prompt: "假设现有技术栈突然不能用，你给我一个替代方案，并说清迁移代价。",
    },
  ],
};

export const RESUME_INTERVIEW_CONTROLS = [
  {
    id: "friendly_training",
    name: "友好训练",
    short_name: "友好",
    headline: "先把经历讲清楚",
    description: "更像教练，先帮你把背景、概念和项目表达捋顺。",
    best_for: "第一次练习、简历刚改完、表达还没收口",
    pressure_label: "低压",
    pace_label: "舒缓",
    visible_focus: ["表达梳理", "基础澄清", "轻度项目验证"],
    difference_note: "这档会先帮你把叙述讲顺，再慢慢进入验证，不会一上来就连续施压。",
    preview_highlight_keys: ["clarification", "authenticity"],
    behavior_budgets: {
      clarification: 24,
      deep_followup: 14,
      lateral_solution: 8,
      tradeoff: 10,
      optimization: 8,
      authenticity: 14,
      role_fit: 12,
      behavioral: 10,
    },
  },
  {
    id: "standard_interview",
    name: "标准面试",
    short_name: "标准",
    headline: "接近常规技术面",
    description: "节奏、压力和追问深度保持均衡，用来建立正式面试基线。",
    best_for: "正式投递前自测、建立能力基线",
    pressure_label: "中等",
    pace_label: "标准",
    visible_focus: ["技术理解", "项目细节", "方案取舍"],
    difference_note: "这档会在深挖、取舍和岗位匹配之间保持均衡，更接近多数正式技术面。",
    preview_highlight_keys: ["deep_followup", "tradeoff"],
    behavior_budgets: {
      clarification: 14,
      deep_followup: 18,
      lateral_solution: 12,
      tradeoff: 14,
      optimization: 12,
      authenticity: 14,
      role_fit: 10,
      behavioral: 6,
    },
  },
  {
    id: "deep_verification",
    name: "深挖验证",
    short_name: "深挖",
    headline: "验证项目是不是真懂",
    description: "明显提高项目真实性、技术细节、边界条件和取舍逻辑的追问比例。",
    best_for: "项目经历强、担心被追问穿、准备中高级面试",
    pressure_label: "中高",
    pace_label: "偏紧",
    visible_focus: ["项目真实性", "技术边界", "方案取舍"],
    difference_note: "这档会连续追项目细节和本人贡献，核心目标是验证你是不是真的做过、真的想明白了。",
    preview_highlight_keys: ["deep_followup", "authenticity"],
    behavior_budgets: {
      clarification: 8,
      deep_followup: 24,
      lateral_solution: 14,
      tradeoff: 18,
      optimization: 14,
      authenticity: 16,
      role_fit: 4,
      behavioral: 2,
    },
  },
  {
    id: "pressure_challenge",
    name: "高压实战",
    short_name: "高压",
    headline: "更接近强压面试现场",
    description: "节奏更紧，更多挑战、反问、横向迁移和方案取舍验证。",
    best_for: "冲刺高强度面试、终面压力场、检验抗压表达",
    pressure_label: "高",
    pace_label: "紧凑",
    visible_focus: ["压力追问", "横向迁移", "方案取舍"],
    difference_note: "这档会更快切场景、更频繁压条件，逼你当场做判断和取舍。",
    preview_highlight_keys: ["tradeoff", "lateral_solution"],
    behavior_budgets: {
      clarification: 6,
      deep_followup: 20,
      lateral_solution: 18,
      tradeoff: 20,
      optimization: 16,
      authenticity: 14,
      role_fit: 2,
      behavioral: 4,
    },
  },
];

const CONTROL_BY_ID = RESUME_INTERVIEW_CONTROLS.reduce((acc, item) => {
  acc[item.id] = item;
  return acc;
}, {});

function normalizePercent(value) {
  const rounded = Math.round(Number(value) * 10) / 10;
  return Number.isInteger(rounded) ? rounded : rounded;
}

function buildBehaviorBudgetProfile(control) {
  const budgets = control?.behavior_budgets || {};
  const total = Object.values(budgets).reduce((sum, value) => sum + Math.max(0, Number(value) || 0), 0) || 1;
  const items = BEHAVIOR_BUDGETS.map((item) => {
    const weight = Math.max(0, Number(budgets[item.key]) || 0);
    return {
      key: item.key,
      label: item.label,
      weight: normalizePercent(weight),
      percent: normalizePercent((weight / total) * 100),
      hint: BEHAVIOR_HINTS[item.key] || "",
    };
  }).sort((a, b) => Number(b.percent) - Number(a.percent) || a.label.localeCompare(b.label, "zh-CN"));

  return items.map((item, index) => ({
    ...item,
    rank: index + 1,
    emphasis: index < 2 ? "high" : Number(item.percent) >= 12 ? "medium" : "low",
  }));
}

function buildBehaviorBudgetHighlights(control, limit = 2) {
  const profile = buildBehaviorBudgetProfile(control);
  const byKey = Object.fromEntries(profile.map((item) => [item.key, item]));
  const selected = [];

  for (const key of control?.preview_highlight_keys || []) {
    const item = byKey[key];
    if (item && !selected.includes(item)) selected.push(item);
    if (selected.length >= limit) break;
  }

  for (const item of profile) {
    if (selected.length >= limit) break;
    if (!selected.includes(item)) selected.push(item);
  }

  return selected.slice(0, limit).map((item) => ({
    key: item.key,
    label: item.label,
    percent: item.percent,
    hint: item.hint,
    rank: item.rank,
  }));
}

function buildBudgetPreviewSummary(highlights) {
  if (!highlights?.length) return "";
  if (highlights.length === 1) return `本档更常出现${highlights[0].label}类问题。`;
  return `本档更常出现${highlights[0].label}和${highlights[1].label}类问题。`;
}

function buildSamplePreview(control) {
  return (SAMPLE_PREVIEWS[control?.id] || []).map((item) => ({
    budget_key: item.budget_key,
    label: BEHAVIOR_BUDGETS.find((budget) => budget.key === item.budget_key)?.label || item.budget_key,
    hint: BEHAVIOR_HINTS[item.budget_key] || "",
    prompt: item.prompt,
  }));
}

function clampIndex(current, order, step) {
  const index = order.indexOf(current);
  if (index < 0) return current;
  return order[Math.max(0, Math.min(order.length - 1, index + step))];
}

function normalizeBudgetMap(budgets = {}) {
  const keys = BEHAVIOR_BUDGETS.map((item) => item.key);
  const cleaned = Object.fromEntries(keys.map((key) => [key, Math.max(0, Number(budgets[key]) || 0)]));
  const total = Object.values(cleaned).reduce((sum, value) => sum + value, 0) || 1;
  const normalized = Object.fromEntries(keys.map((key) => [key, (cleaned[key] / total) * 100]));
  const rounded = Object.fromEntries(keys.map((key) => [key, Math.round(normalized[key])]));
  let delta = 100 - Object.values(rounded).reduce((sum, value) => sum + value, 0);

  const remainders = [...keys].sort((a, b) => (normalized[b] - rounded[b]) - (normalized[a] - rounded[a]));
  while (delta !== 0) {
    const list = delta > 0 ? remainders : [...remainders].reverse();
    let changed = false;
    for (const key of list) {
      if (delta === 0) break;
      const next = rounded[key] + (delta > 0 ? 1 : -1);
      if (next < 0) continue;
      rounded[key] = next;
      delta += delta > 0 ? -1 : 1;
      changed = true;
    }
    if (!changed) break;
  }

  return rounded;
}

export function normalizeResumeInterviewOverrides(input) {
  const raw = input || {};
  return {
    pressure_tuning: RESUME_INTERVIEW_DIY_OPTIONS.pressure_tuning.some((item) => item.id === raw.pressure_tuning)
      ? raw.pressure_tuning
      : DEFAULT_RESUME_INTERVIEW_OVERRIDES.pressure_tuning,
    followup_style: RESUME_INTERVIEW_DIY_OPTIONS.followup_style.some((item) => item.id === raw.followup_style)
      ? raw.followup_style
      : DEFAULT_RESUME_INTERVIEW_OVERRIDES.followup_style,
    focus_boost: RESUME_INTERVIEW_DIY_OPTIONS.focus_boost.some((item) => item.id === raw.focus_boost)
      ? raw.focus_boost
      : DEFAULT_RESUME_INTERVIEW_OVERRIDES.focus_boost,
  };
}

function appendVisibleFocus(control, ...items) {
  const next = [];
  for (const item of [...(control.visible_focus || []), ...items.filter(Boolean)]) {
    if (!next.includes(item)) next.push(item);
  }
  control.visible_focus = next.slice(0, 4);
}

function summarizeDiyOverrides(overrides) {
  const labels = [];
  for (const key of ["pressure_tuning", "followup_style", "focus_boost"]) {
    const option = RESUME_INTERVIEW_DIY_OPTIONS[key].find((item) => item.id === overrides[key]);
    if (!option || option.id === DEFAULT_RESUME_INTERVIEW_OVERRIDES[key]) continue;
    labels.push(option.label);
  }
  if (!labels.length) return "沿用固定挡位默认节奏。";
  return `本场在固定挡位底座上额外调整为：${labels.join(" / ")}。`;
}

export function buildDIYResumeInterviewControl(input, overridesInput) {
  const base = normalizeResumeInterviewControl(input);
  const overrides = normalizeResumeInterviewOverrides(overridesInput);
  const control = {
    ...base,
    control_axes: { ...(base.control_axes || {}) },
    behavior_budgets: { ...(base.behavior_budgets || {}) },
    visible_focus: [...(base.visible_focus || [])],
    base_preset_id: base.base_preset_id || base.id,
    base_preset_name: base.base_preset_name || base.name,
    diy_overrides: overrides,
  };

  if (overrides.pressure_tuning === "lighter") {
    control.behavior_budgets = normalizeBudgetMap({
      ...control.behavior_budgets,
      clarification: (control.behavior_budgets.clarification || 0) + 6,
      role_fit: (control.behavior_budgets.role_fit || 0) + 3,
      tradeoff: Math.max(0, (control.behavior_budgets.tradeoff || 0) - 3),
      lateral_solution: Math.max(0, (control.behavior_budgets.lateral_solution || 0) - 3),
      optimization: Math.max(0, (control.behavior_budgets.optimization || 0) - 3),
    });
    control.pressure_label = clampIndex(control.pressure_label, ["低压", "中等", "中高", "高"], -1);
    control.pace_label = clampIndex(control.pace_label, ["舒缓", "标准", "偏紧", "紧凑"], -1);
    control.control_axes = {
      ...control.control_axes,
      pressure: clampIndex(control.control_axes?.pressure || "中", ["低", "中", "中高", "高"], -1),
      pace: clampIndex(control.control_axes?.pace || "标准", ["舒缓", "标准", "偏紧", "紧凑"], -1),
      verification: "先让候选人把背景说清，再逐步进入验证",
    };
    appendVisibleFocus(control, "先讲顺再验证");
  }

  if (overrides.pressure_tuning === "stronger") {
    control.behavior_budgets = normalizeBudgetMap({
      ...control.behavior_budgets,
      deep_followup: (control.behavior_budgets.deep_followup || 0) + 4,
      tradeoff: (control.behavior_budgets.tradeoff || 0) + 3,
      lateral_solution: (control.behavior_budgets.lateral_solution || 0) + 3,
      clarification: Math.max(0, (control.behavior_budgets.clarification || 0) - 4),
      role_fit: Math.max(0, (control.behavior_budgets.role_fit || 0) - 3),
      behavioral: Math.max(0, (control.behavior_budgets.behavioral || 0) - 3),
    });
    control.pressure_label = clampIndex(control.pressure_label, ["低压", "中等", "中高", "高"], 1);
    control.pace_label = clampIndex(control.pace_label, ["舒缓", "标准", "偏紧", "紧凑"], 1);
    control.control_axes = {
      ...control.control_axes,
      pressure: clampIndex(control.control_axes?.pressure || "中", ["低", "中", "中高", "高"], 1),
      pace: clampIndex(control.control_axes?.pace || "标准", ["舒缓", "标准", "偏紧", "紧凑"], 1),
      verification: "更快进入深挖、取舍和条件压测",
    };
    appendVisibleFocus(control, "更快进入深挖");
  }

  if (overrides.followup_style === "clarify_first") {
    control.behavior_budgets = normalizeBudgetMap({
      ...control.behavior_budgets,
      clarification: (control.behavior_budgets.clarification || 0) + 6,
      deep_followup: Math.max(0, (control.behavior_budgets.deep_followup || 0) - 3),
      authenticity: Math.max(0, (control.behavior_budgets.authenticity || 0) - 2),
      tradeoff: Math.max(0, (control.behavior_budgets.tradeoff || 0) - 1),
    });
    control.control_axes = {
      ...control.control_axes,
      verification: "先澄清角色、背景和职责，再往细节下钻",
    };
    appendVisibleFocus(control, "先澄清再下钻");
  }

  if (overrides.followup_style === "deep_dive") {
    control.behavior_budgets = normalizeBudgetMap({
      ...control.behavior_budgets,
      clarification: Math.max(0, (control.behavior_budgets.clarification || 0) - 4),
      deep_followup: (control.behavior_budgets.deep_followup || 0) + 4,
      authenticity: (control.behavior_budgets.authenticity || 0) + 2,
      tradeoff: (control.behavior_budgets.tradeoff || 0) + 2,
    });
    control.control_axes = {
      ...control.control_axes,
      verification: "更早进入底层细节、边界和本人贡献验证",
    };
    appendVisibleFocus(control, "更早进入深挖");
  }

  if (overrides.focus_boost) {
    const focusLabel = BEHAVIOR_BUDGETS.find((item) => item.key === overrides.focus_boost)?.label || overrides.focus_boost;
    const budgets = { ...control.behavior_budgets, [overrides.focus_boost]: (control.behavior_budgets[overrides.focus_boost] || 0) + 8 };
    let remaining = 8;
    for (const key of ["clarification", "role_fit", "behavioral", "lateral_solution", "optimization", "tradeoff", "authenticity", "deep_followup"]) {
      if (key === overrides.focus_boost || remaining <= 0) continue;
      const available = Math.max(0, (budgets[key] || 0) - 1);
      const taken = Math.min(available, remaining);
      budgets[key] = (budgets[key] || 0) - taken;
      remaining -= taken;
    }
    control.behavior_budgets = normalizeBudgetMap(budgets);
    control.control_axes = {
      ...control.control_axes,
      focus: `在当前挡位基础上，额外提高${focusLabel}比重`,
    };
    appendVisibleFocus(control, focusLabel);
  }

  const changed = JSON.stringify(overrides) !== JSON.stringify(DEFAULT_RESUME_INTERVIEW_OVERRIDES);
  control.origin = changed ? "diy" : "preset";
  control.is_diy_adjusted = changed;
  control.diy_summary = summarizeDiyOverrides(overrides);
  if (changed) {
    control.headline = `${base.headline} · 有限 DIY`;
    control.description = `${base.description} 这场额外做了有限 DIY 调整。`.trim();
    control.difference_note = `${base.difference_note || ""} ${control.diy_summary}`.trim();
  }

  return normalizeResumeInterviewControl(control);
}

export function normalizeResumeInterviewControl(input) {
  const raw = typeof input === "string" ? { id: input } : input || {};
  const id = raw.id || raw.preset_id || raw.interview_control_preset || DEFAULT_RESUME_INTERVIEW_CONTROL_ID;
  const fallback = CONTROL_BY_ID[id] || CONTROL_BY_ID[DEFAULT_RESUME_INTERVIEW_CONTROL_ID];
  const merged = {
    ...fallback,
    ...raw,
    id: fallback.id,
    visible_focus: raw.visible_focus || fallback.visible_focus,
    behavior_budgets: raw.behavior_budgets || fallback.behavior_budgets,
    difference_note: raw.difference_note || fallback.difference_note,
  };
  merged.behavior_budget_profile = raw.behavior_budget_profile || buildBehaviorBudgetProfile(merged);
  merged.behavior_budget_highlights = raw.behavior_budget_highlights || buildBehaviorBudgetHighlights(merged);
  merged.budget_preview_summary = raw.budget_preview_summary || buildBudgetPreviewSummary(merged.behavior_budget_highlights);
  merged.sample_preview = raw.sample_preview || buildSamplePreview(merged);
  return merged;
}

export function readResumeInterviewControl(payload) {
  return normalizeResumeInterviewControl(
    payload?.interview_control ||
    payload?.meta?.interview_control ||
    payload?.interview_control_preset ||
    payload?.meta?.interview_control_preset
  );
}

export function resumeInterviewControlTitle(input) {
  const control = normalizeResumeInterviewControl(input);
  return `${control.name} · ${control.pressure_label}`;
}