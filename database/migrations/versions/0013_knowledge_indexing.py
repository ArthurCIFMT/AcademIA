"""Ingestões e fragmentos com proveniência e ativação completa."""

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
CREATE TABLE academia.ingestao (
	id UUID NOT NULL,
	documento_versao_id UUID NOT NULL,
	aprovacao_revisao INTEGER NOT NULL,
	extracao_id UUID NOT NULL,
	config_hash VARCHAR(64) NOT NULL,
	configuracao JSONB NOT NULL,
	plano_hash VARCHAR(64) NOT NULL,
	colecao VARCHAR(100) NOT NULL,
	estado VARCHAR(25) NOT NULL,
	total INTEGER NOT NULL,
	erro_codigo VARCHAR(80),
	criado_por UUID NOT NULL,
	iniciada_em TIMESTAMP WITH TIME ZONE NOT NULL,
	concluida_em TIMESTAMP WITH TIME ZONE,
	revision INTEGER NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_ingestao_config UNIQUE (documento_versao_id, config_hash),
        CONSTRAINT ck_ingestao_estado CHECK (estado IN
    ('PROCESSANDO','FALHA','CONCLUIDA','PENDENTE_TRATAMENTO','REVOGADA') AND total
    >= 0 AND revision >= 1),
        CONSTRAINT ck_ingestao_conclusao CHECK ((estado = 'CONCLUIDA' AND
    concluida_em IS NOT NULL AND erro_codigo IS NULL AND total > 0) OR (estado <>
    'CONCLUIDA' AND concluida_em IS NULL)),
	FOREIGN KEY(documento_versao_id) REFERENCES academia.documento_versao (id),
	FOREIGN KEY(criado_por) REFERENCES academia.usuario (id)
)
""")
    op.execute(
        """CREATE INDEX ix_ingestao_disponivel ON academia.ingestao (estado, colecao)"""
    )
    op.execute("""
CREATE TABLE academia.fragmento (
	id UUID NOT NULL,
	ingestao_id UUID NOT NULL,
	ordem INTEGER NOT NULL,
	pagina_inicio INTEGER,
	pagina_fim INTEGER,
	linha_inicio INTEGER,
	linha_fim INTEGER,
	secao TEXT,
	inicio INTEGER NOT NULL,
	fim INTEGER NOT NULL,
	texto_hash VARCHAR(64) NOT NULL,
	tokens INTEGER NOT NULL,
	input_tokens INTEGER NOT NULL,
	vetor_id UUID NOT NULL,
	colecao VARCHAR(100) NOT NULL,
	indexado_em TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	CONSTRAINT uq_fragmento_ordem UNIQUE (ingestao_id, ordem),
	CONSTRAINT uq_fragmento_vetor UNIQUE (vetor_id),
        CONSTRAINT ck_fragmento_limites CHECK (ordem >= 1 AND inicio >= 0 AND fim >
    inicio AND tokens >= 1 AND tokens <= 300 AND input_tokens <= 512),
        CONSTRAINT ck_fragmento_origem CHECK ((pagina_inicio IS NULL AND pagina_fim
    IS NULL AND linha_inicio IS NOT NULL AND linha_fim IS NOT NULL AND linha_inicio
    >= 1 AND linha_fim >= linha_inicio) OR (pagina_inicio IS NOT NULL AND pagina_fim
    IS NOT NULL AND pagina_inicio >= 1 AND pagina_fim = pagina_inicio AND
    linha_inicio IS NULL AND linha_fim IS NULL)),
	FOREIGN KEY(ingestao_id) REFERENCES academia.ingestao (id)
)
""")
    op.execute("""
CREATE FUNCTION academia.proteger_indexacao() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Histórico de indexação imutável';
    END IF;
    IF TG_TABLE_NAME = 'ingestao' THEN
        IF (to_jsonb(NEW) - ARRAY['estado','erro_codigo','concluida_em','revision'])
            IS DISTINCT FROM
            (to_jsonb(OLD) - ARRAY['estado','erro_codigo','concluida_em','revision'])
            OR NEW.revision <> OLD.revision + 1 THEN
            RAISE EXCEPTION 'Proveniência de ingestão imutável';
        END IF;
        IF NEW.estado = 'CONCLUIDA' AND (
            (SELECT count(*) FROM academia.fragmento WHERE ingestao_id = NEW.id)
                <> NEW.total OR
            (SELECT count(*) FROM academia.fragmento WHERE ingestao_id = NEW.id
                AND indexado_em IS NOT NULL) <> NEW.total) THEN
            RAISE EXCEPTION 'Ingestão incompleta';
        END IF;
    ELSE
        IF NEW.indexado_em IS NULL AND EXISTS (
            SELECT 1 FROM academia.ingestao
            WHERE id = NEW.ingestao_id AND estado = 'CONCLUIDA') THEN
            RAISE EXCEPTION 'Ingestão completa exige todos os checkpoints';
        END IF;
        IF (to_jsonb(NEW) - 'indexado_em') IS DISTINCT FROM
           (to_jsonb(OLD) - 'indexado_em') THEN
            RAISE EXCEPTION 'Proveniência de fragmento imutável';
        END IF;
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER proteger_ingestao BEFORE UPDATE OR DELETE ON academia.ingestao
FOR EACH ROW EXECUTE FUNCTION academia.proteger_indexacao();
CREATE TRIGGER proteger_fragmento BEFORE UPDATE OR DELETE ON academia.fragmento
FOR EACH ROW EXECUTE FUNCTION academia.proteger_indexacao();
""")


def downgrade() -> None:
    op.execute("""DROP TRIGGER proteger_fragmento ON academia.fragmento;
DROP TRIGGER proteger_ingestao ON academia.ingestao;
DROP FUNCTION academia.proteger_indexacao();""")
    op.drop_table("fragmento", schema="academia")
    op.drop_table("ingestao", schema="academia")
