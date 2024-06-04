BEGIN;
-- protect against concurrent inserts while you update the counter
LOCK TABLE auth_user_groups IN EXCLUSIVE MODE;
-- Update the sequence
SELECT setval(
        'auth_user_groups_id_seq',
        COALESCE(
            (
                SELECT MAX(id) + 1
                FROM auth_user_groups
            ),
            1
        ),
        false
    );
COMMIT;
