import { requestApi } from "../../lib/api/auth";

export type Equipment = {
  id: string;
  nome: string;
  categoria: string | null;
  descricao: string | null;
  imagem_url: string | null;
};

export type InventoryItem = Equipment & { ativo: boolean; operacional: boolean; revisao: number };
export type Page<T> = { itens: T[]; pagina: number; limite: number; total: number };
export type EquipmentFields = {
  nome: string;
  categoria: string;
  descricao: string;
  ativo: boolean;
  operacional: boolean;
  imagem_base64?: string | null;
};

const catalog = "/v1/equipamentos";
const inventory = "/v1/admin/equipamentos";

export async function equipmentCatalog(page: number, signal: AbortSignal): Promise<Page<Equipment>> {
  const response = await requestApi(catalog + "?pagina=" + page, { signal });
  return response.json() as Promise<Page<Equipment>>;
}

export async function equipmentInventory(page: number, signal: AbortSignal): Promise<Page<InventoryItem>> {
  const response = await requestApi(inventory + "?pagina=" + page, { signal });
  return response.json() as Promise<Page<InventoryItem>>;
}

export async function saveEquipment(data: EquipmentFields, csrf: string, requestId: string, item?: InventoryItem) {
  const path = item ? inventory + "/" + encodeURIComponent(item.id) : inventory;
  const body = item ? { ...data, revisao: item.revisao } : { ...data, solicitacao_id: requestId };
  await requestApi(path, {
    method: item ? "PUT" : "POST",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify(body),
  });
}
