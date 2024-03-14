insert into public.heslar_nazev
VALUES (48, 'jistota_urceni', true),
       (49, 'stav_dochovani', true);
ALTER TABLE heslar
    ALTER COLUMN ident_cely SET DEFAULT ('HES-'::text || right(concat('000000', nextval('heslar_ident_cely_seq')::text), 6));
insert into public.heslar
    (nazev_heslare, heslo, heslo_en, razeni)
values (48,
        'jisté (> 95 %)',
        'certain (> 95%)',
        1),
       (48,
        'nejisté (50–95 %)',
        'uncertain (50–95%)',
        2),
       (48,
        'domnělé (5–50 %)',
        'alleged (5–50%)',
        3),
       (48,
        'pseudolokalita (< 5 %)',
        'pseudo-site (< 5%)',
        4),
       (49,
        'zaniklá lokalita',
        'buried site',
        1),
       (49,
        'lokalita pod zástavbou',
        'site in built environment',
        2),
       (49,
        'nadzemní relikty',
        'aboveground remains',
        3),
       (49,
        'ruina',
        'ruin',
        4),
       (49,
        'historická budova/komplex',
        'historical building/complex',
        5);
update heslar
set heslo    = 'Katastrální území',
    heslo_en = 'Cadastral area'
where ident_cely = 'HES-001073';
