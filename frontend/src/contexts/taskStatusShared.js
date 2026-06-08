import { createContext, useContext } from "react";

export const TaskStatusContext = createContext(null);

export function useTaskStatus() {
  return useContext(TaskStatusContext);
}