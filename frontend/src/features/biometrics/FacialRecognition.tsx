import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";

import { ApiError, requestApi } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { ManualAccessForm } from "../manual-access/ManualAccessForm";
import { PhotoInputs, supportedPhoto, toBase64 } from "./PhotoInputs";
import "./biometrics.css";

type Direction = "ENTRADA" | "SAIDA";
type Result = "IDENTIFICADO" | "DESCONHECIDO" | "PONTUACAO_BAIXA" | "AMBIGUO" | "CAPTURA_INVALIDA" | "FALHA_PROVEDOR";
type Receipt = { id: string; resultado: Result; cliente_nome: string | null; similaridade: number | null };

const messages: Record<Result, string> = {
  IDENTIFICADO: "Cliente identificado.",
  DESCONHECIDO: "Nenhuma referência ativa corresponde à captura.",
  PONTUACAO_BAIXA: "Similaridade insuficiente para identificar o cliente.",
  AMBIGUO: "A captura corresponde a mais de uma referência possível.",
  CAPTURA_INVALIDA: "Use uma nova foto com um único rosto visível.",
  FALHA_PROVEDOR: "O CompreFace não conseguiu concluir a identificação.",
};

const percent = new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 2 });

export function FacialRecognition({ csrf }: { csrf: string }) {
  const [direction, setDirection] = useState<Direction>("ENTRADA");
  const [photo, setPhoto] = useState<File>();
  const [receipt, setReceipt] = useState<Receipt>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const request = useRef<AbortController | null>(null);
  const eventId = useRef<string | null>(null);

  useEffect(() => () => request.current?.abort(), []);

  function choose(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.currentTarget.files?.[0];
    event.currentTarget.value = "";
    if (!selected) return;
    setReceipt(undefined);
    eventId.current = null;
    if (!supportedPhoto(selected)) {
      setPhoto(undefined);
      setError("Selecione uma foto JPG ou PNG de até 4 MB.");
      return;
    }
    setPhoto(selected);
    setError("");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!photo || request.current) return;
    const controller = new AbortController();
    request.current = controller;
    eventId.current ??= crypto.randomUUID();
    setBusy(true);
    setError("");
    setReceipt(undefined);
    try {
      const data = {
        evento_id: eventId.current, direcao: direction, imagem_base64: await toBase64(photo),
      };
      const response = await requestApi("/v1/atendimento/reconhecimento", {
        method: "POST", signal: controller.signal,
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
        body: JSON.stringify(data),
      });
      const result = await response.json() as Receipt;
      if (!controller.signal.aborted) {
        setReceipt(result);
        setPhoto(undefined);
        eventId.current = null;
      }
    } catch (reason) {
      if (!controller.signal.aborted) {
        setError(reason instanceof ApiError && reason.status === 422
          ? "A imagem não pôde ser lida. Selecione uma foto JPG ou PNG válida."
          : "Não foi possível confirmar o resultado. Tente novamente com a mesma captura.");
      }
    } finally {
      request.current = null;
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  return <section className="directory" aria-labelledby="recognition-title">
    <h2 id="recognition-title">Reconhecimento facial</h2>
    <form className="directory-form" onSubmit={event => void submit(event)}>
      <fieldset className="directory-group facial-recognition" disabled={busy}>
        <legend>Nova captura</legend>
        <label>Direção
          <select value={direction} onChange={event => {
            setDirection(event.target.value === "SAIDA" ? "SAIDA" : "ENTRADA");
            setReceipt(undefined);
            eventId.current = null;
          }}>
            <option value="ENTRADA">Entrada</option>
            <option value="SAIDA">Saída</option>
          </select>
        </label>
        <PhotoInputs onChange={choose} />
        {photo && <p role="status">Foto selecionada.</p>}
        <Button type="submit" disabled={!photo} pending={busy} pendingLabel="Identificando…">
          Identificar cliente
        </Button>
      </fieldset>
    </form>
    {error && <StatusMessage state="error" title={error} />}
    {receipt && <StatusMessage state={receipt.resultado === "IDENTIFICADO" ? "success" : "conflict"}
      title={messages[receipt.resultado]}>
      {receipt.cliente_nome && <p>{receipt.cliente_nome}</p>}
      {receipt.similaridade !== null && <p>Similaridade {percent.format(receipt.similaridade)}</p>}
      <p>A autorização de entrada é uma etapa separada.</p>
    </StatusMessage>}
    {receipt?.id && receipt.resultado !== "IDENTIFICADO" &&
      <ManualAccessForm key={receipt.id} failureId={receipt.id} csrf={csrf} />}
  </section>;
}
