import { useState, useRef, useCallback, useEffect } from "react";
import { getTaskStatus } from "../api/interview";
import { TaskStatusContext } from "./taskStatusShared";

const POLL_INTERVAL = 3000;

export function TaskStatusProvider({ children }) {
  const [tasks, setTasks] = useState([]);
  const timersRef = useRef({});

  const stopPolling = useCallback((taskId) => {
    if (timersRef.current[taskId]) {
      clearInterval(timersRef.current[taskId]);
      delete timersRef.current[taskId];
    }
  }, []);

  useEffect(() => {
    return () => {
      Object.values(timersRef.current).forEach(clearInterval);
      timersRef.current = {};
    };
  }, []);

  const startTask = useCallback((id, type, label) => {
    stopPolling(id);
    setTasks((prev) => {
      const filtered = prev.filter((t) => t.id !== id);
      return [...filtered, { id, type, label, status: "pending" }];
    });

    timersRef.current[id] = setInterval(async () => {
      try {
        const data = await getTaskStatus(id);
        if (data.status === "done" || data.status === "error") {
          setTasks((prev) =>
            prev.map((t) => (t.id === id ? { ...t, status: data.status, result: data.result } : t))
          );
          stopPolling(id);
        }
      } catch {
        // task not ready or network error, keep polling
      }
    }, POLL_INTERVAL);
  }, [stopPolling]);

  const dismissTask = useCallback((id) => {
    stopPolling(id);
    setTasks((prev) => prev.filter((t) => t.id !== id));
  }, [stopPolling]);

  const [creatingSessions, setCreatingSessions] = useState({});
  const [creatingSessionMode, setCreatingSessionMode] = useState(null);

  const setCreatingSession = useCallback((key, active) => {
    setCreatingSessions((prev) => {
      if (active) return { ...prev, [key]: true };
      if (!prev[key]) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }, []);

  const isCreatingSession = useCallback(
    (key) => Boolean(creatingSessions[key]),
    [creatingSessions]
  );

  return (
    <TaskStatusContext.Provider
      value={{
        tasks,
        startTask,
        dismissTask,
        creatingSessions,
        setCreatingSession,
        isCreatingSession,
        creatingSessionMode,
        setCreatingSessionMode,
      }}
    >
      {children}
    </TaskStatusContext.Provider>
  );
}
