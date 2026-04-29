export type Role = "student" | "instructor" | "admin" | "super_admin";

export function isAdminPortalRole(role: Role | string | null | undefined): role is "admin" | "super_admin" {
  return role === "admin" || role === "super_admin";
}

export function getDashboardPath(role: Role | string): string {
  return role === "super_admin" ? "/admin/dashboard" : `/${role}/dashboard`;
}

export interface UserMe {
  id: number;
  university_id: string;
  full_name: string;
  email: string;
  role: Role;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: Role;
}
