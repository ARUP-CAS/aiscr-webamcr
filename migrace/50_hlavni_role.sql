INSERT INTO public.auth_user_groups (user_id, group_id) SELECT id, hlavni_role FROM public.auth_user where id not in (
SELECT au.id
	FROM public.auth_user as au
	INNER JOIN public.auth_user_groups aug on au.id = aug.user_id and au.hlavni_role = aug.group_id
) AND hlavni_role is not null;
ALTER TABLE auth_user DROP COLUMN hlavni_role;
