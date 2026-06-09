import unittest

from langchain_core.messages import AIMessage, HumanMessage

from backend.interview_control import (
    list_resume_interview_controls,
    summarize_resume_interview_behavior,
)


class ResumeControlP2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controls = {item["id"]: item for item in list_resume_interview_controls()}

    def test_preview_highlights_match_expected_boundaries(self):
        expected = {
            "friendly_training": ["clarification", "authenticity"],
            "standard_interview": ["deep_followup", "tradeoff"],
            "deep_verification": ["deep_followup", "authenticity"],
            "pressure_challenge": ["tradeoff", "lateral_solution"],
        }
        for control_id, highlight_keys in expected.items():
            with self.subTest(control_id=control_id):
                control = self.controls[control_id]
                self.assertEqual(highlight_keys, [item["key"] for item in control["behavior_budget_highlights"]])
                self.assertEqual(highlight_keys, [item["budget_key"] for item in control["sample_preview"]])

    def test_every_control_exposes_preview_assets(self):
        for control in self.controls.values():
            with self.subTest(control_id=control["id"]):
                self.assertEqual(8, len(control["behavior_budget_profile"]))
                self.assertEqual(2, len(control["behavior_budget_highlights"]))
                self.assertEqual(2, len(control["sample_preview"]))
                self.assertTrue(control.get("budget_preview_summary"))

    def test_behavior_summary_reflects_actual_question_style(self):
        control = self.controls["pressure_challenge"]
        messages = [
            AIMessage(content="如果预算不变但延迟翻倍，你优先牺牲什么、保住什么？为什么？"),
            HumanMessage(content="我会先保护核心链路。"),
            AIMessage(content="假设现有技术栈不能用，你给我一个替代方案，并说清迁移代价。"),
            HumanMessage(content="我会拆成过渡方案和最终方案。"),
        ]

        summary = summarize_resume_interview_behavior(messages, control)
        dominant = [item["key"] for item in summary["dominant_behaviors"]]

        self.assertEqual(2, summary["question_count"])
        self.assertIn("tradeoff", dominant)
        self.assertIn("lateral_solution", dominant)
        self.assertTrue(summary.get("alignment_summary"))


if __name__ == "__main__":
    unittest.main()