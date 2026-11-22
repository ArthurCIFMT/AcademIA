import type { ReactNode } from "react";
import "./auth.css";

export function AccessPanel({ title, introduction, children }: {
  title: string; introduction: string; children: ReactNode;
}) {
  return (
    <section className="access-panel" aria-labelledby="titulo-acesso">
      <div className="access-intro">
        <p>AcademIA</p>
        <p>{introduction}</p>
      </div>
      <div className="access-card">
        <h1 id="titulo-acesso">{title}</h1>
        {children}
      </div>
    </section>
  );
}
