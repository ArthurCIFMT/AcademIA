import { useEffect, useRef, useState, type ChangeEvent } from "react";

import { ApiError, requestApi } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { DirectoryTag } from "../clients/directory-ui";
import { PhotoInputs, supportedPhoto, toBase64 } from "./PhotoInputs";
import "./biometrics.css";

type ReferenceStatus = {
  cadastrada: boolean;
  elegivel: boolean;
  disponivel: boolean;
  atualizada_em: string | null;
  pendencia: "ENVIO" | "TROCA" | null;
};

async function readStatus(path: string, options: RequestInit): Promise<ReferenceStatus> {
  return (await requestApi(path, options)).json() as Promise<ReferenceStatus>;
}

function errorText(error: unknown) {
  const status = error instanceof ApiError ? error.status : null;
  if (status === 422 || status === 413) {
    return "Use uma foto JPG ou PNG, de até 4 MB, com um único rosto nítido e bem iluminado.";
  }
  if (status === 409) return "Confira a matrícula e veja se há uma operação pendente.";
  if (status === 503) return "O CompreFace não confirmou a operação. Confira o estado antes de tentar novamente.";
  return "Não foi possível confirmar a operação. Confira o estado da referência.";
}

export function ClientBiometrics({ clientId, csrf }: { clientId: string; csrf: string }) {
  const path = "/v1/atendimento/clientes/" + encodeURIComponent(clientId) + "/biometria";
  const [photo, setPhoto] = useState<File>();
  const [status, setStatus] = useState<ReferenceStatus>();
  const [failed, setFailed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const request = useRef<AbortController | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    void readStatus(path, { signal: controller.signal }).then(
      next => { if (!controller.signal.aborted) setStatus(next); },
      () => { if (!controller.signal.aborted) setFailed(true); },
    );
    return () => controller.abort();
  }, [path, version]);

  useEffect(() => () => request.current?.abort(), []);

  function reload() {
    setFailed(false);
    setStatus(undefined);
    setVersion(current => current + 1);
  }

  function choose(event: ChangeEvent<HTMLInputElement>) {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = "";
    if (!file) return;
    setError("");
    setNotice("");
    if (!supportedPhoto(file)) {
      setError("Selecione um arquivo JPG ou PNG de até 4 MB.");
      setPhoto(undefined);
      return;
    }
    setPhoto(file);
  }

  async function submit(recover: boolean) {
    if (request.current || (!recover && !photo)) return;
    const controller = new AbortController();
    request.current = controller;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const body = !recover && photo ? JSON.stringify({ imagem_base64: await toBase64(photo) }) : undefined;
      const result = await readStatus(path + (recover ? "/pendencia" : ""), {
        method: "POST", signal: controller.signal,
        headers: { "X-CSRF-Token": csrf, ...(body ? { "Content-Type": "application/json" } : {}) },
        body,
      });
      if (controller.signal.aborted) return;
      setPhoto(undefined);
      setStatus(result);
      setNotice(recover ? "Pendência verificada." : "Referência facial cadastrada.");
    } catch (reason) {
      if (!controller.signal.aborted) {
        setError(errorText(reason));
        setPhoto(undefined);
        reload();
      }
    } finally {
      request.current = null;
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  return <section className="directory-card facial-reference" aria-labelledby="biometria-title">
    <h4 id="biometria-title">Referência facial</h4>
    {notice && <p role="status">{notice}</p>}
    {error && <StatusMessage state="error" title={error} />}
    {failed ? <>
      <StatusMessage state="error" title="Não foi possível consultar a referência facial." />
      <Button variant="secondary" onClick={reload}>Tentar de novo</Button>
    </> : !status ? <StatusMessage state="loading" title="Consultando referência facial…" /> : <>
      <DirectoryTag tone={status.cadastrada ? "positive" : "neutral"}>
        {status.cadastrada ? "Referência cadastrada" : "Sem referência cadastrada"}
      </DirectoryTag>
      {!status.elegivel && <p>O cadastro facial exige um cliente habilitado com matrícula registrada.</p>}
      {!status.disponivel && <p>O CompreFace precisa estar configurado para cadastrar uma foto.</p>}
      {status.pendencia && <StatusMessage state="conflict" title="Há uma operação facial pendente.">
        Verifique a pendência para retomar a operação.
      </StatusMessage>}
      {status.elegivel && status.disponivel && (status.pendencia
        ? <Button onClick={() => void submit(true)} pending={busy}>Verificar pendência</Button>
        : <form className="directory-form" onSubmit={event => { event.preventDefault(); void submit(false); }}>
          <fieldset className="directory-fieldset" disabled={busy}>
            <p className="directory-meta">Use JPG ou PNG de até 4 MB com um único rosto.</p>
            <PhotoInputs onChange={choose} />
            {photo && <p role="status">Foto selecionada.</p>}
            <Button type="submit" pending={busy} disabled={!photo}>
              {status.cadastrada ? "Substituir foto" : "Cadastrar foto"}
            </Button>
          </fieldset>
        </form>)}
    </>}
  </section>;
}
