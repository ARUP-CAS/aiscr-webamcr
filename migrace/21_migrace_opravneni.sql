-- vytvoreni tabulky s konkretnimi opravnenimi
CONSTRAINT opravneni_konkretni_pkey PRIMARY KEY (id),
CONSTRAINT opravneni_konkretni_id_key UNIQUE (id),
CONSTRAINT opravneni_opravneni FOREIGN KEY (parent_opravneni) REFERENCES public.opravneni (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE
SET NULL,
    CONSTRAINT opravneni_vazba_na_opravneni FOREIGN KEY (vazba_na_konkretni_opravneni) REFERENCES public.opravneni_konkretni (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE
SET NULL
)