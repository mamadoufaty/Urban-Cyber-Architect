import type { EbiosExtensionModule, EbiosIntegrationHook } from "./types";

type Props = {
  modules: EbiosExtensionModule[];
  integrations: EbiosIntegrationHook[];
};

function statusClass(status: string) {
  return status === "available" ? "status-available" : "status-planned";
}

export default function EbiosExtensionPanel({ modules, integrations }: Props) {
  return (
    <aside className="eb-extension-panel eb-panel">
      <h3>Feuille de route GRC</h3>
      <p className="eb-extension-intro">
        Points d&apos;extension pour l&apos;évolution vers une plateforme GRC complète.
      </p>

      <section>
        <h4>Modules futurs</h4>
        <ul className="eb-extension-list">
          {modules.map((m) => (
            <li key={m.id} className={statusClass(m.status)}>
              <strong>{m.label}</strong>
              <span className="eb-ext-status">{m.status}</span>
              <p>{m.description}</p>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h4>Intégrations plateforme</h4>
        <ul className="eb-extension-list">
          {integrations.map((hook) => (
            <li key={hook.id} className={statusClass(hook.status)}>
              <strong>{hook.label}</strong>
              <span className="eb-ext-status">{hook.status}</span>
              <p>{hook.description}</p>
            </li>
          ))}
        </ul>
      </section>
    </aside>
  );
}
