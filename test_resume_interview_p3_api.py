import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

import backend.storage.copilot_preps as copilot_preps_store
import backend.storage.sessions as sessions_store
import backend.vector_memory as vector_memory_store
from backend.app import create_app
from backend.config import settings
from backend.runtime import _graphs, _task_status


class _FakeGraph:
    def __init__(self):
        self.last_payload = None
        self.last_config = None

    async def ainvoke(self, payload, config):
        self.last_payload = payload or {}
        self.last_config = config
        return {
            "messages": [
                AIMessage(content="你好，先做个自我介绍吧。")
            ]
        }

    async def aget_state(self, config):
        values = {
            "target_role": (self.last_payload or {}).get("target_role", ""),
            "interview_control": (self.last_payload or {}).get("interview_control"),
            "is_finished": False,
        }
        return SimpleNamespace(values=values, next=["interviewer_ask"])


class ResumeInterviewP3ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "interviews.db"
        self.fake_graph = _FakeGraph()

        _graphs.clear()
        _task_status.clear()

        self.preview_package = {
            "id": "preview-p3-001",
            "version": "2026-03-p3",
            "generated_at": "2026-03-14T12:00:00",
            "target_role": "AI 应用开发工程师",
            "resume_hash": "resume-hash-001",
            "source": {
                "resume_length": 2048,
                "target_role": "AI 应用开发工程师",
            },
            "resume_signals": {
                "headline_lines": ["游戏 AI / 数值 / 匹配系统"],
                "metric_lines": ["延迟下降 35%"],
                "project_lines": ["负责 AI 训练平台搭建"],
                "stack_tags": ["Python", "RAG", "LLM"],
            },
            "recommended_preset_id": "deep_verification",
            "recommended_reason": "简历里可深挖的项目和结果信号比较多，适合直接做真实性和细节验证。",
            "recommended_control": {
                "id": "deep_verification",
                "name": "深度验证",
            },
            "available_controls": [
                {"id": "friendly_training"},
                {"id": "standard_interview"},
                {"id": "deep_verification"},
                {"id": "pressure_challenge"},
            ],
            "diy_options": {},
            "default_overrides": {
                "pressure_tuning": "same",
                "followup_style": "balanced",
                "focus_boost": "",
            },
            "suggested_overrides": {
                "pressure_tuning": "same",
                "followup_style": "deep_dive",
                "focus_boost": "deep_followup",
            },
            "suggested_control": {
                "id": "deep_verification",
                "origin": "diy",
            },
            "notes": [
                "DIY 只在固定挡位底座上做有限调整，不会脱离当前预设的面试边界。",
            ],
        }

        async def _fake_init_resume_checkpointer():
            return None

        def _fake_build_resume_interview_preview_package(user_id, target_role, profile=None):
            package = dict(self.preview_package)
            package["target_role"] = target_role
            package["source"] = {
                **self.preview_package["source"],
                "target_role": target_role,
            }
            return package

        self.patchers = [
            patch.object(settings, "base_dir", self.base_dir),
            patch.object(settings, "db_path", self.db_path),
            patch.object(settings, "resume_path", self.data_dir / "resume"),
            patch.object(settings, "knowledge_path", self.data_dir / "knowledge"),
            patch.object(settings, "high_freq_path", self.data_dir / "high_freq"),
            patch.object(sessions_store, "DB_PATH", self.db_path),
            patch.object(vector_memory_store, "DB_PATH", self.db_path),
            patch.object(copilot_preps_store, "DB_PATH", self.db_path),
            patch("backend.app.init_resume_checkpointer", new=_fake_init_resume_checkpointer),
            patch("backend.routers.interview.build_resume_interview_preview_package", new=_fake_build_resume_interview_preview_package),
            patch("backend.graphs.resume_interview.compile_resume_interview", new=lambda user_id: self.fake_graph),
        ]
        for patcher in self.patchers:
            patcher.start()

        self.client_ctx = TestClient(create_app())
        self.client = self.client_ctx.__enter__()
        self.auth_headers = self._login_headers()

    def tearDown(self):
        self.client_ctx.__exit__(None, None, None)
        for patcher in reversed(self.patchers):
            patcher.stop()
        _graphs.clear()
        _task_status.clear()
        self.temp_dir.cleanup()

    def _login_headers(self):
        response = self.client.post(
            "/api/auth/login",
            json={
                "email": settings.default_email,
                "password": settings.default_password,
            },
        )
        self.assertEqual(200, response.status_code, response.text)
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def test_resume_preview_start_and_resume_roundtrip(self):
        preview_response = self.client.post(
            "/api/interview/resume-preview",
            headers=self.auth_headers,
            json={"target_role": "AI 应用开发工程师"},
        )
        self.assertEqual(200, preview_response.status_code, preview_response.text)
        preview_package = preview_response.json()["preview_package"]
        self.assertEqual("preview-p3-001", preview_package["id"])
        self.assertEqual("deep_verification", preview_package["recommended_preset_id"])
        self.assertEqual(
            {
                "pressure_tuning": "same",
                "followup_style": "deep_dive",
                "focus_boost": "deep_followup",
            },
            preview_package["suggested_overrides"],
        )
        self.assertEqual(
            ["headline_lines", "metric_lines", "project_lines", "stack_tags"],
            sorted(preview_package["resume_signals"].keys()),
        )

        start_response = self.client.post(
            "/api/interview/start",
            headers=self.auth_headers,
            json={
                "mode": "resume",
                "target_role": "AI 应用开发工程师",
                "interview_control_preset": preview_package["recommended_preset_id"],
                "preview_package_id": preview_package["id"],
                "interview_control_overrides": preview_package["suggested_overrides"],
            },
        )
        self.assertEqual(200, start_response.status_code, start_response.text)
        start_payload = start_response.json()
        session_id = start_payload["session_id"]
        self.assertTrue(session_id)
        self.assertEqual("AI 应用开发工程师", start_payload["target_role"])
        self.assertEqual("deep_verification", start_payload["interview_control"]["id"])
        self.assertEqual("diy", start_payload["interview_control"]["origin"])
        self.assertEqual(preview_package["id"], start_payload["meta"]["preview_package_id"])
        self.assertEqual(
            preview_package["suggested_overrides"],
            start_payload["meta"]["interview_control_overrides"],
        )
        self.assertEqual(
            preview_package["recommended_preset_id"],
            start_payload["meta"]["recommended_preset_id"],
        )
        self.assertEqual(
            preview_package["suggested_overrides"],
            start_payload["meta"]["suggested_overrides"],
        )
        self.assertEqual("你好，先做个自我介绍吧。", start_payload["message"])

        session_response = self.client.get(
            f"/api/interview/session/{session_id}/resume",
            headers=self.auth_headers,
        )
        self.assertEqual(200, session_response.status_code, session_response.text)
        session_payload = session_response.json()
        self.assertEqual("resume", session_payload["mode"])
        self.assertEqual("ongoing", session_payload["status"])
        self.assertTrue(session_payload["can_continue"])
        self.assertFalse(session_payload["is_finished"])
        self.assertEqual("AI 应用开发工程师", session_payload["target_role"])
        self.assertEqual("deep_verification", session_payload["interview_control"]["id"])
        self.assertEqual("diy", session_payload["interview_control"]["origin"])
        self.assertEqual(preview_package["id"], session_payload["meta"]["preview_package_id"])
        self.assertEqual(preview_package["id"], session_payload["meta"]["preview_package"]["id"])
        self.assertEqual(
            preview_package["suggested_overrides"],
            session_payload["meta"]["interview_control_overrides"],
        )
        self.assertEqual(1, len(session_payload["transcript"]))
        self.assertEqual("assistant", session_payload["transcript"][0]["role"])

    def test_start_rejects_stale_preview_package_id(self):
        response = self.client.post(
            "/api/interview/start",
            headers=self.auth_headers,
            json={
                "mode": "resume",
                "target_role": "AI 应用开发工程师",
                "interview_control_preset": "deep_verification",
                "preview_package_id": "expired-preview-id",
                "interview_control_overrides": self.preview_package["suggested_overrides"],
            },
        )
        self.assertEqual(400, response.status_code, response.text)
        self.assertIn("预生成包已过期", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()