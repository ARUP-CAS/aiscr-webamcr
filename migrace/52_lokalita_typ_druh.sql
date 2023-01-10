INSERT INTO heslar_hierarchie
VALUES ((SELECT id FROM heslar WHERE ident_cely = 'HES-000133'), (SELECT id FROM heslar WHERE ident_cely = 'HES-001122'), 'podřízenost'),
    ((SELECT id FROM heslar WHERE ident_cely = 'HES-000134'), (SELECT id FROM heslar WHERE ident_cely = 'HES-001122'), 'podřízenost'),
    ((SELECT id FROM heslar WHERE ident_cely = 'HES-000135'), (SELECT id FROM heslar WHERE ident_cely = 'HES-001122'), 'podřízenost'),
    ((SELECT id FROM heslar WHERE ident_cely = 'HES-000132'), (SELECT id FROM heslar WHERE ident_cely = 'HES-001123'), 'podřízenost'),
    ((SELECT id FROM heslar WHERE ident_cely = 'HES-000136'), (SELECT id FROM heslar WHERE ident_cely = 'HES-001124'), 'podřízenost'),
    ((SELECT id FROM heslar WHERE ident_cely = 'HES-000137'), (SELECT id FROM heslar WHERE ident_cely = 'HES-001124'), 'podřízenost'),
    ((SELECT id FROM heslar WHERE ident_cely = 'HES-000138'), (SELECT id FROM heslar WHERE ident_cely = 'HES-001124'), 'podřízenost'),
    ((SELECT id FROM heslar WHERE ident_cely = 'HES-000139'), (SELECT id FROM heslar WHERE ident_cely = 'HES-001124'), 'podřízenost'),
    ((SELECT id FROM heslar WHERE ident_cely = 'HES-000140'), (SELECT id FROM heslar WHERE ident_cely = 'HES-001124'), 'podřízenost');
