import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends Omit<HTMLAttributes<HTMLDivElement>, "title"> {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children?: ReactNode;
}

export function Card({ title, subtitle, actions, children, className, ...rest }: CardProps) {
  const classes = ["ui-card", className].filter(Boolean).join(" ");
  return (
    <div className={classes} {...rest}>
      {(title || actions) && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
          }}
        >
          {title && <h3 className="ui-card__title">{title}</h3>}
          {actions}
        </div>
      )}
      {subtitle && <p className="ui-card__subtitle">{subtitle}</p>}
      {children}
    </div>
  );
}
