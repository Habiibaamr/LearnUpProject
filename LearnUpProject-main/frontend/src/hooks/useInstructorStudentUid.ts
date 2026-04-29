import { useCallback, useState } from "react";

const KEY = "learnup_instructor_student_uid";

export function useInstructorStudentUid() {
  const [uid, setUidState] = useState(() =>
    typeof window !== "undefined" ? sessionStorage.getItem(KEY) || "" : ""
  );

  const setUid = useCallback((value: string) => {
    const t = value.trim();
    if (t) sessionStorage.setItem(KEY, t);
    else sessionStorage.removeItem(KEY);
    setUidState(t);
  }, []);

  return { uid, setUid };
}
