import type { ReactNode } from "react";
import { useAuth } from "../context/AuthContext";
import { hasPermission, type AppModule } from "../auth/permissions";
import AccessDenied from "./AccessDenied";

type RoleGuardProps = {
  module: AppModule;
  children: ReactNode;
};

export default function RoleGuard({ module, children }: RoleGuardProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="auth-loading" role="status">
        Chargement…
      </div>
    );
  }

  if (!user || !hasPermission(user.role, module)) {
    return <AccessDenied module={module} />;
  }

  return <>{children}</>;
}
