CREATE INDEX auth_user_id
ON public.auth_user USING btree
(id ASC NULLS LAST)
;

CREATE INDEX historie_vazba_typ_zmeny
ON public.historie USING btree
(vazba ASC NULLS LAST, typ_zmeny COLLATE pg_catalog."default" ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX organizace_id
ON public.organizace USING btree
(id ASC NULLS LAST)
;

CREATE INDEX heslar_id
ON public.heslar USING btree
(id ASC NULLS LAST)
;

CREATE INDEX archeologicky_zaznam_id
ON public.archeologicky_zaznam USING btree
(id ASC NULLS LAST)
;

CREATE INDEX soubor_vazba
ON public.soubor USING btree
(vazba ASC NULLS LAST)
TABLESPACE pg_default;
;

CREATE INDEX historie_id
ON public.historie USING btree
(id ASC NULLS LAST)
;

CREATE INDEX ruian_katastr_id
ON public.ruian_katastr USING btree
(id ASC NULLS LAST)
;

CREATE INDEX projekt_ident_cely
ON public.projekt USING btree
(ident_cely ASC NULLS LAST)
;

CREATE INDEX historie_uzivatel
ON public.historie USING btree
(uzivatel ASC NULLS LAST)
;

CREATE INDEX ix_auth_user_id
ON public.auth_user USING btree
(id ASC NULLS LAST)
;
