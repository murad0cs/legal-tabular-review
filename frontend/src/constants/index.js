export const DOCUMENT_TYPES = [
  { value: 'nda', label: 'Non-Disclosure Agreement' },
  { value: 'contract', label: 'Service Agreement' },
  { value: 'lease', label: 'Commercial Lease' },
  { value: 'employment', label: 'Employment Agreement' },
  { value: 'other', label: 'Other' },
];

export const FIELD_TYPES = [
  { value: 'text', label: 'Text' },
  { value: 'date', label: 'Date' },
  { value: 'currency', label: 'Currency' },
  { value: 'party', label: 'Party/Entity' },
  { value: 'clause', label: 'Clause' },
];

export const NORMALIZATION_RULES = [
  { value: '', label: 'None' },
  { value: 'iso_date', label: 'ISO Date (YYYY-MM-DD)' },
  { value: 'uppercase', label: 'Uppercase' },
  { value: 'lowercase', label: 'Lowercase' },
  { value: 'currency_usd', label: 'USD Currency ($X,XXX.XX)' },
  { value: 'currency_eur', label: 'EUR Currency (€X.XXX,XX)' },
  { value: 'trim', label: 'Trim Whitespace' },
];

export const STATUS_CONFIG = {
  pending: { label: 'Pending', className: 'bg-slate-600/30 text-slate-300' },
  approved: { label: 'Approved', className: 'bg-emerald-500/20 text-emerald-400' },
  rejected: { label: 'Rejected', className: 'bg-red-500/20 text-red-400' },
  edited: { label: 'Edited', className: 'bg-amber-500/20 text-amber-400' },
  draft: { label: 'Draft', className: 'bg-slate-600/30 text-slate-300' },
  in_progress: { label: 'In Progress', className: 'bg-blue-500/20 text-blue-400' },
  completed: { label: 'Completed', className: 'bg-emerald-500/20 text-emerald-400' },
  needs_review: { label: 'Needs Review', className: 'bg-amber-500/20 text-amber-400' },
  ready: { label: 'Ready', className: 'bg-emerald-500/20 text-emerald-400' },
  processing: { label: 'Processing', className: 'bg-blue-500/20 text-blue-400' },
  error: { label: 'Error', className: 'bg-red-500/20 text-red-400' },
  uploaded: { label: 'Uploaded', className: 'bg-slate-600/30 text-slate-300' },
};

