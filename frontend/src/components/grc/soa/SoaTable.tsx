import type { SoaControlRow } from "./types";

type Props = {
  rows: SoaControlRow[];
};

function badgeClass(value: string, positive = "Oui"): string {
  if (value === positive) return "soa-badge soa-badge-yes";
  if (value === "Non") return "soa-badge soa-badge-no";
  return "soa-badge";
}

export default function SoaTable({ rows }: Props) {
  if (!rows.length) {
    return <div className="soa-empty">Aucun contrôle ne correspond aux filtres.</div>;
  }

  return (
    <div className="soa-table-wrap">
      <table className="soa-table">
        <thead>
          <tr>
            <th>Réf. ISO</th>
            <th>Contrôle</th>
            <th>Applicable</th>
            <th>Justification</th>
            <th>Implémenté</th>
            <th>Source EBIOS</th>
            <th>Mesure</th>
            <th>Décision</th>
            <th>Responsable</th>
            <th>Statut</th>
            <th>Commentaire</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.control_id} className={row.applicable === "Oui" ? "soa-row-applicable" : ""}>
              <td className="soa-cell-ref">{row.iso_reference}</td>
              <td>{row.control_name}</td>
              <td>
                <span className={badgeClass(row.applicable)}>{row.applicable}</span>
              </td>
              <td className="soa-cell-text">{row.justification}</td>
              <td>
                <span className={badgeClass(row.implemented)}>{row.implemented}</span>
              </td>
              <td>{row.ebios_source || "—"}</td>
              <td>{row.associated_measure || "—"}</td>
              <td>{row.decision || "—"}</td>
              <td>{row.responsible || "—"}</td>
              <td>{row.status || "—"}</td>
              <td className="soa-cell-text">{row.comment || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
