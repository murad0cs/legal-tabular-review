import clsx from 'clsx';

function Card({ children, className, glow, ...props }) {
  return (
    <div
      className={clsx(
        'glass rounded-2xl p-6',
        glow === 'primary' && 'glow-primary',
        glow === 'accent' && 'glow-accent',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export default Card;
