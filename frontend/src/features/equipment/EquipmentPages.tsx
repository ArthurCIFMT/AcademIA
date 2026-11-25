import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { DirectoryPager, DirectoryTag, useDirectoryFocus } from "../clients/directory-ui";
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

function EquipmentPhoto({ item }: { item: Equipment }) {
  const [failed, setFailed] = useState<string | null>(null);
  const source = item.imagem_url;
  return source && source !== failed
    ? <img className="equipment-photo" src={source} alt={"Foto de " + item.nome} loading="lazy" onError={() => setFailed(source)} />
    : <p className="equipment-photo-fallback">{source ? "Foto indisponível" : "Foto não cadastrada"}</p>;
}

export function EquipmentCatalogPage({ inClientArea = false }: { inClientArea?: boolean }) {
  const { page, error, reload } = useEquipmentPage(equipmentCatalog);
  return (
    <section className="directory" aria-labelledby="equipment-catalog-title">
      <h2 id="equipment-catalog-title">Equipamentos disponíveis</h2>
      {!inClientArea && <p><Link to="/">Voltar ao início</Link></p>}
      {page ? (
        <>
          {page.itens.length ? (
            <ul className="directory-cards" aria-label="Equipamentos disponíveis">
              {page.itens.map((item) => (
                <li key={item.id} className="directory-card">
                  <EquipmentPhoto item={item} />
                  <h3>{item.nome}</h3>
                  {item.categoria && <p>{item.categoria}</p>}
                  {item.descricao && <p>{item.descricao}</p>}
                </li>
              ))}
            </ul>
          ) : <StatusMessage state="empty" title="Nenhum equipamento disponível nesta página." />}
          <DirectoryPager page={page} label="Páginas de equipamentos" changePage={reload} />
        </>
      ) : error ? (
        <>
          <StatusMessage state="error" title="Não foi possível consultar os equipamentos." />
          <Button variant="secondary" onClick={() => reload()}>Tentar novamente</Button>
        </>
      ) : <StatusMessage state="loading" title="Carregando equipamentos…" />}
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
  const saving = useRef(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving.current) return;
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
    saving.current = true;
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
      saving.current = false;
      setBusy(false);
    }
  }

  return (
    <form className="directory-form" onSubmit={(event) => void submit(event)}>
      <fieldset className="directory-fieldset" disabled={busy}>
        <fieldset className="directory-group">
          <legend>Identificação</legend>
          <label className="ac-field">Nome<input name="nome" required maxLength={120} defaultValue={item?.nome} /></label>
          <label className="ac-field">Categoria<input name="categoria" maxLength={80} defaultValue={item?.categoria ?? ""} /></label>
          <label className="ac-field">Descrição<textarea name="descricao" maxLength={1000} defaultValue={item?.descricao ?? ""} /></label>
        </fieldset>
        <fieldset className="directory-group">
          <legend>Disponibilidade</legend>
          <p>O catálogo público mostra equipamentos ativos e operacionais.</p>
          <label className="directory-choice"><input type="checkbox" name="ativo" defaultChecked={item?.ativo ?? true} /> Ativo</label>
          <label className="directory-choice"><input type="checkbox" name="operacional" defaultChecked={item?.operacional ?? true} /> Operacional</label>
        </fieldset>
        <fieldset className="directory-group">
          <legend>Imagem</legend>
          <label className="ac-field">Foto (JPG ou PNG)
            <input type="file" accept="image/jpeg,image/png" aria-describedby="equipment-image-limit" onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
              setRemoveImage(false);
            }} />
          </label>
          <small id="equipment-image-limit">Opcional. Até 4 MB e 2048 px de cada lado.</small>
          {item && !file && !removeImage && <EquipmentPhoto item={item} />}
          {item?.imagem_url && !file && <label className="directory-choice">
            <input type="checkbox" checked={removeImage} onChange={(event) => setRemoveImage(event.target.checked)} />
            Remover foto atual
          </label>}
        </fieldset>
      </fieldset>
      {error && <StatusMessage state="error" title={error} />}
      <div className="directory-actions">
        <Button type="submit" pending={busy} pendingLabel="Salvando…">Salvar equipamento</Button>
        <Button variant="secondary" disabled={busy} onClick={close}>Voltar ao inventário</Button>
      </div>
    </form>
  );
}

export function EquipmentInventoryPage({ csrf }: { csrf: string }) {
  const { page, error, reload } = useEquipmentPage(equipmentInventory);
  const [editing, setEditing] = useState<InventoryItem | "new" | null>(null);
  const [notice, setNotice] = useState("");
  const heading = useDirectoryFocus(editing !== null);

  function edit(item: InventoryItem | "new") {
    setNotice("");
    setEditing(item);
  }

  function close() {
    setEditing(null);
    reload();
  }

  return (
    <section className="directory" aria-labelledby="equipment-admin-title">
      <h3 id="equipment-admin-title" ref={heading} tabIndex={-1}>
        {editing === "new" ? "Novo equipamento" : editing ? "Editar " + editing.nome : "Gerenciar equipamentos"}
      </h3>
      {notice && <StatusMessage state="success" title={notice} />}
      {editing ? (
        <EquipmentForm key={editing === "new" ? "new" : editing.id} csrf={csrf}
          item={editing === "new" ? undefined : editing} close={close}
          onSave={() => { setEditing(null); reload(1); setNotice("Equipamento salvo."); }} />
      ) : (
        <>
          <div className="directory-actions"><Button onClick={() => edit("new")}>Cadastrar equipamento</Button></div>
          {page ? (
            <>
              {page.itens.length ? (
                <ul className="directory-cards" aria-label="Equipamentos cadastrados">
                  {page.itens.map((item) => (
                    <li key={item.id} className="directory-card">
                      <h4>{item.nome}</h4>
                      <EquipmentPhoto item={item} />
                      {item.categoria && <p className="directory-meta">{item.categoria}</p>}
                      <DirectoryTag tone={item.ativo && item.operacional ? "positive" : "attention"}>
                        {item.ativo ? "Ativo" : "Inativo"} · {item.operacional ? "Operacional" : "Indisponível"}
                      </DirectoryTag>
                      <div className="directory-actions"><Button variant="secondary" aria-label={"Editar " + item.nome} onClick={() => edit(item)}>Editar</Button></div>
                    </li>
                  ))}
                </ul>
              ) : <StatusMessage state="empty" title="Nenhum equipamento cadastrado nesta página." />}
              <DirectoryPager page={page} label="Páginas do inventário" changePage={reload} />
            </>
          ) : error ? (
            <>
              <StatusMessage state="error" title="Não foi possível consultar o inventário." />
              <Button variant="secondary" onClick={() => reload()}>Tentar novamente</Button>
            </>
          ) : <StatusMessage state="loading" title="Carregando inventário…" />}
        </>
      )}
    </section>
  );
}
