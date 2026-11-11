import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../lib/api/auth";
import { equipmentCatalog, equipmentInventory, saveEquipment, type Equipment,
  type EquipmentFields, type InventoryItem, type Page } from "./api";
import "./equipment.css";

function useEquipmentPage<T>(load: (page: number, signal: AbortSignal) => Promise<Page<T>>) {
  const [query, setQuery] = useState({ page: 1 });
  const [page, setPage] = useState<Page<T> | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    void load(query.page, controller.signal).then(
      (result) => { if (!controller.signal.aborted) setPage(result); },
      () => { if (!controller.signal.aborted) setError(true); },
    );
    return () => controller.abort();
  }, [load, query]);

  function reload(number = query.page) {
    setPage(null);
    setError(false);
    setQuery({ page: number });
  }

  return { page, error, reload };
}

function Pager({ page, reload }: { page: Page<Equipment>; reload: (page: number) => void }) {
  if (page.pagina === 1 && page.total <= page.limite) return null;
  return (
    <nav className="equipment-actions" aria-label="Páginas de equipamentos">
      <button type="button" disabled={page.pagina <= 1} onClick={() => reload(page.pagina - 1)}>Anterior</button>
      <button type="button" disabled={page.pagina * page.limite >= page.total}
        onClick={() => reload(page.pagina + 1)}>Próxima</button>
    </nav>
  );
}

function EquipmentPhoto({ item }: { item: Equipment }) {
  return item.imagem_url && (
    <img className="equipment-photo" src={item.imagem_url} alt={"Foto de " + item.nome} loading="lazy" />
  );
}

export function EquipmentCatalogPage() {
  const { page, error, reload } = useEquipmentPage(equipmentCatalog);
  return (
    <section aria-labelledby="equipment-catalog-title">
      <h2 id="equipment-catalog-title">Equipamentos disponíveis</h2>
      <p><Link to="/">Voltar ao início</Link></p>
      {page ? (
        <>
          {page.itens.length ? (
            <ul className="equipment-list">
              {page.itens.map((item) => (
                <li key={item.id} className="equipment-card">
                  <EquipmentPhoto item={item} />
                  <h3>{item.nome}</h3>
                  {item.categoria && <p>{item.categoria}</p>}
                  {item.descricao && <p>{item.descricao}</p>}
                </li>
              ))}
            </ul>
          ) : <p>Nenhum equipamento disponível nesta página.</p>}
          <Pager page={page} reload={reload} />
        </>
      ) : error ? (
        <>
          <p role="alert">Não foi possível consultar os equipamentos.</p>
          <button type="button" onClick={() => reload()}>Tentar novamente</button>
        </>
      ) : <p role="status">Carregando equipamentos…</p>}
    </section>
  );
}

function toBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      const value = String(reader.result);
      resolve(value.slice(value.indexOf(",") + 1));
    }, { once: true });
    reader.addEventListener("error", reject, { once: true });
    reader.readAsDataURL(file);
  });
}

function EquipmentForm({ item, csrf, close, onSave }: {
  item?: InventoryItem;
  csrf: string;
  close: () => void;
  onSave: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [removeImage, setRemoveImage] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [requestId] = useState(() => crypto.randomUUID());

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const fields = new FormData(event.currentTarget);
    const data: EquipmentFields = {
      nome: String(fields.get("nome") ?? "").trim(),
      categoria: String(fields.get("categoria") ?? "").trim(),
      descricao: String(fields.get("descricao") ?? "").trim(),
      ativo: fields.has("ativo"),
      operacional: fields.has("operacional"),
    };
    if (!data.nome) {
      setError("Informe o nome do equipamento.");
      return;
    }
    if (file && file.size > 4 * 1024 * 1024) {
      setError("Selecione uma imagem de até 4 MB.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      if (file) data.imagem_base64 = await toBase64(file);
      else if (removeImage) data.imagem_base64 = null;
      await saveEquipment(data, csrf, requestId, item);
      onSave();
    } catch (failure) {
      const status = failure instanceof ApiError ? failure.status : 0;
      if (status === 409) setError("O cadastro mudou. Volte ao inventário e confira o registro antes de tentar novamente.");
      else if (status === 413 || status === 422) setError("Revise os campos e use uma imagem JPG ou PNG válida, de até 4 MB e 2048 px por lado.");
      else if (status === 401 || status === 403) setError("Sua sessão perdeu a permissão para salvar este equipamento.");
      else setError("Não foi possível confirmar o salvamento. Os dados continuam nesta tela.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="equipment-form" onSubmit={(event) => void submit(event)}>
      <fieldset disabled={busy}>
        <legend>{item ? "Editar equipamento" : "Novo equipamento"}</legend>
        <label htmlFor="equipment-name">Nome</label>
        <input id="equipment-name" name="nome" required maxLength={120} defaultValue={item?.nome} />
        <label htmlFor="equipment-category">Categoria</label>
        <input id="equipment-category" name="categoria" maxLength={80} defaultValue={item?.categoria ?? ""} />
        <label htmlFor="equipment-description">Descrição</label>
        <textarea id="equipment-description" name="descricao" maxLength={1000} defaultValue={item?.descricao ?? ""} />
        <label className="equipment-checkbox"><input type="checkbox" name="ativo" defaultChecked={item?.ativo ?? true} /> Ativo</label>
        <label className="equipment-checkbox"><input type="checkbox" name="operacional" defaultChecked={item?.operacional ?? true} /> Operacional</label>
        <label htmlFor="equipment-image">Foto (JPG ou PNG)</label>
        <input id="equipment-image" type="file" accept="image/jpeg,image/png" onChange={(event) => {
          setFile(event.target.files?.[0] ?? null);
          setRemoveImage(false);
        }} />
        {item?.imagem_url && !file && (
          <>
            {!removeImage && <EquipmentPhoto item={item} />}
            <label className="equipment-checkbox">
              <input type="checkbox" checked={removeImage} onChange={(event) => setRemoveImage(event.target.checked)} />
              Remover foto atual
            </label>
          </>
        )}
      </fieldset>
      {error && <p role="alert">{error}</p>}
      <div className="equipment-actions">
        <button type="submit" disabled={busy}>{busy ? "Salvando…" : "Salvar equipamento"}</button>
        <button type="button" disabled={busy} onClick={close}>Voltar ao inventário</button>
      </div>
    </form>
  );
}

export function EquipmentInventoryPage({ csrf }: { csrf: string }) {
  const { page, error, reload } = useEquipmentPage(equipmentInventory);
  const [editing, setEditing] = useState<InventoryItem | "new" | null>(null);
  const [notice, setNotice] = useState("");

  function edit(item: InventoryItem | "new") {
    setNotice("");
    setEditing(item);
  }

  function close() {
    setEditing(null);
    reload();
  }

  return (
    <section aria-labelledby="equipment-admin-title">
      <h3 id="equipment-admin-title">Gerenciar equipamentos</h3>
      {notice && <p role="status">{notice}</p>}
      {editing ? (
        <EquipmentForm key={editing === "new" ? "new" : editing.id} csrf={csrf}
          item={editing === "new" ? undefined : editing} close={close}
          onSave={() => { setEditing(null); reload(1); setNotice("Equipamento salvo."); }} />
      ) : (
        <>
          <button type="button" onClick={() => edit("new")}>Cadastrar equipamento</button>
          {page ? (
            <>
              {page.itens.length ? (
                <ul className="equipment-list">
                  {page.itens.map((item) => (
                    <li key={item.id} className="equipment-card">
                      <h4>{item.nome}</h4>
                      <p>{item.ativo ? "Ativo" : "Inativo"} · {item.operacional ? "Operacional" : "Indisponível"}</p>
                      <button type="button" aria-label={"Editar " + item.nome} onClick={() => edit(item)}>Editar</button>
                    </li>
                  ))}
                </ul>
              ) : <p>Nenhum equipamento cadastrado nesta página.</p>}
              <Pager page={page} reload={reload} />
            </>
          ) : error ? (
            <>
              <p role="alert">Não foi possível consultar o inventário.</p>
              <button type="button" onClick={() => reload()}>Tentar novamente</button>
            </>
          ) : <p role="status">Carregando inventário…</p>}
        </>
      )}
    </section>
  );
}
