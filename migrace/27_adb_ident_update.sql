update public.vyskovy_bod set ident_cely = regexp_replace(ident_cely, '^(X?-?ADB-\w{6})-(\d{4}-V\d{4}$)', '\1-00\2')
where ident_cely ~ '^X?-?ADB-\w{6}-\d{4}-V\d{4}$';