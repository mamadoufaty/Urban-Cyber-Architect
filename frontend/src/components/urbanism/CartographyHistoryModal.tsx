import type { CartographyHistoryEntry, CartographyVersion } from "../../api";
import { cartographyStatusLabel, formatVersionLabel } from "./cartographySelect";

const ACTION_LABELS: Record<string, string> = {
  created: "Création",
  updated: "Modification",
  new_version: "Nouvelle version",
  submitted_for_validation: "Soumission validation",
  validated: "Validation",
  restored: "Restauration",
  duplicated: "Duplication",
  archived: "Archivage",
  unarchived: "Désarchivage",
};

function actionLabel(action: string): string {
  return ACTION_LABELS[action] ?? action;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });
}

type CartographyHistoryModalProps = {
  open: boolean;
  cartographyName: string;
  history: CartographyHistoryEntry[];
  versions: CartographyVersion[];
  loading: boolean;
  restoring: boolean;
  canRestore: boolean;
  onClose: () => void;
  onRestore: (versionId: string) => void;
};

export default function CartographyHistoryModal({
  open,
  cartographyName,
  history,
  versions,
  loading,
  restoring,
  canRestore,
  onClose,
  onRestore,
}: CartographyHistoryModalProps) {
  if (!open) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card modal-card-wide cartography-history-modal" onClick={(e) => e.stopPropagation()}>
        <h3>Historique — {cartographyName}</h3>

        {loading ? (
          <p>Chargement de l&apos;historique…</p>
        ) : (
          <>
            <h4>Versions</h4>
            <table className="cartography-history-table">
              <thead>
                <tr>
                  <th>Version</th>
                  <th>Statut</th>
                  <th>Auteur</th>
                  <th>Créée le</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {versions.map((v) => (
                  <tr key={v.id}>
                    <td>{formatVersionLabel(v)}</td>
                    <td>{cartographyStatusLabel(v.status)}</td>
                    <td>{v.author ?? "—"}</td>
                    <td>{formatDate(v.created_at)}</td>
                    <td>
                      {canRestore && !v.is_current && (
                        <button
                          type="button"
                          className="ua-btn"
                          disabled={restoring}
                          onClick={() => onRestore(v.id)}
                        >
                          Restaurer
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h4>Journal des modifications</h4>
            <table className="cartography-history-table">
              <thead>
                <tr>
                  <th>Version</th>
                  <th>Auteur</th>
                  <th>Date</th>
                  <th>Action</th>
                  <th>Commentaire</th>
                </tr>
              </thead>
              <tbody>
                {history.length === 0 && (
                  <tr>
                    <td colSpan={5}>Aucun historique pour le moment.</td>
                  </tr>
                )}
                {history.map((h) => (
                  <tr key={h.id}>
                    <td>{h.version}</td>
                    <td>{h.author ?? "—"}</td>
                    <td>{formatDate(h.created_at)}</td>
                    <td>{actionLabel(h.action)}</td>
                    <td>{h.comment ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
}
