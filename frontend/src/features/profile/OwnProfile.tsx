import { useEffect, useState, type FormEvent } from "react";

import { requestApi } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";

type Profile = {
  email: string;
  endereco: string | null;
  nome_cliente: string | null;
  data_nascimento: string | null;
  telefone: string | null;
  nome_funcionario: string | null;
  cargo: string | null;
  data_admissao: string | null;
  foto_disponivel: boolean;
};

const endpoint = "/v1/meu-perfil";

function dateLabel(value: string) {
  return value.split("-").reverse().join("/");
}

function ProfilePhoto({ name, available }: { name: string; available: boolean }) {
  const [url, setUrl] = useState<string>();
  useEffect(() => {
    const controller = new AbortController();
    let objectUrl: string | undefined;
    if (available && typeof URL.createObjectURL === "function") {
      void requestApi(endpoint + "/foto", { signal: controller.signal, headers: { Accept: "image/jpeg" } })
        .then(response => response.blob())
        .then(image => {
          if (controller.signal.aborted) return;
          objectUrl = URL.createObjectURL(image);
          setUrl(objectUrl);
        }).catch(() => { /* As iniciais permanecem disponíveis. */ });
    }
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [available]);
  return available && url
    ? <img width={96} height={96} src={url} alt="Minha foto de perfil" />
    : <p aria-label="Iniciais do perfil">{name.split(/\s+/).slice(0, 2).map(part => part.charAt(0)).join("").toLocaleUpperCase("pt-BR")}</p>;
}

export function OwnProfile({ csrf }: { csrf: string }) {
  const [profile, setProfile] = useState<Profile>();
  const [address, setAddress] = useState("");
  const [loadError, setLoadError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<"saved" | "error">();

  useEffect(() => {
    const request = new AbortController();
    void requestApi(endpoint, { cache: "no-store", signal: request.signal })
      .then(response => response.json() as Promise<Profile>)
      .then(result => {
        if (request.signal.aborted) return;
        setProfile(result);
        setAddress(result.endereco ?? "");
      }).catch(() => { if (!request.signal.aborted) setLoadError(true); });
    return () => request.abort();
  }, [attempt]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setNotice(undefined);
    try {
      const response = await requestApi(endpoint + "/endereco", {
        method: "PATCH", cache: "no-store",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
        body: JSON.stringify({ endereco: address.trim() || null }),
      });
      const result = await response.json() as Profile;
      setProfile(result);
      setAddress(result.endereco ?? "");
      setNotice("saved");
    } catch {
      setNotice("error");
    } finally {
      setBusy(false);
    }
  }

  return <section className="directory" aria-labelledby="profile-title">
    <h2 id="profile-title">Meu perfil</h2>
    {loadError ? <>
      <StatusMessage state="error" title="Não foi possível carregar seu perfil." />
      <Button onClick={() => { setLoadError(false); setAttempt(value => value + 1); }}>Tentar novamente</Button>
    </> : !profile ? <StatusMessage state="loading" title="Carregando perfil…" /> : <>
      <ProfilePhoto name={profile.nome_cliente || profile.nome_funcionario || profile.email} available={profile.foto_disponivel} />
      <dl>
        {profile.nome_cliente && <><dt>Nome no cadastro de cliente</dt><dd>{profile.nome_cliente}</dd></>}
        {profile.nome_funcionario && <><dt>Nome no cadastro de funcionário</dt><dd>{profile.nome_funcionario}</dd></>}
        <dt>E-mail</dt><dd>{profile.email}</dd>
        {profile.data_nascimento && <><dt>Data de nascimento</dt><dd>{dateLabel(profile.data_nascimento)}</dd></>}
        {profile.telefone && <><dt>Telefone</dt><dd>{profile.telefone}</dd></>}
        {profile.cargo && <><dt>Cargo</dt><dd>{profile.cargo}</dd></>}
        {profile.data_admissao && <><dt>Data de admissão</dt><dd>{dateLabel(profile.data_admissao)}</dd></>}
      </dl>
      <form className="directory-form" onSubmit={event => void save(event)}>
        <label className="ac-field">Endereço (opcional)
          <textarea className="ac-field-control" autoComplete="street-address" rows={3} maxLength={300}
            value={address} disabled={busy} onChange={event => { setAddress(event.target.value); setNotice(undefined); }} />
        </label>
        <Button type="submit" pending={busy}>Salvar endereço</Button>
      </form>
      {notice === "saved" && <StatusMessage state="success" title="Endereço salvo." />}
      {notice === "error" && <StatusMessage state="error" title="Não foi possível salvar o endereço. Tente novamente." />}
    </>}
  </section>;
}
