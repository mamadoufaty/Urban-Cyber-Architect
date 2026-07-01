import { useEffect, useState } from "react";
import { importEbiosUrbanismAssets } from "../../../api";

type Props = {
  projectId: string;
  assessmentId: string;
  assetCount: number;
  onSyncComplete: () => Promise<void>;
};

export default function SupportingAssetsBanner({
  projectId,
  assessmentId,
  assetCount,
  onSyncComplete,
}: Props) {
  const [importing, setImporting] = useState(false);
  const [importMsg, setImportMsg] = useState<string | null>(null);

  const runImport = async (showNoopMsg = false) => {
    setImporting(true);
    setImportMsg(null);
    try {
      const result = await importEbiosUrbanismAssets(projectId, assessmentId);
      await onSyncComplete();
      if (result.imported_count > 0) {
        setImportMsg(`${result.imported_count} bien(s) support importé(s) depuis l'urbanisme.`);
      } else if (showNoopMsg) {
        setImportMsg("Cartographie urbanisme déjà synchronisée.");
      }
    } catch {
      setImportMsg("Import urbanisme indisponible.");
    } finally {
      setImporting(false);
    }
  };

  useEffect(() => {
    runImport().catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- import automatique à l'ouverture
  }, [projectId, assessmentId]);

  return (
    <div className="eb-urbanism-banner">
      <div>
        <strong>Biens supports</strong>
        <p>
          {assetCount} bien(s) support disponible(s)
          {importing ? " — synchronisation…" : " — importés depuis la cartographie Club Urba."}
        </p>
        {importMsg ? <p className="eb-urbanism-msg">{importMsg}</p> : null}
      </div>
      <button
        type="button"
        className="eb-btn eb-btn-ghost"
        onClick={() => runImport(true)}
        disabled={importing}
      >
        Synchroniser urbanisme
      </button>
    </div>
  );
}
