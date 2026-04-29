import { api } from "./api";

export interface AdminUserRow {
  id: number;
  university_id: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  position?: string | null;
  created_at: string;
}

export interface AdminInstructorRow {
  instructor_id: number;
  user_id: number;
  university_id: string;
  full_name: string;
  email: string;
}

export interface AdminCourseOfferingRow {
  course_offering_id: number;
  course_id: number;
  course_code: string;
  course_title: string;
  semester_id: number;
  status: string;
}

export async function listUsers() {
  const { data } = await api.get<AdminUserRow[]>("/admin/users");
  return data;
}

export async function listInstructors() {
  const { data } = await api.get<AdminInstructorRow[]>("/admin/instructors");
  return data;
}

export async function listCourseOfferings() {
  const { data } = await api.get<AdminCourseOfferingRow[]>("/admin/course-offerings");
  return data;
}

export async function createStudentAccount(payload: Record<string, unknown>) {
  return api.post("/admin/create-student-account", payload);
}

export async function createInstructorAccount(payload: Record<string, unknown>) {
  return api.post("/admin/create-instructor-account", payload);
}

export async function createAdminAccount(payload: Record<string, unknown>) {
  return api.post("/admin/create-admin-account", payload);
}

export async function updateAdminAccount(userId: number, payload: Record<string, unknown>) {
  return api.patch(`/admin/admin-accounts/${userId}`, payload);
}

export async function deleteAdminAccount(userId: number) {
  return api.delete(`/admin/admin-accounts/${userId}`);
}

export async function assignInstructor(payload: {
  course_offering_id: number;
  instructor_id: number;
}) {
  return api.post("/admin/assign-instructor-to-offering", payload);
}

export async function listOfferingInstructors(courseOfferingId: number) {
  const { data } = await api.get<
    Array<{ id: number; course_offering_id: number; instructor_id: number }>
  >(`/admin/course-offering-instructors/${courseOfferingId}`);
  return data;
}

export async function completeStudentTerm(payload: {
  university_id: string;
  term_index: number;
}) {
  return api.post("/admin/complete-student-term", payload);
}

export async function completeTermAllStudents(payload: { term_index: number }) {
  return api.post("/admin/complete-term-all-students", payload);
}

export interface FinalGradesWindowStatus {
  is_open: boolean;
  term_index: number | null;
  updated_by_user_id: number | null;
  updated_at: string | null;
}

export async function getFinalGradesWindow() {
  const { data } = await api.get<FinalGradesWindowStatus>("/admin/final-grades-window");
  return data;
}

export async function openFinalGradesWindow(payload: { term_index: number }) {
  return api.post("/admin/final-grades-window/open", payload);
}

export async function closeFinalGradesWindow() {
  return api.post("/admin/final-grades-window/close");
}
