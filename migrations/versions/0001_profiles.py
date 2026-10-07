"""Create versioned local profiles without changing existing runtime tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_profiles"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS career")
    op.create_table("owners",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("label", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="career",
    )
    op.create_table("profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["career.owners.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("owner_id", "id", name="uq_profiles_owner_id"),
        schema="career",
    )
    op.create_table("profile_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("preferences_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id", "profile_id"],
            ["career.profiles.owner_id", "career.profiles.id"], ondelete="CASCADE",
            name="fk_versions_owned_profile"),
        sa.UniqueConstraint("owner_id", "profile_id", "version", name="uq_versions_profile_number"),
        sa.CheckConstraint("version > 0", name="ck_versions_positive"),
        sa.CheckConstraint("schema_version = 1", name="ck_versions_schema"),
        schema="career",
    )


def downgrade():
    op.drop_table("profile_versions", schema="career")
    op.drop_table("profiles", schema="career")
    op.drop_table("owners", schema="career")
    # Preserve the schema, which may later contain unrelated data.
