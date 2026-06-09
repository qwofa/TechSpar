import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, ChevronRight, CalendarDays, UploadCloud, CheckCircle2, Clock, Play, Briefcase, Sparkles } from "lucide-react";
import { getResumeStatus, uploadResume, startInterview, getHistory, getProfile, inferTargetRole, previewResumeInterview } from "../api/interview";
import { useSessionLauncher } from "../hooks/useSessionLauncher";
import {
  DEFAULT_RESUME_INTERVIEW_CONTROL_ID,
  DEFAULT_RESUME_INTERVIEW_OVERRIDES,
  RESUME_INTERVIEW_CONTROLS,
  RESUME_INTERVIEW_DIY_OPTIONS,
  buildDIYResumeInterviewControl,
  normalizeResumeInterviewControl,
  readResumeInterviewControl,
} from "../lib/interviewControl";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

const INTERVIEW_STEPS = [
  { title: "自我介绍", desc: "基于简历背景做自我介绍，考察表达与提炼能力" },
  { title: "项目深挖", desc: "面试官针对高光项目追问细节，挖掘经历真实度" },
  { title: "技术追问", desc: "结合您的技术栈深入考察，探测技术点掌握边界" },
  { title: "总结反馈", desc: "出具维度清晰的评分报告与薄弱点改进建议" },
];

function ScorePill({ score }) {
  if (score == null) {
    return (
      <Badge variant="secondary" className="min-w-[64px] justify-center rounded-full px-2.5 py-1 text-[12px] bg-hover text-dim border-none font-medium tracking-wide">
        未评分
      </Badge>
    );
  }
  let bg, color;
  if (score >= 8) { bg = "rgba(34,197,94,0.12)"; color = "var(--success)"; }
  else if (score >= 6) { bg = "rgba(245,158,11,0.12)"; color = "var(--ai-glow)"; }
  else if (score >= 4) { bg = "rgba(253,203,110,0.15)"; color = "#e2b93b"; }
  else { bg = "rgba(239,68,68,0.12)"; color = "var(--destructive)"; }
  return (
    <Badge
      variant="outline"
      className="min-w-[64px] justify-center rounded-full px-2.5 py-1 font-bold text-[13px] shadow-sm tracking-wide"
      style={{ background: bg, borderColor: "transparent", color }}
    >
      {score}/10
    </Badge>
  );
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function ControlPreviewPanel({ control }) {
  const highlights = control.behavior_budget_highlights || [];

  return (
    <div className="mt-5 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
      <div className="rounded-2xl border border-border/70 bg-background/60 px-4 py-4 md:px-5">
        <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
          <div>
            <div className="text-[13px] font-semibold text-text">预算画像预览</div>
            <div className="mt-1 text-[12px] text-dim">开始前先看这档更常把问题问向哪里</div>
          </div>
          <Badge variant="secondary">{control.budget_preview_summary}</Badge>
        </div>
        <div className="grid gap-2.5">
          {(control.behavior_budget_profile || []).map((item) => {
            const accent = item.emphasis === "high"
              ? "var(--primary)"
              : item.emphasis === "medium"
                ? "var(--ai-glow)"
                : "rgba(148,163,184,0.7)";
            return (
              <div key={item.key}>
                <div className="mb-1.5 flex items-center justify-between gap-3 text-[12px]">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="font-medium text-text truncate">{item.label}</span>
                    {item.rank <= 2 && <Badge variant="outline">高亮</Badge>}
                  </div>
                  <span className="text-dim shrink-0">{item.percent}%</span>
                </div>
                <div className="h-2 rounded-full bg-hover overflow-hidden">
                  <div className="h-full rounded-full transition-[width] duration-300" style={{ width: `${item.percent}%`, background: accent }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="rounded-2xl border border-border/70 bg-background/60 px-4 py-4 md:px-5">
        <div className="text-[13px] font-semibold text-text">样题预览</div>
        <div className="mt-1 text-[12px] text-dim">预览固定高亮两组最明显的动作差异</div>
        <div className="mt-3 flex flex-wrap gap-2">
          {highlights.map((item) => (
            <Badge key={item.key} variant="outline">
              {item.label} · {item.percent}%
            </Badge>
          ))}
        </div>
        <div className="mt-4 flex flex-col gap-3">
          {(control.sample_preview || []).map((sample) => (
            <div key={`${control.id}-${sample.budget_key}`} className="rounded-xl border border-border/60 bg-card/70 px-3.5 py-3">
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <Badge variant="secondary">{sample.label}</Badge>
                <span className="text-[11px] text-dim">{sample.hint}</span>
              </div>
              <div className="text-[13px] leading-6 text-text">{sample.prompt}</div>
            </div>
          ))}
        </div>
        {control.difference_note && (
          <div className="mt-4 rounded-xl border border-primary/15 bg-primary/6 px-3.5 py-3 text-[12px] leading-5 text-dim">
            {control.difference_note}
          </div>
        )}
      </div>
    </div>
  );
}

function PreviewPackagePanel({ previewPackage, previewLoading, previewError, effectiveControl }) {
  if (previewLoading) {
    return <Skeleton className="mt-6 h-[220px] rounded-2xl w-full" />;
  }

  if (previewError) {
    return (
      <div className="mt-6 rounded-2xl border border-red/20 bg-red/10 px-4 py-4 text-sm text-red">
        {previewError}
      </div>
    );
  }

  if (!previewPackage) return null;

  const signals = previewPackage.resume_signals || {};

  return (
    <div className="mt-6 rounded-2xl border border-primary/20 bg-primary/5 px-4 py-4 md:px-5">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <div className="text-[13px] font-semibold text-text">预生成包</div>
          <div className="mt-1 text-[12px] leading-5 text-dim">
            {previewPackage.recommended_reason}
          </div>
        </div>
        <Badge variant="outline">包 ID · {previewPackage.id}</Badge>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Badge variant="secondary">推荐挡位 · {previewPackage.recommended_control?.name || effectiveControl.name}</Badge>
        <Badge variant="secondary">当前启动 · {effectiveControl.name}</Badge>
        {effectiveControl.is_diy_adjusted && <Badge variant="outline">已做有限 DIY</Badge>}
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-border/60 bg-background/70 px-3.5 py-3">
          <div className="text-[12px] font-semibold text-text">简历抬头线索</div>
          <div className="mt-2 flex flex-col gap-1.5 text-[12px] text-dim leading-5">
            {(signals.headline_lines || []).slice(0, 3).map((item) => <div key={item}>{item}</div>)}
          </div>
        </div>
        <div className="rounded-xl border border-border/60 bg-background/70 px-3.5 py-3">
          <div className="text-[12px] font-semibold text-text">项目 / 指标信号</div>
          <div className="mt-2 flex flex-col gap-1.5 text-[12px] text-dim leading-5">
            {[...(signals.project_lines || []).slice(0, 2), ...(signals.metric_lines || []).slice(0, 1)].map((item) => <div key={item}>{item}</div>)}
          </div>
        </div>
        <div className="rounded-xl border border-border/60 bg-background/70 px-3.5 py-3">
          <div className="text-[12px] font-semibold text-text">识别到的技术栈</div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {(signals.stack_tags || []).length ? (signals.stack_tags || []).map((item) => (
              <span key={item} className="rounded-full bg-hover px-2 py-1 text-[11px] text-dim">{item}</span>
            )) : <span className="text-[12px] text-dim">当前未提取到明显技术栈标签</span>}
          </div>
        </div>
      </div>
    </div>
  );
}

function DIYOptionGroup({ title, description, value, options, onChange }) {
  return (
    <div className="rounded-2xl border border-border/70 bg-background/60 px-4 py-4">
      <div className="text-[13px] font-semibold text-text">{title}</div>
      <div className="mt-1 text-[12px] text-dim">{description}</div>
      <div className="mt-3 grid gap-2">
        {options.map((option) => {
          const active = value === option.id;
          return (
            <button
              key={`${title}-${option.id}`}
              type="button"
              className={cn(
                "rounded-xl border px-3.5 py-3 text-left transition-all",
                active ? "border-primary/45 bg-primary/10" : "border-border/60 bg-card/55 hover:border-primary/30 hover:bg-primary/5"
              )}
              onClick={() => onChange(option.id)}
            >
              <div className="text-[13px] font-medium text-text">{option.label}</div>
              <div className="mt-1 text-[12px] leading-5 text-dim">{option.description}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function ResumeInterview() {
  const navigate = useNavigate();
  const [resumeFile, setResumeFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [targetRole, setTargetRole] = useState("");
  const [targetRoleInferring, setTargetRoleInferring] = useState(false);
  const [selectedControlId, setSelectedControlId] = useState(DEFAULT_RESUME_INTERVIEW_CONTROL_ID);
  const [controlTouched, setControlTouched] = useState(false);
  const [diyOverrides, setDiyOverrides] = useState(() => ({ ...DEFAULT_RESUME_INTERVIEW_OVERRIDES }));
  const [diyTouched, setDiyTouched] = useState(false);
  const [previewPackage, setPreviewPackage] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");
  const launcher = useSessionLauncher({ key: "resume", navigate });
  const loading = launcher.loading;
  const selectedControl = normalizeResumeInterviewControl(selectedControlId);
  const effectiveControl = buildDIYResumeInterviewControl(selectedControl, diyOverrides);

  const autoInferRole = async () => {
    setTargetRoleInferring(true);
    try {
      const { target_role } = await inferTargetRole();
      if (target_role) setTargetRole(target_role);
    } catch {
      // Silent fallback — user can type manually.
    } finally {
      setTargetRoleInferring(false);
    }
  };

  useEffect(() => {
    Promise.all([
      getResumeStatus().catch(() => ({ has_resume: false })),
      getProfile().catch(() => ({})),
    ]).then(([s, p]) => {
      if (s.has_resume) setResumeFile({ filename: s.filename, size: s.size });
      const existing = (p?.target_role || "").trim();
      if (existing) {
        setTargetRole(existing);
      } else if (s.has_resume) {
        autoInferRole();
      }
    }).finally(() => setPageLoading(false));

    getHistory(3, 0, "resume")
      .then((data) => setHistory(data.items || []))
      .catch(() => {})
      .finally(() => setHistoryLoading(false));
  }, []);

  useEffect(() => {
    if (!resumeFile) {
      setPreviewPackage(null);
      setPreviewError("");
      setPreviewLoading(false);
      return;
    }

    const role = targetRole.trim();
    if (!role) {
      setPreviewPackage(null);
      setPreviewError("");
      return;
    }

    let cancelled = false;
    setPreviewLoading(true);
    setPreviewError("");

    previewResumeInterview(role)
      .then((data) => {
        if (cancelled) return;
        const nextPreview = data?.preview_package || null;
        setPreviewPackage(nextPreview);

        if (!nextPreview) return;

        if (!controlTouched) {
          setSelectedControlId(nextPreview.recommended_preset_id || DEFAULT_RESUME_INTERVIEW_CONTROL_ID);
        }

        if (!diyTouched) {
          setDiyOverrides({
            ...DEFAULT_RESUME_INTERVIEW_OVERRIDES,
            ...(nextPreview.suggested_overrides || nextPreview.default_overrides || {}),
          });
        }
      })
      .catch((err) => {
        if (cancelled) return;
        setPreviewPackage(null);
        setPreviewError(`预生成包生成失败: ${err.message}`);
      })
      .finally(() => {
        if (!cancelled) {
          setPreviewLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [resumeFile, targetRole, controlTouched, diyTouched]);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const hadResume = !!resumeFile;
    try {
      const data = await uploadResume(file);
      setResumeFile({ filename: data.filename, size: data.size });
      setPreviewPackage(null);
      setPreviewError("");
      setControlTouched(false);
      setDiyTouched(false);
      setSelectedControlId(DEFAULT_RESUME_INTERVIEW_CONTROL_ID);
      setDiyOverrides({ ...DEFAULT_RESUME_INTERVIEW_OVERRIDES });
      if (!hadResume && !targetRole.trim()) {
        await autoInferRole();
      }
    } catch (err) {
      alert("上传失败: " + err.message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleSelectControl = (controlId) => {
    setSelectedControlId(controlId);
    setControlTouched(true);
  };

  const handleChangeOverride = (key, value) => {
    setDiyOverrides((current) => ({
      ...current,
      [key]: value,
    }));
    setDiyTouched(true);
  };

  const handleResetToSuggested = () => {
    setControlTouched(false);
    setDiyTouched(false);
    setSelectedControlId(previewPackage?.recommended_preset_id || DEFAULT_RESUME_INTERVIEW_CONTROL_ID);
    setDiyOverrides({
      ...DEFAULT_RESUME_INTERVIEW_OVERRIDES,
      ...(previewPackage?.suggested_overrides || previewPackage?.default_overrides || {}),
    });
  };

  const handleStart = async () => {
    if (!resumeFile) return;
    const role = targetRole.trim();
    if (!role || !previewPackage) return;
    await launcher.launch(() => startInterview("resume", null, {
      targetRole: role,
      interviewControlPreset: selectedControl.id,
      previewPackageId: previewPackage.id,
      interviewControlOverrides: diyOverrides,
    }));
  };

  return (
    <div className="flex-1 w-full max-w-[800px] mx-auto px-4 py-8 md:px-8 md:py-10 animate-in fade-in duration-500">
      {/* 头部区域 */}
      <div className="mb-10">
        <div className="flex items-center gap-3.5 mb-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center shadow-sm border border-primary/10">
            <FileText size={24} className="text-primary" />
          </div>
          <div className="text-3xl md:text-[34px] font-display font-bold tracking-tight text-text">简历模拟面试</div>
        </div>
        <div className="text-[15px] text-dim/90 max-w-[90%] leading-relaxed">
          上传简历即可开启1对1高度定制的实战仿真演练，让 AI 面试官对你的经历提出致命追问。
        </div>
      </div>

      {/* 核心动作区域大卡片 */}
      <Card className="mb-12 border-border/60 shadow-md bg-card/60 backdrop-blur-sm overflow-hidden rounded-3xl">
        <div className="h-1 bg-gradient-to-r from-primary/30 via-primary to-primary/30 w-full opacity-80" />
        <CardContent className="p-6 md:p-8">
          <div className="mb-5 flex items-center justify-between">
            <div className="font-semibold text-text flex items-center gap-2">
              <span className="w-1.5 h-4 bg-primary rounded-full inline-block" /> 候选人资产就绪状态
            </div>
            {resumeFile && (
              <Badge variant="outline" className="bg-success/10 border-success/30 text-success font-medium tracking-wider px-3 shadow-sm">
                <CheckCircle2 size={13} className="mr-1.5" /> 简历已解析
              </Badge>
            )}
          </div>

          <div className="min-h-[140px] relative">
            {pageLoading ? (
              <Skeleton className="h-[140px] rounded-2xl w-full" />
            ) : resumeFile ? (
              <div className="group overflow-hidden rounded-2xl border-2 border-primary/20 bg-primary/5 p-5 md:p-6 transition-all hover:bg-primary/10 hover:border-primary/40 relative">
                {/* 装饰性光晕 */}
                <div className="absolute top-0 right-0 -mt-10 -mr-10 w-40 h-40 bg-primary/10 blur-[40px] rounded-full point-events-none" />
                
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-5 relative z-10">
                  <div className="flex items-start gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-card border border-primary/20 flex shrink-0 items-center justify-center shadow-lg shadow-primary/5">
                      <FileText size={26} className="text-primary drop-shadow-sm" />
                    </div>
                    <div className="flex flex-col justify-center h-14">
                      <div className="font-bold text-text text-[16px] break-all">{resumeFile.filename}</div>
                      <div className="text-[13px] text-dim font-medium tracking-wide">DOC SIZE: {(resumeFile.size / 1024).toFixed(0)} KB</div>
                    </div>
                  </div>
                  
                  <label className={cn("cursor-pointer shrink-0 mt-2 sm:mt-0", uploading && "opacity-50 pointer-events-none")}>
                    <Button variant="outline" size="sm" asChild className="rounded-xl h-10 px-5 font-medium hover:bg-primary hover:text-primary-foreground transition-all hover:border-primary">
                      <span>{uploading ? "解析替换中..." : "替换新版本..."}</span>
                    </Button>
                    <input type="file" accept=".pdf" className="hidden" onChange={handleUpload} disabled={uploading} />
                  </label>
                </div>
              </div>
            ) : (
              <label className={cn(
                "flex flex-col items-center justify-center gap-4 px-6 md:px-10 py-12 bg-card/40 border-[2px] border-dashed border-border/80 rounded-2xl cursor-pointer transition-all hover:border-primary/50 hover:bg-primary/5 group",
                uploading && "opacity-50 pointer-events-none scale-[0.98]"
              )}>
                <div className="w-16 h-16 rounded-full bg-hover group-hover:bg-primary/10 flex items-center justify-center transition-all group-hover:scale-110 duration-300">
                  <UploadCloud size={30} className="text-dim/80 group-hover:text-primary transition-colors" />
                </div>
                <div className="text-center">
                  <span className="font-bold text-text text-[16px] block mb-1.5 transition-colors group-hover:text-primary">
                    {uploading ? "正在安全读取您的电子简历..." : "点击或拖拽您的 PDF 简历至此"}
                  </span>
                  <span className="text-[13px] text-dim font-medium px-4 py-1.5 rounded-full bg-hover/80 text-dim">
                    仅支持 PDF 格式 · 建议文件不超过 20MB
                  </span>
                </div>
                <input type="file" accept=".pdf" className="hidden" onChange={handleUpload} disabled={uploading} />
              </label>
            )}
          </div>

          <div className="mt-6 pt-5 border-t border-border/50">
            <div className="flex items-center gap-2 mb-2.5">
              <Briefcase size={14} className="text-dim" />
              <label className="text-[13px] font-semibold text-text">本次面试目标岗位</label>
            </div>
            <div className="flex gap-2">
              <Input
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder={targetRoleInferring ? "正在根据简历推断..." : "如：AI 应用开发工程师 / 后端开发实习生"}
                disabled={targetRoleInferring}
                className="h-10 flex-1"
              />
              <Button
                variant="outline"
                size="sm"
                className="h-10 px-3 shrink-0"
                disabled={!resumeFile || targetRoleInferring}
                onClick={autoInferRole}
                title="根据简历重新推断"
              >
                <Sparkles size={14} className={cn(targetRoleInferring && "animate-spin")} />
              </Button>
            </div>
            <div className="text-[12px] text-dim mt-1.5">面试官会按该岗位方向调整考察重点与追问深度</div>
          </div>

          <div className="mt-6 pt-5 border-t border-border/50">
            <div className="flex items-center justify-between gap-3 mb-3">
              <div>
                <div className="text-[13px] font-semibold text-text">面试挡位</div>
                <div className="mt-1 text-[12px] text-dim">挡位会写入本次会话，并影响追问压力、节奏和复盘上下文</div>
              </div>
              <Badge variant="outline" className="shrink-0">
                {effectiveControl.pressure_label} · {effectiveControl.pace_label}
              </Badge>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {RESUME_INTERVIEW_CONTROLS.map((control) => {
                const active = selectedControlId === control.id;
                return (
                  <button
                    key={control.id}
                    type="button"
                    className={cn(
                      "rounded-2xl border p-4 text-left transition-all bg-card/55 hover:border-primary/35 hover:bg-primary/5",
                      active ? "border-primary/45 bg-primary/10 shadow-sm shadow-primary/10" : "border-border/70"
                    )}
                    onClick={() => handleSelectControl(control.id)}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-semibold text-text">{control.name}</div>
                      <Badge variant={active ? "default" : "secondary"}>{control.short_name}</Badge>
                    </div>
                    <div className="mt-1 text-[13px] font-medium text-primary">{control.headline}</div>
                    <div className="mt-2 text-[12px] leading-5 text-dim">{control.description}</div>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {control.visible_focus.map((item) => (
                        <span key={item} className="rounded-full bg-hover px-2 py-1 text-[11px] text-dim">
                          {item}
                        </span>
                      ))}
                    </div>
                  </button>
                );
              })}
            </div>

            <PreviewPackagePanel
              previewPackage={previewPackage}
              previewLoading={previewLoading}
              previewError={previewError}
              effectiveControl={effectiveControl}
            />

            <div className="mt-6 rounded-2xl border border-border/70 bg-card/40 p-4 md:p-5">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div>
                  <div className="text-[13px] font-semibold text-text">有限 DIY 调整</div>
                  <div className="mt-1 text-[12px] text-dim">只允许在当前挡位底座上微调压力、追问风格和额外关注点，不会脱离该挡位边界。</div>
                </div>
                <div className="flex items-center gap-2 flex-wrap justify-end">
                  {previewPackage?.suggested_control?.is_diy_adjusted && !diyTouched && (
                    <Badge variant="secondary">已套用系统建议</Badge>
                  )}
                  {effectiveControl.is_diy_adjusted && <Badge variant="outline">当前已启用 DIY</Badge>}
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-8 px-3"
                    onClick={handleResetToSuggested}
                    disabled={previewLoading || (!previewPackage && !diyTouched && !controlTouched)}
                  >
                    恢复推荐配置
                  </Button>
                </div>
              </div>

              <div className="mt-4 grid gap-3 xl:grid-cols-3">
                <DIYOptionGroup
                  title="压力微调"
                  description="只微调压力和推进速度，不改变本场核心面试风格。"
                  value={diyOverrides.pressure_tuning}
                  options={RESUME_INTERVIEW_DIY_OPTIONS.pressure_tuning}
                  onChange={(value) => handleChangeOverride("pressure_tuning", value)}
                />
                <DIYOptionGroup
                  title="追问路径"
                  description="决定是先澄清还是更快进入细节和真实性验证。"
                  value={diyOverrides.followup_style}
                  options={RESUME_INTERVIEW_DIY_OPTIONS.followup_style}
                  onChange={(value) => handleChangeOverride("followup_style", value)}
                />
                <DIYOptionGroup
                  title="额外加码点"
                  description="在当前挡位里额外提高一个方向的关注比例。"
                  value={diyOverrides.focus_boost}
                  options={RESUME_INTERVIEW_DIY_OPTIONS.focus_boost}
                  onChange={(value) => handleChangeOverride("focus_boost", value)}
                />
              </div>

              <div className="mt-4 rounded-2xl border border-primary/15 bg-primary/5 px-4 py-4">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <div>
                    <div className="text-[13px] font-semibold text-text">本场实际启动画像</div>
                    <div className="mt-1 text-[12px] text-dim">这里展示最终会写入会话的控制对象预览。</div>
                  </div>
                  <Badge variant="secondary">{effectiveControl.name}</Badge>
                </div>
                <div className="mt-3 text-[13px] leading-6 text-dim">{effectiveControl.diy_summary || "沿用固定挡位默认节奏。"}</div>
                <ControlPreviewPanel control={effectiveControl} />
              </div>
            </div>
          </div>

          {launcher.error && (
            <div className="mt-5 rounded-2xl border border-red/20 bg-red/10 px-4 py-3 text-sm text-red">
              {launcher.error}
            </div>
          )}

          <div className="mt-6 pt-5 border-t border-border/70 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-[13px] text-dim w-full md:w-auto text-center md:text-left">
              {!resumeFile
                ? "请先上传简历。"
                : !targetRole.trim()
                  ? "请先填写目标岗位。"
                  : previewLoading
                    ? "正在生成这次面试的预生成包和推荐配置。"
                    : previewError
                      ? "预生成包当前不可用，修复后才会允许正式启动。"
                      : "准备开始迎接挑战？点击右侧正式进入模拟环境"}
            </div>
            {loading ? (
               <div className="w-full md:w-[220px] rounded-xl bg-card border border-primary/20 py-3.5 px-4 flex items-center justify-center gap-2 relative overflow-hidden shrink-0 shadow-sm">
                 <div className="absolute inset-0 bg-primary/10 animate-pulse pointer-events-none" />
                 <div className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse-dot" />
                 <div className="text-[14px] font-semibold text-primary">构建专属对局...</div>
               </div>
            ) : (
              <Button
                variant="gradient"
                size="lg"
                className="w-full md:w-auto h-14 px-10 text-[16px] font-bold tracking-wide rounded-xl shadow-lg shadow-primary/20 transition-all hover:-translate-y-0.5 hover:shadow-xl hover:shadow-primary/30 disabled:opacity-40 disabled:hover:translate-y-0 disabled:shadow-none shrink-0"
                disabled={!resumeFile || !targetRole.trim() || targetRoleInferring || previewLoading || !previewPackage || !!previewError}
                onClick={handleStart}
              >
                <Play size={18} className="mr-2 fill-current" /> 立即开始模拟
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-10">
        {/* 左侧：流程 */}
        <div className="md:col-span-5 relative">
          <div className="text-[17px] font-bold text-text mb-6 flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-hover flex items-center justify-center text-dim">
              <Clock size={18} />
            </div>
            流程时间线指南
          </div>
          
          <div className="relative pl-[20px] pt-2">
            {INTERVIEW_STEPS.map((step, i) => (
              <div key={i} className="relative pb-9 last:pb-2 group">
                {/* 发光线 */}
                {i < INTERVIEW_STEPS.length - 1 && (
                  <div className="absolute left-[-11.5px] top-6 bottom-0 w-[2px] bg-border group-hover:bg-primary/40 transition-colors duration-300" />
                )}
                {/* 发光圆点 */}
                <div className="absolute left-[-16.5px] top-1.5 w-[12px] h-[12px] rounded-full border-[2.5px] border-primary bg-background shadow-[0_0_10px_0_rgba(var(--primary-rgb),0.5)] z-10" />
                
                <div className="inline-flex items-center text-[14px] font-bold text-text bg-card/60 backdrop-blur-sm px-3.5 py-1.5 rounded-lg border border-border/80 shadow-sm mb-2.5 transition-colors group-hover:border-primary/30 group-hover:bg-primary/5">
                  {step.title}
                </div>
                <div className="text-[13px] text-dim leading-relaxed font-medium pl-1 max-w-[90%]">{step.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* 右侧：记录 */}
        <div className="md:col-span-7">
          <div className="flex items-baseline justify-between mb-6">
            <div className="text-[17px] font-bold text-text flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-hover flex items-center justify-center text-dim">
                <CalendarDays size={18} />
              </div>
              最近考核记录
            </div>
            {history.length > 0 && (
              <button
                onClick={() => navigate("/history")}
                className="text-[13px] font-medium text-dim hover:text-primary transition-colors flex items-center gap-0.5 group"
              >
                查看全部 <ChevronRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
              </button>
            )}
          </div>

          <div className="min-h-[250px]">
            {historyLoading ? (
              <div className="flex flex-col gap-3.5">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-[80px] rounded-2xl w-full bg-card" />)}
              </div>
            ) : history.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full min-h-[250px] px-6 rounded-3xl border-2 border-dashed border-border/60 bg-card/20 text-center">
                <div className="w-16 h-16 bg-card border border-border/50 rounded-2xl flex items-center justify-center mb-4 text-dim shadow-sm">
                  <HistoryIcon />
                </div>
                <div className="text-[15px] font-bold text-text mb-2">暂无训练数据报告</div>
                <div className="text-[13px] text-dim max-w-[240px] leading-relaxed">
                  上方上传您最新的简历并开启挑战，您的第一份详尽面评解析将会出现在这里。
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-3.5">
                {history.map((s) => {
                  const reviewed = (s.status || "reviewed") === "reviewed";
                  const control = readResumeInterviewControl(s);
                  const title = reviewed
                    ? "简历沉浸式死磕"
                    : s.status === "review_failed" ? "复盘生成失败，点击重试"
                    : s.status === "reviewing" ? "复盘正在生成中"
                    : "面试未完成，点击继续";
                  return (
                  <Card
                    key={s.session_id}
                    className="cursor-pointer group flex items-center justify-between p-4 md:p-5 hover:border-primary/40 hover:bg-card hover:shadow-lg hover:shadow-primary/5 transition-all rounded-2xl border-border/80 bg-card/40"
                    onClick={() => navigate(reviewed ? `/review/${s.session_id}` : `/interview/${s.session_id}`)}
                  >
                    <div className="flex items-center gap-4 min-w-0 flex-1">
                      <div className="w-11 h-11 rounded-xl bg-background border border-border/60 flex items-center justify-center text-text shrink-0 group-hover:bg-primary/10 group-hover:border-primary/30 group-hover:text-primary transition-all shadow-sm">
                        <FileText size={20} />
                      </div>
                      <div className="flex flex-col min-w-0 gap-1.5">
                        <div className="font-bold text-[15px] text-text truncate pr-4 tracking-tight group-hover:text-primary transition-colors">
                          {title}
                        </div>
                        <div className="flex items-center gap-1.5 text-[12px] text-dim font-medium tabular-nums">
                          <Clock size={12} className="opacity-80" />
                          {formatDate(s.created_at)}
                          <span className="text-border">·</span>
                          <span>{control.short_name}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-5 shrink-0 pl-2">
                       <ScorePill score={s.avg_score} />
                       <div className="w-8 h-8 rounded-full bg-card border border-border/50 flex items-center justify-center group-hover:bg-primary group-hover:border-primary group-hover:text-primary-foreground transition-all text-dim shadow-sm">
                         <ChevronRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
                       </div>
                    </div>
                  </Card>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function HistoryIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-dim/80">
      <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
    </svg>
  );
}

