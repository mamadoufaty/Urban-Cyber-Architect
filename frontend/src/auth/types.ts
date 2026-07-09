export interface AuthUser {
  id: string;
  username: string;
  displayName: string;
  role: import("./permissions").UserRole;
  organizationId: string | null;
}

export interface AuthSession {
  user: AuthUser;
  accessToken: string;
  expiresAt: number;
}

export interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}
