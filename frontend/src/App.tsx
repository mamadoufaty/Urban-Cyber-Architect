import { Routes, Route, NavLink, useLocation } from "react-router-dom";

import { SidebarProvider, useSidebar } from "./context/SidebarContext";

import { useAuth } from "./context/AuthContext";

import ProtectedRoute from "./components/ProtectedRoute";

import RoleGuard from "./components/RoleGuard";

import UserSessionBar from "./components/UserSessionBar";

import LoginPage from "./pages/LoginPage";

import { isLoginPath } from "./routing/isLoginPath";

import { hasPermission, type AppModule } from "./auth/permissions";

import {

  CYBER_MODULES,

  NAV_SECTIONS,

  URBANISM_MODULES,

  type NavItem,

  type NavSection,

} from "./routing/navigation";

import Dashboard from "./pages/Dashboard";

import Projects from "./pages/Projects";

import AIGovernance from "./pages/AIGovernance";

import PromptStudio from "./pages/PromptStudio";

import KnowledgeBase from "./pages/KnowledgeBase";

import UrbanismSchema from "./pages/UrbanismSchema";

import MetamodelValidation from "./pages/MetamodelValidation";

import EbiosRm from "./pages/EbiosRm";

import RiskRegister from "./pages/RiskRegister";

import DashboardRssi from "./pages/DashboardRssi";

import StatementOfApplicability from "./pages/StatementOfApplicability";

import PlanTraitementRisques from "./pages/PlanTraitementRisques";
import Livrables from "./pages/Livrables";

import AdminUsers from "./pages/administration/AdminUsers";

import WazuhDashboard from "./pages/soc/WazuhDashboard";

import SocCorrelations from "./pages/soc/Correlations";

import WazuhConnectorSettings from "./pages/settings/WazuhConnectorSettings";

import ModulePlaceholder from "./pages/ModulePlaceholder";

import type { ReactNode } from "react";



function Guarded({ module, children }: { module: AppModule; children: ReactNode }) {

  return <RoleGuard module={module}>{children}</RoleGuard>;

}



function filterNavSections(role: string | undefined, sections: NavSection[]): NavSection[] {

  return sections

    .map((section) => ({

      ...section,

      items: section.items.filter((item) => hasPermission(role, item.module)),

    }))

    .filter((section) => section.items.length > 0);

}



function NavSectionBlock({ section }: { section: NavSection }) {

  return (

    <nav className="nav-section">

      <h3>{section.title}</h3>

      {section.items.map((item: NavItem) => (

        <NavLink

          key={item.path}

          to={item.path}

          end={item.path === "/"}

          className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}

        >

          {item.label}

        </NavLink>

      ))}

    </nav>

  );

}



export default function App() {

  const { pathname } = useLocation();



  if (isLoginPath(pathname)) {

    return <LoginPage />;

  }



  return (

    <ProtectedRoute>

      <SidebarProvider>

        <AppShell />

      </SidebarProvider>

    </ProtectedRoute>

  );

}



function AppShell() {

  const { sidebarOpen, toggleSidebar } = useSidebar();

  const { user } = useAuth();

  const visibleSections = filterNavSections(user?.role, NAV_SECTIONS);



  return (

    <div className={`app-layout${sidebarOpen ? "" : " sidebar-collapsed"}`}>

      <aside className="sidebar" aria-hidden={!sidebarOpen}>

        <div className="logo">

          <h1>Urban Cyber Architect</h1>

          <span>PRD V2 — V1</span>

        </div>



        <div className="sidebar-nav-scroll">

          {visibleSections.map((section) => (

            <NavSectionBlock key={section.id} section={section} />

          ))}

        </div>



        <UserSessionBar variant="sidebar" />

      </aside>



      <main className="main">

        <header className="app-top-bar">

          <button

            type="button"

            className="sidebar-toggle-btn"

            onClick={toggleSidebar}

            aria-expanded={sidebarOpen}

            aria-label={sidebarOpen ? "Masquer le menu latéral" : "Afficher le menu latéral"}

            title={sidebarOpen ? "Masquer le menu" : "Afficher le menu"}

          >

            ☰

          </button>

          <UserSessionBar variant="header" />

        </header>

        <Routes>

          <Route

            path="/"

            element={

              <Guarded module="dashboard">

                <Dashboard />

              </Guarded>

            }

          />

          <Route

            path="/projects"

            element={

              <Guarded module="projects">

                <Projects />

              </Guarded>

            }

          />

          <Route

            path="/ai-governance"

            element={

              <Guarded module="ai">

                <AIGovernance />

              </Guarded>

            }

          />

          <Route

            path="/prompt-studio"

            element={

              <Guarded module="ai">

                <PromptStudio />

              </Guarded>

            }

          />

          <Route

            path="/knowledge-base"

            element={

              <Guarded module="ai">

                <KnowledgeBase />

              </Guarded>

            }

          />

          <Route

            path="/schema-urbanisme"

            element={

              <Guarded module="urbanism">

                <UrbanismSchema />

              </Guarded>

            }

          />

          <Route

            path="/validation-metamodele"

            element={

              <Guarded module="urbanism">

                <MetamodelValidation />

              </Guarded>

            }

          />

          <Route

            path="/ebios"

            element={

              <Guarded module="grc">

                <EbiosRm />

              </Guarded>

            }

          />

          <Route

            path="/registre-risques"

            element={

              <Guarded module="grc">

                <RiskRegister />

              </Guarded>

            }

          />

          <Route

            path="/dashboard-rssi"

            element={

              <Guarded module="grc">

                <DashboardRssi />

              </Guarded>

            }

          />

          <Route

            path="/declaration-applicabilite"

            element={

              <Guarded module="grc">

                <StatementOfApplicability />

              </Guarded>

            }

          />

          <Route

            path="/plan-traitement-risques"

            element={

              <Guarded module="grc">

                <PlanTraitementRisques />

              </Guarded>

            }

          />

          <Route

            path="/livrables"

            element={

              <Guarded module="grc">

                <Livrables />

              </Guarded>

            }

          />

          <Route

            path="/soc/wazuh"

            element={

              <Guarded module="soc">

                <WazuhDashboard />

              </Guarded>

            }

          />

          <Route

            path="/soc/correlations"

            element={

              <Guarded module="soc">

                <SocCorrelations />

              </Guarded>

            }

          />

          <Route

            path="/parametres/connecteurs/wazuh"

            element={

              <Guarded module="settings">

                <WazuhConnectorSettings />

              </Guarded>

            }

          />

          <Route

            path="/administration/users"

            element={

              <Guarded module="administration">

                <AdminUsers />

              </Guarded>

            }

          />

          {URBANISM_MODULES.filter((m) => m.path !== "/schema-urbanisme" && m.path !== "/validation-metamodele").map(

            (m) => (

              <Route

                key={m.path}

                path={m.path}

                element={

                  <Guarded module="urbanism">

                    <ModulePlaceholder title={m.label} layer="urbanisme" />

                  </Guarded>

                }

              />

            )

          )}

          {CYBER_MODULES.filter(

            (m) =>

              m.path !== "/ebios" &&

              m.path !== "/registre-risques" &&

              m.path !== "/dashboard-rssi" &&

              m.path !== "/declaration-applicabilite" &&

              m.path !== "/plan-traitement-risques" &&

              m.path !== "/livrables"

          ).map((m) => (

            <Route

              key={m.path}

              path={m.path}

              element={

                <Guarded module="grc">

                  <ModulePlaceholder title={m.label} layer="cyber" />

                </Guarded>

              }

            />

          ))}

        </Routes>

      </main>

    </div>

  );

}


