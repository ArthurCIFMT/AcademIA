import { useEffect, useRef, useSyncExternalStore, type MouseEvent, type ReactNode } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigationType } from "react-router-dom";
import type { Role } from "../lib/api/auth";
import { Button, NavigationDisclosure } from "../ui/primitives";
import { areaHome, areaMenu, areaShortcuts, areas, ownProfilePath } from "./areaNavigation";
import "./frames.css";

const mobileMenuQuery = "(max-width: 47rem)";

function subscribeToMenuWidth(onChange: () => void) {
  const media = window.matchMedia?.(mobileMenuQuery);
  media?.addEventListener("change", onChange);
  return () => media?.removeEventListener("change", onChange);
}

function hasMobileMenu() {
  return window.matchMedia?.(mobileMenuQuery).matches ?? false;
}

function useMainFocus() {
  const ref = useRef<HTMLElement>(null);
  const previousPath = useRef<string>(undefined);
  const { pathname } = useLocation();
  const navigation = useNavigationType();
  useEffect(() => {
    if (previousPath.current === undefined ? navigation !== "POP" : previousPath.current !== pathname) {
      ref.current?.focus();
    }
    previousPath.current = pathname;
  }, [pathname, navigation]);
  return ref;
}

function SkipLink({ focusMain }: { focusMain: () => void }) {
  return <a className="site-skip" href="#conteudo" onClick={event => {
    event.preventDefault();
    focusMain();
  }}>Ir para o conteúdo</a>;
}

function Brand({ to }: { to: string }) {
  return <Link className="site-brand" to={to}>
    <span className="site-brand-mark" aria-hidden="true">A</span>
    <span className="site-brand-name">AcademIA</span>
  </Link>;
}

export function PublicFrame({ children }: { children: ReactNode }) {
  const main = useMainFocus();
  return (
    <>
      <SkipLink focusMain={() => main.current?.focus()} />
      <header className="site-bar"><div className="site-bar-inner"><Brand to="/" /></div></header>
      <main id="conteudo" className="shell public-main" tabIndex={-1} ref={main}>{children}</main>
    </>
  );
}

export function PublicLayout() {
  return <PublicFrame><Outlet /></PublicFrame>;
}

function SectionMenu({ role, activePath, maintenance, focusMain }: {
  role: Role; activePath: string; maintenance: boolean; focusMain: () => void;
}) {
  const { pathname } = useLocation();
  const mobile = useSyncExternalStore(subscribeToMenuWidth, hasMobileMenu);
  const items = areaMenu(role, maintenance);
  const active = items.find(item => item.path === activePath)?.label ?? "Menu da área";

  function closeOnFollow(event: MouseEvent<HTMLAnchorElement>) {
    if (event.defaultPrevented || event.button !== 0 || event.altKey || event.shiftKey || event.metaKey || event.ctrlKey) return;
    const disclosure = event.currentTarget.closest("details");
    if (disclosure) {
      disclosure.open = false;
      focusMain();
    }
  }

  const links = (entries: typeof items, disclosure = false) => (
    <ul className="site-sections">
      {entries.map(item => <li key={item.path}>
        <Link to={item.path} aria-current={item.path !== activePath ? undefined
          : item.path === pathname.replace(/\/+$/, "").toLowerCase() ? "page" : "location"}
          onClick={disclosure ? closeOnFollow : undefined}>{item.label}</Link>
      </li>)}
    </ul>
  );
  return (
    <aside className="site-sidebar">
      {mobile ? <>
        <nav className="site-shortcuts" aria-label="Atalhos da área">
          {links(areaShortcuts[role].flatMap(path => items.filter(item => item.path === path)))}
        </nav>
        <div className="site-mobile-menu">
          <NavigationDisclosure key={pathname} label={"Menu · " + active} navigationLabel="Seções da área">
            {links(items, true)}
          </NavigationDisclosure>
        </div>
      </> : <nav aria-label="Seções da área">{links(items)}</nav>}
    </aside>
  );
}

export function AreaFrame({ role, allowed, activePath, maintenance, signOut, children }: {
  role?: Role; allowed: Role[]; activePath: string; maintenance: boolean;
  signOut: () => Promise<void>; children: ReactNode;
}) {
  const main = useMainFocus();
  return (
    <>
      <SkipLink focusMain={() => main.current?.focus()} />
      <header className="site-bar">
        <div className="site-bar-inner">
          <Brand to={role ? areaHome[role] : "/area"} />
          <div className="site-account">
            {(allowed.length > 1 || (!role && allowed.length > 0)) &&
              <nav aria-label="Áreas disponíveis">
                <ul className="site-areas">{allowed.map(item => <li key={item}>
                  <NavLink to={areaHome[item]} aria-current={item === role ? "location" : undefined}>
                    {areas[item].label}
                  </NavLink>
                </li>)}</ul>
              </nav>}
            {role && <NavLink className="site-account-profile" to={ownProfilePath(role)}>Meu perfil</NavLink>}
            <Button variant="secondary" onClick={() => void signOut()}>Sair</Button>
          </div>
        </div>
      </header>
      <div className={role ? "site-workspace" : undefined}>
        {role && <SectionMenu role={role} activePath={activePath} maintenance={maintenance}
          focusMain={() => main.current?.focus()} />}
        <main id="conteudo" className={role ? "shell site-content" : "shell public-main"}
          tabIndex={-1} ref={main}>
          {role && <h1 className="site-area-heading">{areas[role].title}</h1>}
          {children}
        </main>
      </div>
    </>
  );
}
