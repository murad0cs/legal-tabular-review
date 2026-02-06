import clsx from 'clsx';
import { STATUS_CONFIG } from '../constants/index.js';

function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || { label: status, className: 'bg-slate-600/30 text-slate-300' };

  return (
    <span className={clsx('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', config.className)}>
      {config.label}
    </span>
  );
}

export default StatusBadge;
