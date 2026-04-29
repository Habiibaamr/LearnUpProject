import { api } from "./api";

export interface InstructorStudentProfile {
  user_id: number;
  student_id: number;
  university_id: string;
  full_name: string;
  email: string;
  photo_url: string | null;
  faculty_id: number | null;
  department_id: number | null;
  level: number | null;
  cgpa: number | null;
  passed_credit_hours: number | null;
  phone: string | null;
  advisor_instructor_id: number | null;
}

export interface InstructorCourseRow {
  registration_id: number;
  student_id: number;
  course_offering_id: number;
  course_id: number;
  course_code: string;
  course_title: string;
  credit_hours: number;
  semester_id: number;
  registration_status: string;
  registered_at: string;
}

export interface InstructorAssignedOffering {
  course_offering_id: number;
  course_id: number;
  course_code: string;
  course_title: string;
  credit_hours: number;
  semester_id: number;
  offering_status: string;
}

export interface InstructorOfferingRegistration {
  registration_id: number;
  student_id: number;
  student_university_id: string;
  student_full_name: string;
  status: string;
  final_grade: string | null;
  is_passed: boolean | null;
  registered_at: string;
  completed_at: string | null;
}

export interface InstructorFinalGradesWindowStatus {
  is_open: boolean;
  term_index: number | null;
  updated_by_user_id: number | null;
  updated_at: string | null;
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

export async function getStudentByUniversityId(universityId: string) {
  const { data } = await api.get<InstructorStudentProfile>(
    `/instructor/students/${encodeURIComponent(universityId)}`
  );
  return data;
}

export async function getStudentCourses(universityId: string) {
  const { data } = await api.get<InstructorCourseRow[]>(
    `/instructor/students/${encodeURIComponent(universityId)}/courses`
  );
  return data;
}

export async function addCourseForStudent(universityId: string, courseOfferingId: number) {
  return api.post(
    `/instructor/students/${encodeURIComponent(universityId)}/add-course/${courseOfferingId}`
  );
}

export async function dropCourseForStudent(universityId: string, courseOfferingId: number) {
  return api.post(
    `/instructor/students/${encodeURIComponent(universityId)}/drop-course/${courseOfferingId}`
  );
}

export async function getStudentCourseBoard(universityId: string) {
  const { data } = await api.get<{ courses: CourseBoardRow[] }>(
    `/instructor/students/${encodeURIComponent(universityId)}/course-board`
  );
  return data.courses;
}

export async function addCourseForStudentByCourse(universityId: string, courseId: number) {
  return api.post(
    `/instructor/students/${encodeURIComponent(universityId)}/add-course-by-course/${courseId}`
  );
}

export async function dropCourseForStudentByCourse(universityId: string, courseId: number) {
  return api.post(
    `/instructor/students/${encodeURIComponent(universityId)}/drop-course-by-course/${courseId}`
  );
}

export async function getFinalGradesWindowStatus() {
  const { data } = await api.get<InstructorFinalGradesWindowStatus>("/instructor/final-grades-window");
  return data;
}

export async function getMyAssignedOfferings() {
  const { data } = await api.get<InstructorAssignedOffering[]>("/instructor/my-offerings");
  return data;
}

export async function getOfferingRegistrations(courseOfferingId: number) {
  const { data } = await api.get<InstructorOfferingRegistration[]>(
    `/instructor/my-offerings/${courseOfferingId}/registrations`
  );
  return data;
}

export async function submitFinalGrade(
  courseOfferingId: number,
  registrationId: number,
  payload: { final_grade: string; is_passed: boolean }
) {
  return api.post(
    `/instructor/my-offerings/${courseOfferingId}/registrations/${registrationId}/final-grade`,
    payload
  );
}
