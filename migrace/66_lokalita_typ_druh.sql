INSERT INTO heslar_hierarchie
VALUES ((SELECT id FROM heslar WHERE ident_cely = 'HES-000133'), (SELECT id FROM heslar WHERE ident_cely = 'HES-001122'), 'podřízenost'),
    ((SELECT id FROM heslar WHERE ident_cely = 'HES-000134'), (SELECT id FROM heslar WHERE ident_cely = 'HES-001122'), 'podřízenost'),
    ((SELECT id FROM heslar WHERE ident_cely = 'HES-000132'), (SELECT id FROM heslar WHERE ident_cely = 'HES-001123'), 'podřízenost'),
    ((SELECT id FROM heslar WHERE ident_cely = 'HES-000136'), (SELECT id FROM heslar WHERE ident_cely = 'HES-001124'), 'podřízenost');
