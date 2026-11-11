-- Fixture sintética do TRN-01 para o banco academia_test.
DO $$
BEGIN
    IF current_database() <> 'academia_test' THEN
        RAISE EXCEPTION 'Este seed deve ser executado apenas em academia_test.';
    END IF;

    INSERT INTO academia.equipamento (id, nome, ativo, operacional, revision)
    VALUES
        ('11100000-0000-4000-8000-000000000001', '[SINTÉTICO] Recurso A', true, true, 1),
        ('11100000-0000-4000-8000-000000000002', '[SINTÉTICO] Recurso B', true, false, 1),
        ('11100000-0000-4000-8000-000000000003', '[SINTÉTICO] Recurso C', true, true, 1)
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO academia.exercicio
        (id, nome, nome_normalizado, descricao, grupo_muscular, dispensa_equipamento, ativo, revision)
    VALUES
        ('11200000-0000-4000-8000-000000000001', '[SINTÉTICO] Movimento sem recurso',
         '[sintético] movimento sem recurso', 'Registro fictício para o ensaio de catálogo.',
         'Grupo sintético', true, true, 1),
        ('11200000-0000-4000-8000-000000000002', '[SINTÉTICO] Movimento com alternativas',
         '[sintético] movimento com alternativas', 'Registro fictício para testar alternativas.',
         'Grupo sintético', false, true, 1)
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO academia.exercicio_recurso_grupo (id, exercicio_id)
    VALUES
        ('11300000-0000-4000-8000-000000000001', '11200000-0000-4000-8000-000000000002'),
        ('11300000-0000-4000-8000-000000000002', '11200000-0000-4000-8000-000000000002')
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO academia.exercicio_recurso (id, grupo_id, equipamento_id)
    VALUES
        ('11400000-0000-4000-8000-000000000001', '11300000-0000-4000-8000-000000000001', '11100000-0000-4000-8000-000000000001'),
        ('11400000-0000-4000-8000-000000000002', '11300000-0000-4000-8000-000000000001', '11100000-0000-4000-8000-000000000002'),
        ('11400000-0000-4000-8000-000000000003', '11300000-0000-4000-8000-000000000002', '11100000-0000-4000-8000-000000000003')
    ON CONFLICT (id) DO NOTHING;
END
$$;
