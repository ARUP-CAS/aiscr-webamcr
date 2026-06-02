from django.db import migrations

# Záchranná síť na úrovni DB: i raw-SQL importy obcházející Django ORM tím mají
# zaručeno, že se e-mail (přihlašovací jméno) vždy uloží malými písmeny.
FORWARD_SQL = """
CREATE OR REPLACE FUNCTION lowercase_email()
RETURNS TRIGGER AS $$
BEGIN
    NEW.email := lower(NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_lowercase_email
BEFORE INSERT OR UPDATE
ON auth_user
FOR EACH ROW
EXECUTE FUNCTION lowercase_email();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS trg_lowercase_email ON auth_user;
DROP FUNCTION IF EXISTS lowercase_email();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("uzivatel", "0030_add_notofikace_typ_E-NZ-03"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD_SQL, reverse_sql=REVERSE_SQL),
    ]
