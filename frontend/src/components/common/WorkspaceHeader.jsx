export function WorkspaceHeader({ eyebrow, title, description, children }) {
  return (
    <header className="workspace-header">
      <div className="min-w-0 max-w-3xl">
        <p className="eyebrow"><span aria-hidden="true" />{eyebrow}</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-text-hi sm:text-4xl">{title}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-text-mid sm:text-base">{description}</p>
      </div>
      {children && <div className="flex max-w-full shrink-0 flex-wrap items-center gap-2">{children}</div>}
    </header>
  );
}
