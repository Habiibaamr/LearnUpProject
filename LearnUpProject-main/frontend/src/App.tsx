import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { DashboardLayout } from "./layouts/DashboardLayout";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import StudentDashboard from "./pages/student/StudentDashboard";
import IdentityCard from "./pages/student/IdentityCard";
import MyCourses from "./pages/student/MyCourses";
import AddDropCourses from "./pages/student/AddDropCourses";
import GroupsRegistration from "./pages/student/GroupsRegistration";
import ChatbotPage from "./pages/student/Chatbot";
import Schedule from "./pages/student/Schedule";
import InstructorDashboard from "./pages/instructor/InstructorDashboard";
import InstructorSearch from "./pages/instructor/InstructorSearch";
import InstructorStudentProfile from "./pages/instructor/InstructorStudentProfile";
import InstructorStudentCourses from "./pages/instructor/InstructorStudentCourses";
import InstructorStudentCourseBoard from "./pages/instructor/InstructorStudentCourseBoard";
import InstructorAdvising from "./pages/instructor/InstructorAdvising";
import InstructorAssigned from "./pages/instructor/InstructorAssigned";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminManageUsers from "./pages/admin/AdminManageUsers";
import AdminCreateStudent from "./pages/admin/AdminCreateStudent";
import AdminCreateInstructor from "./pages/admin/AdminCreateInstructor";
import AdminCreateAdmin from "./pages/admin/AdminCreateAdmin";
import AdminAssignInstructor from "./pages/admin/AdminAssignInstructor";
import AdminSystemOverview from "./pages/admin/AdminSystemOverview";
import AdminCompleteStudentTerm from "./pages/admin/AdminCompleteStudentTerm";
import AdminFinalGradesWindow from "./pages/admin/AdminFinalGradesWindow";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />

          <Route element={<ProtectedRoute allowedRoles={["student"]} />}>
            <Route path="student" element={<DashboardLayout role="student" />}>
              <Route index element={<Navigate to="dashboard" replace />} />
              <Route path="dashboard" element={<StudentDashboard />} />
              <Route path="identity" element={<IdentityCard />} />
              <Route path="courses" element={<MyCourses />} />
              <Route path="add-drop" element={<AddDropCourses />} />
              <Route path="groups" element={<GroupsRegistration />} />
              <Route path="chatbot" element={<ChatbotPage />} />
              <Route path="schedule" element={<Schedule />} />
            </Route>
          </Route>

          <Route element={<ProtectedRoute allowedRoles={["instructor"]} />}>
            <Route path="instructor" element={<DashboardLayout role="instructor" />}>
              <Route index element={<Navigate to="dashboard" replace />} />
              <Route path="dashboard" element={<InstructorDashboard />} />
              <Route path="search" element={<InstructorSearch />} />
              <Route path="profile" element={<InstructorStudentProfile />} />
              <Route path="student-courses" element={<InstructorStudentCourses />} />
              <Route path="student-course-board" element={<InstructorStudentCourseBoard />} />
              <Route path="add-course" element={<Navigate to="/instructor/student-course-board" replace />} />
              <Route path="drop-course" element={<Navigate to="/instructor/student-course-board" replace />} />
              <Route path="advising" element={<InstructorAdvising />} />
              <Route path="assigned" element={<InstructorAssigned />} />
            </Route>
          </Route>

          <Route element={<ProtectedRoute allowedRoles={["admin", "super_admin"]} />}>
            <Route path="admin" element={<DashboardLayout role="admin" />}>
              <Route index element={<Navigate to="dashboard" replace />} />
              <Route path="dashboard" element={<AdminDashboard />} />
              <Route path="users" element={<AdminManageUsers />} />
              <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
                <Route path="create-student" element={<AdminCreateStudent />} />
                <Route path="create-instructor" element={<AdminCreateInstructor />} />
                <Route path="assign" element={<AdminAssignInstructor />} />
                <Route path="overview" element={<AdminSystemOverview />} />
                <Route path="complete-term" element={<AdminCompleteStudentTerm />} />
                <Route path="final-grades-window" element={<AdminFinalGradesWindow />} />
              </Route>
              <Route element={<ProtectedRoute allowedRoles={["super_admin"]} />}>
                <Route path="create-admin" element={<AdminCreateAdmin />} />
              </Route>
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
