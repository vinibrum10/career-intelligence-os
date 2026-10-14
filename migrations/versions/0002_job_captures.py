"""Manual job sources and immutable capture history."""
from alembic import op
import sqlalchemy as sa
revision = "0002_job_captures"
down_revision = "0001_profiles"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("job_sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["career.owners.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("owner_id", "id", name="uq_jobs_owned_source"), schema="career")
    op.create_table("job_snapshots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("source_url", sa.Text()),
        sa.Column("association_confirmed", sa.Boolean(), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True)),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id", "source_id"], ["career.job_sources.owner_id", "career.job_sources.id"], ondelete="CASCADE", name="fk_snapshots_owned_source"),
        sa.UniqueConstraint("owner_id", "source_id", "version", name="uq_snapshots_source_version"),
        sa.CheckConstraint("version > 0", name="ck_snapshots_positive"), schema="career")

def downgrade():
    op.drop_table("job_snapshots", schema="career")
    op.drop_table("job_sources", schema="career")
