"""Persist manual drafts and protect published workout content."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_avaliacao_cliente_snapshot_id",
        "avaliacao",
        ["cliente_id", "onboarding_id", "id"],
        schema="academia",
    )
    op.create_table(
        "versao_ficha",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("cliente_id", sa.Uuid(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("origem", sa.String(20), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=True),
        sa.Column("onboarding_id", sa.Uuid(), nullable=False),
        sa.Column("avaliacao_id", sa.Uuid(), nullable=True),
        sa.Column("versao_base_id", sa.Uuid(), nullable=True),
        sa.Column("estado_publicacao", sa.String(25), nullable=False),
        sa.Column("vigente", sa.Boolean(), nullable=False),
        sa.Column("publicada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("conteudo_excluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("motivo_exclusao", sa.String(40), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["academia.cliente.usuario_id"]),
        sa.ForeignKeyConstraint(["autor_id"], ["academia.usuario.id"]),
        sa.UniqueConstraint("cliente_id", "numero", name="uq_ficha_cliente_numero"),
        sa.UniqueConstraint("cliente_id", "id", name="uq_ficha_cliente_id"),
        sa.ForeignKeyConstraint(
            ["cliente_id", "onboarding_id"],
            ["academia.onboarding_versao.cliente_id", "academia.onboarding_versao.id"],
            name="fk_ficha_onboarding_cliente",
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id", "onboarding_id", "avaliacao_id"],
            [
                "academia.avaliacao.cliente_id",
                "academia.avaliacao.onboarding_id",
                "academia.avaliacao.id",
            ],
            name="fk_ficha_avaliacao_contexto",
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id", "versao_base_id"],
            ["academia.versao_ficha.cliente_id", "academia.versao_ficha.id"],
            name="fk_ficha_base_cliente",
        ),
        sa.CheckConstraint(
            "numero >= 1 AND revision >= 1 AND "
            "((origem = 'MANUAL' AND autor_id IS NOT NULL) OR origem = 'IA')",
            name="ck_ficha_identificacao",
        ),
        sa.CheckConstraint(
            "(estado_publicacao = 'RASCUNHO' AND NOT vigente AND publicada_em IS NULL "
            "AND conteudo_excluido_em IS NULL AND motivo_exclusao IS NULL) OR "
            "(estado_publicacao IN ('PUBLICADO', 'SUBSTITUIDO') "
            "AND vigente = (estado_publicacao = 'PUBLICADO') "
            "AND publicada_em IS NOT NULL AND conteudo_excluido_em IS NULL "
            "AND motivo_exclusao IS NULL) OR "
            "(estado_publicacao = 'CONTEUDO_EXPIRADO' AND NOT vigente "
            "AND publicada_em IS NOT NULL AND conteudo_excluido_em IS NOT NULL "
            "AND motivo_exclusao IN ('LIMITE_15', 'REJEITADA_ANTERIOR'))",
            name="ck_ficha_publicacao",
        ),
        schema="academia",
    )
    op.create_index(
        "uq_ficha_vigente",
        "versao_ficha",
        ["cliente_id"],
        unique=True,
        postgresql_where=sa.text("vigente"),
        schema="academia",
    )
    op.create_table(
        "dia_ficha",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("versao_id", sa.Uuid(), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(60), nullable=False),
        sa.ForeignKeyConstraint(["versao_id"], ["academia.versao_ficha.id"]),
        sa.UniqueConstraint("versao_id", "ordem", name="uq_ficha_dia_ordem"),
        sa.CheckConstraint(
            "ordem >= 1 AND length(btrim(titulo)) > 0", name="ck_ficha_dia"
        ),
        schema="academia",
    )
    op.create_table(
        "item_ficha",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("dia_id", sa.Uuid(), nullable=False),
        sa.Column("exercicio_id", sa.Uuid(), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("series", sa.Integer(), nullable=False),
        sa.Column("repeticoes", sa.String(40), nullable=False),
        sa.Column("carga_kg", sa.Numeric(8, 2), nullable=True),
        sa.Column("intervalo_segundos", sa.Integer(), nullable=False),
        sa.Column("cadencia", sa.String(40), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("exercicio_snapshot", JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["dia_id"], ["academia.dia_ficha.id"]),
        sa.ForeignKeyConstraint(["exercicio_id"], ["academia.exercicio.id"]),
        sa.UniqueConstraint("dia_id", "ordem", name="uq_ficha_item_ordem"),
        sa.CheckConstraint(
            "ordem >= 1 AND series BETWEEN 1 AND 100 "
            "AND length(btrim(repeticoes)) > 0 "
            "AND intervalo_segundos BETWEEN 0 AND 3600 "
            "AND (carga_kg IS NULL OR carga_kg >= 0) "
            "AND jsonb_typeof(exercicio_snapshot) = 'object'",
            name="ck_ficha_item",
        ),
        schema="academia",
    )
    op.create_table(
        "parecer",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("versao_id", sa.Uuid(), nullable=False),
        sa.Column("instrutor_id", sa.Uuid(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["versao_id"], ["academia.versao_ficha.id"]),
        sa.ForeignKeyConstraint(["instrutor_id"], ["academia.funcionario.usuario_id"]),
        sa.CheckConstraint(
            "estado IN ('PENDENTE', 'ACEITO', 'REJEITADO')", name="ck_parecer_estado"
        ),
        schema="academia",
    )
    op.execute("""
        CREATE FUNCTION academia.proteger_metadados_ficha() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Metadados da ficha são preservados.'
                        USING ERRCODE = '55000';
            END IF;
            IF ROW(NEW.id, NEW.cliente_id, NEW.numero,
                   NEW.origem, NEW.autor_id, NEW.versao_base_id)
               IS DISTINCT FROM
               ROW(OLD.id, OLD.cliente_id, OLD.numero,
                   OLD.origem, OLD.autor_id, OLD.versao_base_id)
            THEN
                RAISE EXCEPTION 'Identificação da versão é imutável.'
                        USING ERRCODE = '55000';
            END IF;
            IF OLD.estado_publicacao = 'RASCUNHO'
               AND NEW.estado_publicacao NOT IN ('RASCUNHO', 'PUBLICADO') THEN
                RAISE EXCEPTION 'Transição de rascunho inválida.'
                        USING ERRCODE = '55000';
            END IF;
            IF OLD.estado_publicacao <> 'RASCUNHO' THEN
                IF ROW(NEW.onboarding_id, NEW.avaliacao_id,
                       NEW.publicada_em, NEW.revision)
                   IS DISTINCT FROM
                   ROW(OLD.onboarding_id, OLD.avaliacao_id,
                       OLD.publicada_em, OLD.revision)
                   OR NEW.estado_publicacao = 'RASCUNHO'
                   OR (OLD.estado_publicacao = 'SUBSTITUIDO'
                       AND NEW.estado_publicacao = 'PUBLICADO')
                   OR (OLD.vigente AND NEW.estado_publicacao = 'CONTEUDO_EXPIRADO')
                   OR (OLD.estado_publicacao = 'CONTEUDO_EXPIRADO'
                       AND NEW IS DISTINCT FROM OLD)
                THEN
                    RAISE EXCEPTION 'Versão publicada é imutável.'
                        USING ERRCODE = '55000';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER proteger_metadados_ficha BEFORE UPDATE OR DELETE
        ON academia.versao_ficha FOR EACH ROW
        EXECUTE FUNCTION academia.proteger_metadados_ficha()
    """)
    op.execute("""
        CREATE FUNCTION academia.proteger_conteudo_ficha() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE versao uuid; estado text;
        BEGIN
            IF TG_TABLE_NAME = 'dia_ficha' THEN
                IF TG_OP = 'UPDATE' AND NEW.versao_id <> OLD.versao_id THEN
                    RAISE EXCEPTION 'Dia não pode mudar de versão.'
                        USING ERRCODE = '55000';
                END IF;
                IF TG_OP = 'DELETE' THEN versao := OLD.versao_id;
                ELSE versao := NEW.versao_id; END IF;
            ELSE
                IF TG_OP = 'UPDATE' AND NEW.dia_id <> OLD.dia_id THEN
                    RAISE EXCEPTION 'Item não pode mudar de dia.'
                        USING ERRCODE = '55000';
                END IF;
                IF TG_OP = 'DELETE' THEN
                    SELECT versao_id INTO versao FROM academia.dia_ficha
                        WHERE id = OLD.dia_id;
                ELSE
                    SELECT versao_id INTO versao FROM academia.dia_ficha
                        WHERE id = NEW.dia_id;
                END IF;
            END IF;
            SELECT estado_publicacao INTO estado FROM academia.versao_ficha
                WHERE id = versao FOR UPDATE;
            IF estado = 'RASCUNHO'
               OR (estado = 'CONTEUDO_EXPIRADO' AND TG_OP = 'DELETE') THEN
                IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
                RETURN NEW;
            END IF;
            RAISE EXCEPTION 'Conteúdo publicado é imutável.'
                        USING ERRCODE = '55000';
        END;
        $$
    """)
    for table in ("dia_ficha", "item_ficha"):
        op.execute(
            f"CREATE TRIGGER proteger_conteudo_ficha BEFORE INSERT OR UPDATE OR DELETE "
            f"ON academia.{table} FOR EACH ROW "
            "EXECUTE FUNCTION academia.proteger_conteudo_ficha()"
        )


def downgrade() -> None:
    op.drop_table("parecer", schema="academia")
    op.drop_table("item_ficha", schema="academia")
    op.drop_table("dia_ficha", schema="academia")
    op.drop_table("versao_ficha", schema="academia")
    op.execute("DROP FUNCTION academia.proteger_conteudo_ficha()")
    op.execute("DROP FUNCTION academia.proteger_metadados_ficha()")
    op.drop_constraint(
        "uq_avaliacao_cliente_snapshot_id",
        "avaliacao",
        type_="unique",
        schema="academia",
    )
