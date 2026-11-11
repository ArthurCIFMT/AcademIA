"""Execuções IA duráveis e publicação assistida. Revision 0014."""

from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "\nCREATE TABLE academia.execucao_ia (\n\tid UUID NOT NULL, \n\tator_id UUID NOT NULL, \n\tcliente_id UUID NOT NULL, \n\tidempotency_key VARCHAR(100) NOT NULL, \n\tentrada_hash VARCHAR(64) NOT NULL, \n\trequest_hash VARCHAR(64) NOT NULL, \n\tfinalidade VARCHAR(25) NOT NULL, \n\testado VARCHAR(35) NOT NULL, \n\tonboarding_id UUID, \n\tversao_base_id UUID, \n\tversao_publicada_id UUID, \n\tworker_id UUID NOT NULL, \n\tconfig_version INTEGER NOT NULL, \n\tmodelo VARCHAR(100) NOT NULL, \n\tprompt_version VARCHAR(60) NOT NULL, \n\tiniciada_em TIMESTAMP WITH TIME ZONE NOT NULL, \n\tprazo_em TIMESTAMP WITH TIME ZONE NOT NULL, \n\tterminada_em TIMESTAMP WITH TIME ZONE, \n\tresultado JSONB NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_execucao_ia_chave UNIQUE (cliente_id, idempotency_key), \n\tFOREIGN KEY(cliente_id, onboarding_id) REFERENCES academia.onboarding_versao (cliente_id, id), \n\tFOREIGN KEY(cliente_id, versao_publicada_id) REFERENCES academia.versao_ficha (cliente_id, id), \n\tFOREIGN KEY(cliente_id, versao_base_id) REFERENCES academia.versao_ficha (cliente_id, id), \n\tCONSTRAINT ck_execucao_finalidade CHECK (finalidade IN ('DUVIDA','GERACAO','ADAPTACAO')), \n\tCONSTRAINT ck_execucao_prazo CHECK ((estado = 'EM_EXECUCAO') = (terminada_em IS NULL) AND prazo_em > iniciada_em), \n\tCONSTRAINT ck_execucao_sem_copia_ficha CHECK (jsonb_typeof(resultado) = 'object' AND NOT (resultado ? 'proposta')), \n\tFOREIGN KEY(ator_id) REFERENCES academia.usuario (id), \n\tFOREIGN KEY(cliente_id) REFERENCES academia.cliente (usuario_id)\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_execucao_cliente_tempo ON academia.execucao_ia (cliente_id, iniciada_em)"
    )
    op.execute(
        "\nCREATE TABLE academia.triagem (\n\tid UUID NOT NULL, \n\texecucao_id UUID NOT NULL, \n\tonboarding_id UUID NOT NULL, \n\tresumo JSONB NOT NULL, \n\tregra_version INTEGER NOT NULL, \n\testado VARCHAR(35), \n\tmotivos JSONB NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (execucao_id), \n\tFOREIGN KEY(execucao_id) REFERENCES academia.execucao_ia (id), \n\tFOREIGN KEY(onboarding_id) REFERENCES academia.onboarding_versao (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE academia.etapa_ia (\n\tid UUID NOT NULL, \n\texecucao_id UUID NOT NULL, \n\ttipo VARCHAR(25) NOT NULL, \n\testado VARCHAR(25) NOT NULL, \n\tchamadas INTEGER NOT NULL, \n\tlimite_saida_tokens INTEGER NOT NULL, \n\tprompt_bytes INTEGER NOT NULL, \n\tprompt_sha256 VARCHAR(64) NOT NULL, \n\tenviada_em TIMESTAMP WITH TIME ZONE, \n\tduracao_ms INTEGER, \n\ttokens_entrada INTEGER, \n\ttokens_saida INTEGER, \n\tdados JSONB NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_etapa_execucao_tipo UNIQUE (execucao_id, tipo), \n\tCONSTRAINT ck_etapa_orcamento CHECK (chamadas BETWEEN 0 AND 1 AND limite_saida_tokens > 0 AND prompt_bytes > 0), \n\tFOREIGN KEY(execucao_id) REFERENCES academia.execucao_ia (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE academia.evidencia_execucao (\n\tid UUID NOT NULL, \n\texecucao_id UUID NOT NULL, \n\tfragmento_id UUID NOT NULL, \n\tfinalidade VARCHAR(25) NOT NULL, \n\tmetadados JSONB NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_evidencia_execucao_fragmento UNIQUE (execucao_id, fragmento_id), \n\tFOREIGN KEY(execucao_id) REFERENCES academia.execucao_ia (id), \n\tFOREIGN KEY(fragmento_id) REFERENCES academia.fragmento (id)\n)\n\n"
    )
    op.add_column(
        "versao_ficha",
        sa.Column("explicacao", sa.Text(), nullable=True),
        schema="academia",
    )
    op.execute(
        "CREATE FUNCTION academia.proteger_explicacao_ficha() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF OLD.estado_publicacao <> 'RASCUNHO' AND NEW.explicacao IS DISTINCT FROM OLD.explicacao AND NOT (NEW.estado_publicacao = 'CONTEUDO_EXPIRADO' AND NEW.explicacao IS NULL) THEN RAISE EXCEPTION 'Explicação publicada imutável'; END IF; RETURN NEW; END $$; CREATE TRIGGER proteger_explicacao_ficha BEFORE UPDATE ON academia.versao_ficha FOR EACH ROW EXECUTE FUNCTION academia.proteger_explicacao_ficha();"
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER proteger_explicacao_ficha ON academia.versao_ficha; DROP FUNCTION academia.proteger_explicacao_ficha();"
    )
    op.drop_column("versao_ficha", "explicacao", schema="academia")
    op.drop_table("evidencia_execucao", schema="academia")
    op.drop_table("etapa_ia", schema="academia")
    op.drop_table("triagem", schema="academia")
    op.drop_table("execucao_ia", schema="academia")
