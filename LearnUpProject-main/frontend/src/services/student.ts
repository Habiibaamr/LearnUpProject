import { api } from "./api";

export interface StudentCard {
  /** Present when served by current LearnUp API (v2 student row auto-create). */
  student_card_api?: string;
  user_id: number;
  university_id: string;
  full_name: string;
  email: string;
  role: string;
  photo_url: string | null;
  faculty_id: number | null;
  faculty_name: string | null;
  faculty_code: string | null;
  department_id: number | null;
  department_name: string | null;
  department_code: string | null;
  level: number | null;
  cgpa: number | null;
  passed_credit_hours: number | null;
  total_credit_hours: number;
  phone: string | null;
  advisor_instructor_id: number | null;
  advisor_name: string | null;
}

export interface StudentCourseRow {
  registration_id: number;
  course_offering_id: number;
  course_id: number;
  course_code: string;
  course_title: string;
  credit_hours: number;
  semester_id: number;
  registration_status: string;
  registered_at: string;
}

export type CourseBoardStatus = "available" | "enrolled" | "locked" | "passed";

export interface CourseBoardRow {
  course_id: number;
  course_offering_id: number;
  course_code: string;
  title: string;
  credit_hours: number;
  level: number | null;
  status: CourseBoardStatus;
  lock_reason: string | null;
  missing_prerequisite_ids: number[];
  can_add: boolean;
  can_drop: boolean;
}

export async function getStudentCard() {
  const { data } = await api.get<StudentCard>("/learnup/student/identity-card");
  return data;
}

export async function uploadStudentPhoto(photo: File) {
  const formData = new FormData();
  formData.append("photo", photo);
  const { data } = await api.post<{ message: string; photo_url: string }>("/student/me/photo", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getStudentCourses() {
  const { data } = await api.get<StudentCourseRow[]>("/student/me/courses");
  return data;
}

export async function addStudentCourse(courseOfferingId: number) {
  return api.post(`/student/me/add-course/${courseOfferingId}`);
}

export async function dropStudentCourse(courseOfferingId: number) {
  return api.post(`/student/me/drop-course/${courseOfferingId}`);
}

export async function getCourseBoard() {
  const { data } = await api.get<{ courses: CourseBoardRow[] }>("/student/me/course-board");
  return data.courses;
}

export async function addStudentCourseByCourse(courseId: number) {
  return api.post(`/student/me/add-course-by-course/${courseId}`);
}

export async function dropStudentCourseByCourse(courseId: number) {
  return api.post(`/student/me/drop-course-by-course/${courseId}`);
}

export async function getAvailableGroups(courseOfferingId: number) {
  const { data } = await api.get<{
    course_offering_id: number;
    lecture_groups: Array<Record<string, unknown>>;
    section_groups: Array<Record<string, unknown>>;
  }>(`/student/me/available-groups/${courseOfferingId}`);
  return data;
}

export async function registerLecture(lectureGroupId: number) {
  return api.post(`/student/me/register-lecture/${lectureGroupId}`);
}

export async function registerSection(sectionGroupId: number) {
  return api.post(`/student/me/register-section/${sectionGroupId}`);
}

export async function dropLecture(lectureGroupId: number) {
  return api.post(`/student/me/drop-lecture/${lectureGroupId}`);
}

export async function dropSection(sectionGroupId: number) {
  return api.post(`/student/me/drop-section/${sectionGroupId}`);
}
