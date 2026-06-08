export const DEFAULT_RESUME_INTERVIEW_CONTROL_ID = "standard_interview";

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

export function normalizeResumeInterviewControl(input) {
  const raw = typeof input === "string" ? { id: input } : input || {};
  const id = raw.id || raw.preset_id || raw.interview_control_preset || DEFAULT_RESUME_INTERVIEW_CONTROL_ID;
  const fallback = CONTROL_BY_ID[id] || CONTROL_BY_ID[DEFAULT_RESUME_INTERVIEW_CONTROL_ID];
  return {
    ...fallback,
    ...raw,
    id: fallback.id,
    visible_focus: raw.visible_focus || fallback.visible_focus,
    behavior_budgets: raw.behavior_budgets || fallback.behavior_budgets,
  };
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