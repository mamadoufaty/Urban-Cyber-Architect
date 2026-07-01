import type { ReactNode } from "react";

type Props = {
  open: boolean;
  title: string;
  onClose: () => void;
  onSubmit: () => void;
  submitLabel: string;
  children: ReactNode;
  busy?: boolean;
};

export default function RecordFormModal({
  open,
  title,
  onClose,
  onSubmit,
  submitLabel,
  children,
  busy,
}: Props) {
  if (!open) return null;

  return (
    <div className="eb-modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="eb-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="eb-modal-title"
      >
        <header className="eb-modal-header">
          <h3 id="eb-modal-title">{title}</h3>
          <button type="button" className="eb-btn-icon" onClick={onClose} aria-label="Fermer">
            ×
          </button>
        </header>
        <div className="eb-modal-body">{children}</div>
        <footer className="eb-modal-footer">
          <button type="button" className="eb-btn eb-btn-ghost" onClick={onClose} disabled={busy}>
            Annuler
          </button>
          <button type="button" className="eb-btn eb-btn-primary" onClick={onSubmit} disabled={busy}>
            {busy ? "Enregistrement…" : submitLabel}
          </button>
        </footer>
      </div>
    </div>
  );
}

export function FormField({
  label,
  children,
  required,
}: {
  label: string;
  children: ReactNode;
  required?: boolean;
}) {
  return (
    <label className="eb-form-field">
      <span>
        {label}
        {required && <span className="eb-required"> *</span>}
      </span>
      {children}
    </label>
  );
}

export function FormInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input className="eb-input" {...props} />;
}

export function FormTextarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className="eb-textarea" rows={3} {...props} />;
}

export function FormSelect(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className="eb-select eb-input-full" {...props} />;
}
