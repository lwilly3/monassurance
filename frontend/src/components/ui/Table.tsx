import * as React from "react";

export interface TableProps extends React.HTMLAttributes<HTMLTableElement> {
  caption?: string;
}

export function Table({ caption, className = "", ...props }: TableProps) {
  return (
    <div className="overflow-x-auto">
      <table
        className={[
          "w-full border-collapse text-sm text-left text-[var(--color-fg)]",
          className,
        ].join(" ")}
        {...props}
      />
      {caption && <p className="mt-2 text-xs text-[var(--color-muted)]">{caption}</p>}
    </div>
  );
}

export function Th(props: React.ThHTMLAttributes<HTMLTableCellElement>) {
  const { className = "", ...rest } = props;
  return (
    <th
      className={[
        "border-b bg-black/5 px-3 py-2 font-medium text-[var(--color-fg)]",
        className,
      ].join(" ")}
      scope="col"
      {...rest}
    />
  );
}

export function Td(props: React.TdHTMLAttributes<HTMLTableCellElement>) {
  const { className = "", ...rest } = props;
  return (
    <td className={["border-b px-3 py-2", className].join(" ")} {...rest} />
  );
}
