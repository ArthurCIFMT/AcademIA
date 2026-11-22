import { useEffect, useRef, useState, type FormEvent } from "react";

import { ApiError } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { DirectoryPager, DirectoryTag, useDirectoryFocus } from "../clients/directory-ui";
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
  const saving = useRef(false);

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
    if (saving.current) return;
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
    saving.current = true;
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
      saving.current = false;
      setBusy(false);
    }
  }

  return (
    <form className="directory-form" onSubmit={(event) => void submit(event)}>
      <fieldset className="directory-fieldset" disabled={busy}>
        <fieldset className="directory-group">
          <legend>Dados do exercício</legend>
          <label className="ac-field">Nome<input name="nome" required maxLength={120} defaultValue={exercise?.nome} /></label>
          <label className="ac-field">Descrição do movimento
            <textarea name="descricao" required maxLength={2000} defaultValue={exercise?.descricao} />
          </label>
          <label className="ac-field">Grupo muscular<input name="grupo_muscular" required maxLength={80} defaultValue={exercise?.grupo_muscular} /></label>
          <label className="directory-choice"><input type="checkbox" name="ativo" defaultChecked={exercise?.ativo ?? true} /> Ativo</label>
        </fieldset>
        <fieldset className="directory-group">
          <legend>Recursos necessários</legend>
          <label className="directory-choice"><input type="checkbox" checked={bodyweight}
            onChange={(event) => setBodyweight(event.target.checked)} /> Dispensa equipamento</label>
          {bodyweight && groups.length > 0 && <p>Salvar com dispensa remove as combinações anteriores.</p>}
          {!bodyweight && (
            <>
              {groups.length === 0
                ? <p>O exercício fica fora da seleção até receber uma alternativa ou uma dispensa.</p>
                : <p>Marque os equipamentos usados juntos em cada alternativa. Para um exercício ativo, basta uma alternativa completa disponível.</p>}
              {resourceError ? (
                <div>
                  <StatusMessage state="error" title="Não foi possível consultar os equipamentos." />
                  <Button variant="secondary" onClick={() => {
                    setResourceError(false);
                    setAttempt(value => value + 1);
                  }}>Tentar novamente</Button>
                </div>
              ) : options === null && <p role="status">Carregando equipamentos…</p>}
              {groups.map((group, index) => (
                <fieldset className="directory-group exercise-combination" key={index}>
                  <legend>Alternativa {index + 1}</legend>
                  {[...resources.values()].map(resource => (
                    <label className="directory-choice" key={resource.id}>
                      <input type="checkbox" checked={group.includes(resource.id)}
                        disabled={!group.includes(resource.id) && group.length >= 20}
                        onChange={() => toggle(index, resource.id)} />
                      {resource.nome}{resource.disponivel ? "" : " (indisponível)"}
                    </label>
                  ))}
                  <Button variant="secondary" onClick={() => setGroups(groups.filter((_, position) => position !== index))}>
                    Remover alternativa {index + 1}
                  </Button>
                </fieldset>
              ))}
              <Button variant="secondary" disabled={!resources.size || groups.length >= 10}
                onClick={() => setGroups([...groups, []])}>Adicionar alternativa</Button>
            </>
          )}
        </fieldset>
      </fieldset>
      {error && <StatusMessage state="error" title={error} />}
      <div className="directory-actions">
        <Button type="submit" pending={busy} pendingLabel="Salvando…">Salvar exercício</Button>
        <Button variant="secondary" disabled={busy} onClick={close}>Voltar ao catálogo</Button>
      </div>
    </form>
  );
}

function ExerciseResources({ exercise }: { exercise: Exercise }) {
  if (exercise.dispensa_equipamento) return <p>Dispensa equipamento</p>;
  if (!exercise.combinacoes.length) return <p>Sem alternativa de equipamentos cadastrada</p>;
  return <details className="directory-help">
    <summary>Alternativas de equipamentos ({exercise.combinacoes.length})</summary>
    <ol>{exercise.combinacoes.map((group, index) => <li key={index}>
      {group.map(resource => resource.nome + (resource.disponivel ? "" : " (indisponível)")).join(" + ")}
    </li>)}</ol>
  </details>;
}

export function ExerciseCatalog({ csrf }: { csrf: string }) {
  const [query, setQuery] = useState({ page: 1 });
  const [result, setResult] = useState<ExercisePage | null>(null);
  const [error, setError] = useState(false);
  const [editor, setEditor] = useState<Exercise | "new" | null>(null);
  const [notice, setNotice] = useState("");
  const heading = useDirectoryFocus(editor !== null);

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
    <section className="directory" aria-labelledby="exercise-title">
      <h3 id="exercise-title" ref={heading} tabIndex={-1}>
        {editor === "new" ? "Novo exercício" : editor ? "Editar " + editor.nome : "Catálogo de exercícios"}
      </h3>
      {notice && <StatusMessage state="success" title={notice} />}
      {editor ? (
        <ExerciseForm key={editor === "new" ? editor : editor.id} csrf={csrf}
          exercise={editor === "new" ? undefined : editor}
          close={() => { setEditor(null); load(query.page); }}
          saved={() => { setEditor(null); setNotice("Exercício salvo."); load(query.page); }} />
      ) : (
        <>
          <div className="directory-actions"><Button onClick={() => edit("new")}>Cadastrar exercício</Button></div>
          {result ? (
            <>
              {result.itens.length ? (
                <ul className="directory-cards" aria-label="Exercícios cadastrados">
                  {result.itens.map((item) => (
                    <li key={item.id} className="directory-card">
                      <h4>{item.nome}</h4>
                      <p className="directory-meta">{item.grupo_muscular}</p>
                      <DirectoryTag tone={item.elegivel ? "positive" : "attention"}>
                        {item.elegivel ? "Disponível para seleção" : item.ativo ? "Recursos indisponíveis ou pendentes" : "Inativo"}
                      </DirectoryTag>
                      <p>{item.descricao}</p>
                      <ExerciseResources exercise={item} />
                      <div className="directory-actions"><Button variant="secondary" aria-label={"Editar " + item.nome} onClick={() => edit(item)}>Editar</Button></div>
                    </li>
                  ))}
                </ul>
              ) : <StatusMessage state="empty" title="Nenhum exercício cadastrado nesta página." />}
              <DirectoryPager page={result} label="Páginas do catálogo" changePage={load} />
            </>
          ) : error ? (
            <>
              <StatusMessage state="error" title="Não foi possível carregar o catálogo." />
              <Button variant="secondary" onClick={() => load(query.page)}>Tentar novamente</Button>
            </>
          ) : <StatusMessage state="loading" title="Carregando catálogo…" />}
        </>
      )}
    </section>
  );
}
