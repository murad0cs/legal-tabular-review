import clsx from 'clsx';

const COLORS = {
  high: { text: 'text-emerald-400', bg: 'bg-emerald-500/20', fill: 'bg-emerald-500' },
  medium: { text: 'text-amber-400', bg: 'bg-amber-500/20', fill: 'bg-amber-500' },
  low: { text: 'text-red-400', bg: 'bg-red-500/20', fill: 'bg-red-500' },
};

function ConfidenceBadge({ value, showBar = false }) {
  const percentage = Math.round(value * 100);
  const level = percentage >= 80 ? 'high' : percentage >= 50 ? 'medium' : 'low';
  const colors = COLORS[level];

  if (showBar) {
    return (
      <div className="flex items-center gap-2">
        <div className="flex-1 h-2 rounded-full bg-slate-700 overflow-hidden">
          <div className={clsx('h-full rounded-full transition-all', colors.fill)} style={{ width: `${percentage}%` }} />
        </div>
        <span className={clsx('text-xs font-medium w-10 text-right', colors.text)}>{percentage}%</span>
      </div>
    );
  }

  return (
    <span className={clsx('inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', colors.bg, colors.text)}>
      {percentage}%
    </span>
  );
}

export default ConfidenceBadge;
