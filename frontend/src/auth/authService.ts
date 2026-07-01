import type { AuthUser } from "./types";
import { isUserRole, type UserRole } from "./permissions";

const STORAGE_KEY = "uca.auth.session";
const SESSION_TTL_MS = 8 * 60 * 60 * 1000;
const API_BASE = "/api";

export interface AuthSession {
  user: AuthUser;
  accessToken: string;
  expiresAt: number;
}

export function loadSession(): AuthSession | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const session = JSON.parse(raw) as AuthSession;
    if (!session.expiresAt || session.expiresAt <= Date.now()) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    if (!session.user?.id || !isUserRole(session.user.role)) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return session;
  } catch {
    localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function saveSession(session: AuthSession): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearSession(): void {
  localStorage.removeItem(STORAGE_KEY);
}

function toAuthUser(payload: {
  id: string;
  username: string;
  displayName: string;
  role: string;
}): AuthUser {
  if (!isUserRole(payload.role)) {
    throw new Error("Identifiants invalides.");
  }
  return {
    id: payload.id,
    username: payload.username,
    displayName: payload.displayName,
    role: payload.role as UserRole,
  };
}

export async function authenticate(username: string, password: string): Promise<AuthSession> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    throw new Error("Identifiants invalides.");
  }

  const data = (await response.json()) as {
    user: { id: string; username: string; displayName: string; role: string };
  };
  const user = toAuthUser(data.user);

  return {
    user,
    accessToken: `session-${user.id}-${Date.now()}`,
    expiresAt: Date.now() + SESSION_TTL_MS,
  };
}
