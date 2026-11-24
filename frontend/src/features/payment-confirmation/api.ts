import { requestApi } from "../../lib/api/auth";

export const methods = {
  PIX: "Pix",
  DINHEIRO: "Dinheiro",
  CARTAO: "Cartão",
  TRANSFERENCIA: "Transferência",
  OUTRO: "Outro",
} as const;

export type PaymentFields = {
  valor: string;
  pago_em: string;
  metodo: keyof typeof methods;
  referencia_externa: string;
};

export type ManualPayment = PaymentFields & {
  id: string;
  estado: "CONFIRMADO" | "ANULADO";
  confirmado_em: string;
  registrado_por_nome: string | null;
  substitui_id: string | null;
  cobranca_id?: string | null;
  anulado_em: string | null;
  anulado_por_nome: string | null;
  motivo_anulacao: string | null;
};

export type PaymentPage = {
  cliente_nome: string;
  itens: ManualPayment[];
  pagina: number;
  limite: number;
  total: number;
};

const path = (id: string) => "/v1/admin/clientes/" + encodeURIComponent(id) + "/pagamentos";

export async function listPayments(id: string, page: number, signal: AbortSignal) {
  const response = await requestApi(path(id) + "?pagina=" + page, { signal });
  return response.json() as Promise<PaymentPage>;
}

export async function postPayment(id: string, suffix: string, body: object, csrf: string) {
  await requestApi(path(id) + suffix, {
    method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify(body),
  });
}
