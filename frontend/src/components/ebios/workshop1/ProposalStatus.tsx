// Statut d'une proposition générée automatiquement depuis la cartographie
// (§ Atelier 1 — Générer automatiquement depuis la cartographie). Un élément
// "draft" (saisi manuellement) n'affiche aucun badge : seul le cycle
// proposé → validé/rejeté introduit par la génération automatique en a un.

export function proposalStatusLabel(status?: string): string | null {
  switch (status) {
    case "proposed":
      return "Proposé";
    case "validated":
      return "Validé";
    case "rejected":
      return "Rejeté";
    default:
      return null;
  }
}

export function proposalStatusClass(status?: string): string {
  switch (status) {
    case "proposed":
      return "status-proposed";
    case "validated":
      return "status-validated";
    case "rejected":
      return "status-rejected";
    default:
      return "";
  }
}

type Props = {
  status?: string;
  onValidate: () => void;
  onReject: () => void;
  onRestore: () => void;
  busy?: boolean;
};

export default function ProposalActions({ status, onValidate, onReject, onRestore, busy }: Props) {
  if (status === "proposed") {
    return (
      <>
        <button type="button" className="eb-btn eb-btn-primary" onClick={onValidate} disabled={busy}>
          Valider
        </button>
        <button type="button" className="eb-btn eb-btn-ghost" onClick={onReject} disabled={busy}>
          Rejeter
        </button>
      </>
    );
  }
  if (status === "rejected") {
    return (
      <button type="button" className="eb-btn eb-btn-ghost" onClick={onRestore} disabled={busy}>
        Restaurer
      </button>
    );
  }
  return null;
}
