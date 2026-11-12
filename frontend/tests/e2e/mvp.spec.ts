import { randomUUID } from "node:crypto";
import { expect, test } from "@playwright/test";
import { completeOnboarding, firstAccess, fixture, generate, mailLink, manualEditor,
  mutate, origin, password, publishManual, review, session, signIn, signOut } from "./helpers";

test.beforeEach(async ({ browser }, info) => {
  info.annotations.push({ type: "navegador", description: browser.version() });
});

test.afterEach(async ({ browser }, info) => {
  if (info.status === "passed") for (const context of browser.contexts()) await context.close();
});

test("E2E-01 cadastro, primeiro acesso, convite, onboarding e ficha manual", async ({ page, browser }) => {
  test.setTimeout(180_000);
  const staffEmail = "e2e-jornada-instrutor-" + fixture.sufixo + "@example.test";
  const clientEmail = "e2e-jornada-cliente-" + fixture.sufixo + "@example.test";
  await signIn(page, fixture.usuarios.admin.email);
  await page.goto("/area/administracao/funcionarios");
  await page.getByRole("button", { name: "Cadastrar funcionário", exact: true }).click();
  await page.getByLabel("Nome", { exact: true }).fill("Instrutor Jornada");
  await page.getByLabel("Cargo", { exact: true }).fill("Instrutor");
  await page.getByLabel("Data de admissão").fill("2026-01-01");
  await page.getByLabel("E-mail", { exact: true }).fill(staffEmail);
  await page.getByRole("checkbox", { name: "Instrutor", exact: true }).check();
  await page.getByRole("button", { name: "Salvar cadastro", exact: true }).click();
  await expect(page.getByText("Funcionário cadastrado.", { exact: true })).toBeVisible();
  const instructor = await browser.newPage({ baseURL: origin });
  await firstAccess(instructor, staffEmail);
  await signIn(instructor, staffEmail);
  const instructorId = (await session(instructor)).user_id;

  await page.goto("/area/administracao/clientes");
  await page.getByRole("button", { name: "Cadastrar cliente", exact: true }).click();
  await page.getByLabel("Nome", { exact: true }).fill("Cliente Jornada");
  await page.getByLabel("Data de nascimento").fill("1995-06-15");
  await page.getByLabel("E-mail", { exact: true }).fill(clientEmail);
  const created = page.waitForResponse(r => r.url().endsWith("/api/v1/clientes") && r.request().method() === "POST");
  await page.getByRole("button", { name: "Salvar cadastro", exact: true }).click();
  const client = await (await created).json() as { id: string };
  await expect(page.getByText("Cliente cadastrado.", { exact: true })).toBeVisible();
  const clientPage = await browser.newPage({ baseURL: origin });
  await firstAccess(clientPage, clientEmail);

  await page.goto("/area/administracao/designacoes?cliente=" + client.id);
  await page.getByRole("radio", { name: /Instrutor Jornada/ }).check();
  await page.getByRole("button", { name: "Salvar designação", exact: true }).click();
  await expect(page.getByText("Designação salva.", { exact: true })).toBeVisible();
  const invitation = await mutate(page, "/v1/onboarding/clientes/" + client.id + "/convite", { solicitacao_id: randomUUID() });
  expect(invitation.status()).toBe(201);
  await clientPage.goto(await mailLink(clientEmail, "/onboarding/convite"));
  await clientPage.getByRole("button", { name: "Abrir formulário", exact: true }).click();
  await completeOnboarding(clientPage);
  await expect(clientPage.getByText(/Onboarding concluído/)).toBeVisible();
  expect((await clientPage.request.get("/api/v1/auth/session")).status()).toBe(401);
  await signIn(clientPage, clientEmail);
  await clientPage.goto("/area/cliente/onboarding");
  await expect(clientPage.getByText(/Versão 1 concluída/)).toBeVisible();
  await page.goto("/area/administracao/equipamentos");
  await page.getByRole("button", { name: "Cadastrar equipamento", exact: true }).click();
  await page.getByLabel("Nome", { exact: true }).fill("Halteres Jornada");
  await page.getByRole("button", { name: "Salvar equipamento", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Halteres Jornada", exact: true })).toBeVisible();
  await page.goto("/area/administracao/exercicios");
  await page.getByRole("button", { name: "Cadastrar exercício", exact: true }).click();
  await page.getByLabel("Nome", { exact: true }).fill("Rosca Jornada");
  await page.getByLabel("Descrição do movimento").fill("Flexão de cotovelos com halteres; fixture E2E.");
  await page.getByLabel("Grupo muscular").fill("Bíceps");
  await page.getByRole("button", { name: "Adicionar alternativa", exact: true }).click();
  await page.getByRole("checkbox", { name: "Halteres Jornada", exact: true }).check();
  await page.getByRole("button", { name: "Salvar exercício", exact: true }).click();
  await expect(page.getByText("Exercício salvo.", { exact: true })).toBeVisible();
  await instructor.goto("/area/instrutor/clientes/" + client.id + "/avaliacoes");
  await instructor.getByLabel("Observação da avaliação").fill("Avaliação sintética de rotina.");
  await instructor.getByRole("button", { name: "Registrar avaliação", exact: true }).click();
  await expect(instructor.getByText("Avaliação registrada.", { exact: true })).toBeVisible();
  await manualEditor(instructor, client.id, "Rosca Jornada");
  const published = await publishManual(instructor);
  expect(published.treino.ficha.autor_id).toBe(instructorId);
  expect(published.treino.parecer.estado).toBe("PENDENTE");
  await clientPage.setViewportSize({ width: 390, height: 844 });
  await clientPage.goto("/area/cliente/treinos");
  await expect(clientPage.getByText("Rosca Jornada", { exact: true })).toBeVisible();
  await expect(clientPage.getByText(/Parecer.*Pendente/)).toBeVisible();
  expect(await clientPage.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await clientPage.screenshot({ path: process.env.ACADEMIA_E2E_OUTPUT + "/mvp-celular.png", fullPage: true });
  const download = clientPage.waitForEvent("download");
  await clientPage.getByRole("button", { name: "Exportar ficha em JSON", exact: true }).click();
  expect((await download).suggestedFilename()).toMatch(/\.json$/);
  await instructor.goto("/area/instrutor/revisoes");
  await expect(instructor.getByRole("link", { name: /Cliente Jornada.*Versão 1/ })).toBeVisible();
  await review(instructor, client.id, published.treino.ficha.id, "REJEITADO");
  await clientPage.reload();
  await expect(clientPage.getByText("Rosca Jornada", { exact: true })).toBeVisible();
  await expect(clientPage.getByText(/Parecer.*Rejeitado/)).toBeVisible();
  await signOut(clientPage); await signIn(clientPage, clientEmail);
  await clientPage.goto("/area/cliente/treinos");
  await expect(clientPage.getByText("Rosca Jornada", { exact: true })).toBeVisible();
});

test("E2E-02 sessão de dois clientes, CSRF e resposta maliciosa inerte", async ({ page, browser }) => {
  await signIn(page, fixture.usuarios.seguranca.email);
  await page.goto("/area/cliente/assistente");
  let dialogs = 0, attackRequests = 0;
  page.on("dialog", dialog => { dialogs++; void dialog.dismiss(); });
  page.on("request", req => { if (req.url().includes("e2e-ataque")) attackRequests++; });
  await page.getByLabel("Mensagem", { exact: true }).fill("E2E_RENDERIZACAO");
  const answered = page.waitForResponse(r => r.url().endsWith("/api/v1/ia/chat") && r.request().method() === "POST");
  await page.getByRole("button", { name: "Enviar dúvida", exact: true }).click();
  const turn = await (await answered).json() as { solicitacao_id: string };
  await expect(page.getByText(/<script>window.__e2eExecutou=true<\/script>/)).toBeVisible();
  await expect(page.locator(".chat-text script, .chat-text img, .chat-text a")).toHaveCount(0);
  expect(await page.evaluate(() => Object.hasOwn(window, "__e2eExecutou"))).toBe(false);
  expect(dialogs).toBe(0); expect(attackRequests).toBe(0);
  const badCsrf = await page.request.post("/api/v1/ia/chat", { headers: { Origin: origin },
    data: { solicitacao_id: randomUUID(), mensagem: "Sem CSRF", finalidade: "DUVIDA" } });
  expect(badCsrf.status()).toBe(403);
  const aSession = await session(page);
  const other = await browser.newPage({ baseURL: origin }); await signIn(other, fixture.usuarios.sem_onboarding.email);
  expect((await other.request.get("/api/v1/ia/chat/" + turn.solicitacao_id)).status()).toBe(404);
  expect((await other.request.get("/api/v1/onboarding/meu/versoes/" + fixture.usuarios.seguranca.onboarding_id)).status()).toBe(404);
  expect((await other.request.get("/api/v1/clientes")).status()).toBe(403);
  await signOut(page); await signIn(page, fixture.usuarios.sem_onboarding.email);
  await page.goto("/area/cliente/assistente");
  await expect(page.getByText(/E2E_MARCADOR_PRIVADO/)).toHaveCount(0);
  const oldCsrf = await page.request.post("/api/v1/ia/chat", { headers: { Origin: origin, "X-CSRF-Token": aSession.csrf_token },
    data: { solicitacao_id: randomUUID(), mensagem: "Token da outra sessão", finalidade: "DUVIDA" } });
  expect(oldCsrf.status()).toBe(403);
  await page.getByLabel("Mensagem", { exact: true }).fill("O que é cadência?");
  await page.getByRole("button", { name: "Enviar dúvida", exact: true }).click();
  await expect(page.getByText("Resposta sintética de teste: cadência é o tempo de uma repetição.", { exact: true })).toBeVisible();
});

test("E2E-03 triagem grave, NAO_SEI e onboarding ausente", async ({ browser }) => {
  for (const [name, expected] of [["grave", "BLOQUEADA"], ["nao_sei", "DADOS_INSUFICIENTES"], ["sem_onboarding", "DADOS_INSUFICIENTES"]]) {
    const page = await browser.newPage({ baseURL: origin }); await signIn(page, fixture.usuarios[name].email);
    const receipt = await generate(page);
    expect(receipt.estado).toBe(expected); expect(receipt.versao_publicada_id).toBeNull();
    await expect(page.getByText(/Não foi publicada uma nova ficha/)).toBeVisible();
  }
  const page = await browser.newPage({ baseURL: origin }); await signIn(page, fixture.usuarios.sem_instrutor.email);
  const receipt = await generate(page); expect(receipt.estado).toBe("PUBLICADA");
  await expect(page.getByRole("article", { name: "Ficha gerada" })).toBeVisible();
  await page.goto("/area/cliente/assistente");
  await page.getByLabel("Mensagem", { exact: true }).fill("Posso tirar uma dúvida sem parecer?");
  await page.getByRole("button", { name: "Enviar dúvida", exact: true }).click();
  await expect(page.getByText("Resposta sintética de teste: cadência é o tempo de uma repetição.", { exact: true })).toBeVisible();
});

test("E2E-04 geração única, confirmação do onboarding e adaptação versionada", async ({ page, browser }) => {
  const client = fixture.usuarios.adaptacao;
  const coach = await browser.newPage({ baseURL: origin });
  await signIn(coach, fixture.usuarios.instrutor.email);
  const noticeIds = async () => (await (await coach.request.get("/api/v1/notificacoes/pendentes")).json() as { id: string }[]).map(v => v.id).sort();
  const noticesBefore = await noticeIds();
  await signIn(page, client.email);
  const first = await generate(page); expect(first.estado).toBe("PUBLICADA");
  const noticesAfter = await noticeIds();
  expect(noticesAfter.filter(id => !noticesBefore.includes(id))).toHaveLength(1);
  const replay = await mutate(page, "/v1/ia/fichas/execucoes", { solicitacao_id: first.solicitacao_id });
  expect((await replay.json()).versao_publicada_id).toBe(first.versao_publicada_id);
  await page.reload(); await page.getByRole("button", { name: "Consultar estado salvo", exact: true }).click();
  await expect(page.getByText("Versão 1 · Vigente", { exact: true })).toBeVisible();
  expect(await noticeIds()).toEqual(noticesAfter);
  await page.goto("/area/cliente/onboarding");
  await page.getByRole("button", { name: "Atualizar meus dados", exact: true }).click();
  await page.getByLabel("Tempo por sessão (minutos)").fill("45");
  await page.getByRole("button", { name: "Revisar atualização", exact: true }).click();
  await expect(page.getByRole("region", { name: "Confirmar atualização" })).toBeVisible();
  await page.getByRole("button", { name: "Confirmar nova versão", exact: true }).click();
  await expect(page.getByText(/Versão 2 concluída/)).toBeVisible();
  const before = await (await page.request.get("/api/v1/treinos/clientes/" + client.id + "/publicadas/" + first.versao_publicada_id + "/ficha")).json();
  await page.goto("/area/cliente/assistente");
  await page.getByLabel("Objetivo", { exact: true }).selectOption("ADAPTACAO");
  await expect(page.getByRole("button", { name: "Solicitar adaptação", exact: true })).toBeDisabled();
  await page.getByLabel("Conferi e confirmei no onboarding os dados relevantes para esta adaptação").check();
  await page.getByLabel("Mensagem", { exact: true }).fill("Ajustar somente o primeiro dia, contexto já confirmado.");
  const adapted = page.waitForResponse(r => r.url().endsWith("/api/v1/ia/chat") && r.request().method() === "POST");
  await page.getByRole("button", { name: "Solicitar adaptação", exact: true }).click();
  const result = await (await adapted).json(); expect(result.estado).toBe("PUBLICADA");
  await page.getByRole("button", { name: "Comparar versões", exact: true }).click();
  await expect(page.getByRole("region", { name: "Diferenças da adaptação" })).toBeVisible();
  const after = await (await page.request.get("/api/v1/treinos/clientes/" + client.id + "/publicadas/" + result.versao_publicada_id + "/ficha")).json();
  expect(after.ficha.numero).toBe(2); expect(after.parecer.estado).toBe("PENDENTE");
  expect(after.ficha.dias[1]).toEqual(before.ficha.dias[1]);
  expect(after.ficha.dias[0].itens[0].series).toBe(before.ficha.dias[0].itens[0].series + 1);
  const outsider = await browser.newPage({ baseURL: origin }); await signIn(outsider, fixture.usuarios.instrutor_alheio.email);
  expect((await outsider.request.get("/api/v1/treinos/clientes/" + client.id + "/versoes/" + result.versao_publicada_id + "/revisao")).status()).toBe(403);
});

test("E2E-05 retenção de 16 versões, rejeição e exportação", async ({ page, browser }) => {
  const client = fixture.usuarios.retencao;
  await signIn(page, fixture.usuarios.instrutor.email);
  const versions: string[] = [];
  for (let index = 0; index < 16; index++) {
    const data = { solicitacao_id: randomUUID(), versao_base_id: versions.at(-1) ?? null,
      onboarding_id: client.onboarding_id, dias: [{ titulo: "Dia de retenção", itens: [{
        exercicio_id: fixture.usuarios.exercicio.id, equipamento_ids: [], series: 2,
        repeticoes: "8-12", intervalo_segundos: 60 }] }] };
    const draftResponse = await mutate(page, "/v1/treinos/clientes/" + client.id + "/rascunhos", data);
    expect(draftResponse.status()).toBe(201); const draft = await draftResponse.json();
    const published = await mutate(page, "/v1/treinos/clientes/" + client.id + "/versoes/" + draft.id + "/publicacao", {
      solicitacao_id: randomUUID(), revisao: draft.revisao, onboarding_id: client.onboarding_id,
      versao_base_id: data.versao_base_id, restricoes_conferidas: true });
    expect(published.status()).toBe(200); versions.push(draft.id);
  }
  const clientPage = await browser.newPage({ baseURL: origin }); await signIn(clientPage, client.email);
  await clientPage.goto("/area/cliente/treinos");
  await expect(clientPage.getByLabel("Versão da ficha").locator("option")).toHaveCount(15);
  await expect(clientPage.getByText("Versão 16 · Vigente", { exact: true })).toBeVisible();
  for (const suffix of ["/ficha", "/exportacao"]) {
    expect((await clientPage.request.get("/api/v1/treinos/clientes/" + client.id + "/publicadas/" + versions[0] + suffix)).status()).toBe(404);
  }
  await review(page, client.id, versions[14], "REJEITADO");
  await clientPage.reload(); await expect(clientPage.getByLabel("Versão da ficha").locator("option")).toHaveCount(15);
  await review(page, client.id, versions[15], "REJEITADO");
  await clientPage.reload(); await expect(clientPage.getByLabel("Versão da ficha").locator("option")).toHaveCount(14);
  await expect(clientPage.getByText(/Parecer.*Rejeitado/)).toBeVisible();
  expect((await clientPage.request.get("/api/v1/treinos/clientes/" + client.id + "/publicadas/" + versions[14] + "/exportacao")).status()).toBe(404);
});

test("E2E-06 equipamento muda durante a publicação e API recusa", async ({ page, browser }) => {
  await signIn(page, fixture.usuarios.admin.email);
  const equipmentResponse = await mutate(page, "/v1/admin/equipamentos", { solicitacao_id: randomUUID(), nome: "Equipamento de revalidação", ativo: true, operacional: true });
  expect(equipmentResponse.status()).toBe(201); const equipment = await equipmentResponse.json();
  const exerciseResponse = await mutate(page, "/v1/exercicios", { nome: "Exercício de revalidação", descricao: "Fixture dependente do equipamento.", grupo_muscular: "Geral", ativo: true, dispensa_equipamento: false, combinacoes: [[equipment.id]] });
  expect(exerciseResponse.status()).toBe(201);
  const instructor = await browser.newPage({ baseURL: origin }); await signIn(instructor, fixture.usuarios.instrutor.email);
  await manualEditor(instructor, fixture.usuarios.equipamentos.id, "Exercício de revalidação");
  const changed = await mutate(page, "/v1/admin/equipamentos/" + equipment.id, { nome: equipment.nome,
    ativo: true, operacional: false, revisao: equipment.revisao }, "PUT");
  expect(changed.status()).toBe(200);
  const refused = instructor.waitForResponse(r => r.url().endsWith("/publicacao") && r.request().method() === "POST");
  await instructor.getByRole("button", { name: "Publicar versão salva", exact: true }).click();
  expect((await refused).status()).toBe(409);
  await expect(instructor.getByRole("alert").filter({ hasText: /recursos mudaram/ })).toBeVisible();
  const denied = await mutate(instructor, "/v1/admin/equipamentos/" + equipment.id,
    { nome: equipment.nome, ativo: true, operacional: true, revisao: 2 }, "PUT");
  expect(denied.status()).toBe(403);
});

test("E2E-07 treino manual continua após indisponibilidade da IA", async ({ page, browser }) => {
  const client = fixture.usuarios.manual;
  await signIn(page, client.email); await page.goto("/area/cliente/assistente");
  await page.getByLabel("Mensagem", { exact: true }).fill("Dúvida durante indisponibilidade.");
  await page.getByRole("button", { name: "Enviar dúvida", exact: true }).click();
  await expect(page.getByText("O serviço não conseguiu concluir a resposta", { exact: true })).toBeVisible();
  const instructor = await browser.newPage({ baseURL: origin }); await signIn(instructor, fixture.usuarios.instrutor.email);
  await manualEditor(instructor, client.id); await publishManual(instructor);
  await page.goto("/area/cliente/treinos");
  await expect(page.getByText("Agachamento E2E", { exact: true })).toBeVisible();
  await signOut(page); await signIn(page, client.email); await page.goto("/area/cliente/treinos");
  await expect(page.getByText("Agachamento E2E", { exact: true })).toBeVisible();
});

test("E2E-08 recuperação e perfis de cliente/funcionário independentes", async ({ page, browser }) => {
  const staff = fixture.usuarios.atendente;
  await signIn(page, fixture.usuarios.admin.email);
  const client = await mutate(page, "/v1/clientes", { nome: "Atendente com perfil cliente",
    data_nascimento: "1990-01-01", email: staff.email, vincular_existente: true });
  expect(client.status()).toBe(201); const profile = await client.json();
  const staffPage = await browser.newPage({ baseURL: origin }); await signIn(staffPage, staff.email);
  expect((await session(staffPage)).roles).toEqual(expect.arrayContaining(["CLIENTE", "ATENDENTE"]));
  const inactive = await mutate(page, "/v1/clientes/" + staff.id, { nome: profile.nome,
    data_nascimento: profile.data_nascimento, revisao: profile.revisao, ativo: false }, "PUT");
  expect(inactive.status()).toBe(200);
  expect((await staffPage.request.get("/api/v1/clientes")).status()).toBe(200);
  expect((await staffPage.request.get("/api/v1/onboarding/meu")).status()).toBe(403);
  const recovering = await browser.newPage({ baseURL: origin });
  await recovering.goto("/recuperar-acesso");
  await recovering.getByLabel("E-mail", { exact: true }).fill(staff.email);
  await recovering.getByRole("button", { name: "Solicitar recuperação", exact: true }).click();
  await expect(recovering.getByText(/Se o e-mail estiver elegível/)).toBeVisible();
  const link = await mailLink(staff.email, "/redefinir-senha");
  await recovering.goto(link);
  await recovering.getByLabel("Nova senha", { exact: true }).fill(password + "-nova");
  await recovering.getByLabel("Confirme a nova senha").fill(password + "-nova");
  await recovering.getByRole("button", { name: "Redefinir senha", exact: true }).click();
  await expect(recovering.getByText("Senha redefinida. Entre com a nova senha.", { exact: true })).toBeVisible();
  expect((await staffPage.request.get("/api/v1/auth/session")).status()).toBe(401);
  await signIn(recovering, staff.email, password + "-nova");
  await expect(recovering.getByRole("heading", { name: "Área de atendimento", exact: true })).toBeVisible();
});
