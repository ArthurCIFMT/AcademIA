import { useEffect, useState, type FormEvent } from "react";

import { ApiError } from "../../lib/api/auth";
import { exercisePage, exerciseResources, saveExercise, type Exercise,
  type ExerciseFields, type ExercisePage, type Resource } from "./api";
import "./exercises.css";

function ExerciseForm({ exercise, csrf, close, saved }: {
  exercise?: Exercise;
  csrf: string;
  close: () => void;
  saved: () => void;
}) {
  const [groups, setGroups] = useState(() => exercise?.combinacoes.map((group) => group.map(({ id }) => id)) ?? []);
  const [bodyweight, setBodyweight] = useState(exercise?.dispensa_equipamento ?? false);
  const [options, setOptions] = useState<Resource[] | null>(null);
  const [resourceError, setResourceError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    void exerciseResources(controller.signal).then(
      (result) => { if (!controller.signal.aborted) setOptions(result); },
      () => { if (!controller.signal.aborted) setResourceError(true); },
    );
    return () => controller.abort();
  }, [attempt]);

  const resources = new Map(exercise?.combinacoes.flat().map((option) => [option.id, option]));
  for (const option of options ?? []) resources.set(option.id, option);

  function toggle(index: number, id: string) {
    setGroups((current) => current.map((group, position) => {
      if (position !== index) return group;
      return group.includes(id) ? group.filter((resource) => resource !== id) : [...group, id];
    }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const values = new FormData(event.currentTarget);
    const data: ExerciseFields = {
      nome: String(values.get("nome")).trim(),
      descricao: String(values.get("descricao")).trim(),
      grupo_muscular: String(values.get("grupo_muscular")).trim(),
      ativo: values.has("ativo"),
      dispensa_equipamento: bodyweight,
      combinacoes: bodyweight ? [] : groups,
    };
    if (!data.nome || !data.descricao || !data.grupo_muscular) {
      setError("Preencha nome, descrição e grupo muscular.");
      return;
    }
    if (data.combinacoes.some((group) => !group.length)) {
      setError("Selecione os equipamentos de cada alternativa ou remova a alternativa vazia.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await saveExercise(data, csrf, exercise);
      saved();
    } catch (failure) {
      const status = failure instanceof ApiError ? failure.status : 0;
      if (status === 409) setError(exercise
        ? "O nome já existe ou o cadastro mudou. Confira o catálogo antes de tentar novamente."
        : "Já existe um exercício com esse nome, inclusive se estiver inativo.");
      else if (status === 422) setError("Confira os campos e use combinações distintas de equipamentos cadastrados.");
      else if (status === 401 || status === 403) setError("Sua sessão perdeu a permissão para salvar exercícios.");
      else setError("Não foi possível confirmar o salvamento. Os dados continuam nesta tela.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="exercise-form" onSubmit={(event) => void submit(event)}>
      <fieldset disabled={busy}>
        <legend>{exercise ? "Editar exercício" : "Novo exercício"}</legend>
        <label htmlFor="exercise-name">Nome</label>
        <input id="exercise-name" name="nome" required maxLength={120} defaultValue={exercise?.nome} />
        <label htmlFor="exercise-description">Descrição do movimento</label>
        <textarea id="exercise-description" name="descricao" required maxLength={2000} defaultValue={exercise?.descricao} />
        <label htmlFor="exercise-muscle">Grupo muscular</label>
        <input id="exercise-muscle" name="grupo_muscular" required maxLength={80} defaultValue={exercise?.grupo_muscular} />
        <label><input type="checkbox" name="ativo" defaultChecked={exercise?.ativo ?? true} /> Ativo</label>
        <label><input type="checkbox" checked={bodyweight}
          onChange={(event) => setBodyweight(event.target.checked)} /> Dispensa equipamento</label>
        {bodyweight && groups.length > 0 && <p>Salvar com dispensa remove as combinações anteriores.</p>}
        {!bodyweight && (
          <>
            {groups.length === 0 && <p>O exercício fica fora da seleção até receber uma alternativa ou uma dispensa.</p>}
            {resourceError ? (
              <div>
                <p role="alert">Não foi possível consultar os equipamentos.</p>
                <button type="button" onClick={() => {
                  setResourceError(false);
                  setAttempt((value) => value + 1);
                }}>Tentar novamente</button>
              </div>
            ) : options === null && <p role="status">Carregando equipamentos…</p>}
            {groups.map((group, index) => (
              <fieldset className="exercise-combination" key={index}>
                <legend>Alternativa {index + 1}</legend>
                {[...resources.values()].map((resource) => (
                  <label key={resource.id}>
                    <input type="checkbox" checked={group.includes(resource.id)}
                      disabled={!group.includes(resource.id) && group.length >= 20}
                      onChange={() => toggle(index, resource.id)} />
                    {resource.nome}{resource.disponivel ? "" : " (indisponível)"}
                  </label>
                ))}
                <button type="button" onClick={() => setGroups(groups.filter((_, position) => position !== index))}>
                  Remover alternativa {index + 1}
                </button>
              </fieldset>
            ))}
            <button type="button" disabled={!resources.size || groups.length >= 10}
              onClick={() => setGroups([...groups, []])}>Adicionar alternativa</button>
          </>
        )}
      </fieldset>
      {error && <p role="alert">{error}</p>}
      <div className="exercise-actions">
        <button type="submit" disabled={busy}>{busy ? "Salvando…" : "Salvar exercício"}</button>
        <button type="button" disabled={busy} onClick={close}>Voltar ao catálogo</button>
      </div>
    </form>
  );
}

export function ExerciseCatalog({ csrf }: { csrf: string }) {
  const [query, setQuery] = useState({ page: 1 });
  const [result, setResult] = useState<ExercisePage | null>(null);
  const [error, setError] = useState(false);
  const [editor, setEditor] = useState<Exercise | "new" | null>(null);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    void exercisePage(query.page, controller.signal).then(
      (data) => { if (!controller.signal.aborted) setResult(data); },
      () => { if (!controller.signal.aborted) setError(true); },
    );
    return () => controller.abort();
  }, [query]);

  function load(page: number) {
    setResult(null);
    setError(false);
    setQuery({ page });
  }

  function edit(value: Exercise | "new") {
    setNotice("");
    setEditor(value);
  }

  return (
    <section aria-labelledby="exercise-title">
      <h3 id="exercise-title">Catálogo de exercícios</h3>
      {notice && <p role="status">{notice}</p>}
      {editor ? (
        <ExerciseForm key={editor === "new" ? editor : editor.id} csrf={csrf}
          exercise={editor === "new" ? undefined : editor}
          close={() => { setEditor(null); load(query.page); }}
          saved={() => { setEditor(null); setNotice("Exercício salvo."); load(query.page); }} />
      ) : (
        <>
          <button type="button" onClick={() => edit("new")}>Cadastrar exercício</button>
          {result ? (
            <>
              {result.itens.length ? (
                <ul className="exercise-list">
                  {result.itens.map((item) => (
                    <li key={item.id}>
                      <h4>{item.nome}</h4>
                      <p>{item.grupo_muscular}</p>
                      <p>{item.descricao}</p>
                      <p>{item.elegivel ? "Disponível para seleção" : item.ativo ? "Recursos indisponíveis ou pendentes" : "Inativo"}</p>
                      <button type="button" aria-label={"Editar " + item.nome} onClick={() => edit(item)}>Editar</button>
                    </li>
                  ))}
                </ul>
              ) : <p>Nenhum exercício cadastrado nesta página.</p>}
              {(result.total > result.limite || result.pagina > 1) && (
                <nav className="exercise-actions" aria-label="Páginas do catálogo">
                  <button type="button" disabled={result.pagina <= 1}
                    onClick={() => load(result.pagina - 1)}>Anterior</button>
                  <button type="button" disabled={result.pagina * result.limite >= result.total}
                    onClick={() => load(result.pagina + 1)}>Próxima</button>
                </nav>
              )}
            </>
          ) : error ? (
            <>
              <p role="alert">Não foi possível carregar o catálogo.</p>
              <button type="button" onClick={() => load(query.page)}>Tentar novamente</button>
            </>
          ) : <p role="status">Carregando catálogo…</p>}
        </>
      )}
    </section>
  );
}
