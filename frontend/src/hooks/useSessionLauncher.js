import { useCallback, useState } from "react";
import { useTaskStatus } from "../contexts/taskStatusShared";

function toMessage(error) {
  if (!error) return "未知错误";
  if (typeof error === "string") return error;
  return error.message || String(error);
}

export function useSessionLauncher({
  key,
  navigate,
  getPath = (data) => `/interview/${data.session_id}`,
  getState = (data) => data,
  errorPrefix = "启动失败",
} = {}) {
  const taskStatus = useTaskStatus() || {};
  const [localCreating, setLocalCreating] = useState(false);
  const [error, setError] = useState("");

  const isCreating = taskStatus.isCreatingSession?.(key) ?? localCreating;

  const setCreating = useCallback((active) => {
    if (taskStatus.setCreatingSession && key) {
      taskStatus.setCreatingSession(key, active);
      return;
    }
    setLocalCreating(active);
  }, [key, taskStatus]);

  const clearError = useCallback(() => setError(""), []);

  const launch = useCallback(async (runner, options = {}) => {
    if (isCreating) return null;
    setError("");
    setCreating(true);
    try {
      const data = await runner();
      if (options.navigate !== false && navigate) {
        const path = (options.getPath || getPath)(data);
        const state = (options.getState || getState)(data);
        navigate(path, { state });
      }
      return data;
    } catch (err) {
      const message = `${options.errorPrefix || errorPrefix}: ${toMessage(err)}`;
      setError(message);
      options.onError?.(message, err);
      return null;
    } finally {
      setCreating(false);
    }
  }, [errorPrefix, getPath, getState, isCreating, navigate, setCreating]);

  return {
    loading: isCreating,
    error,
    setError,
    clearError,
    launch,
  };
}