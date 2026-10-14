"""Extraction runs, claims and exact-text evidence for saved job captures."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "0003_extractions"
down_revision = "0002_job_captures"
branch_labels = None
depends_on = None

def upgrade():
    op.create_unique_constraint("uq_snapshots_owned", "job_snapshots", ["owner_id", "id"], schema="career")
    op.create_table("extraction_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("extractor", sa.String(60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id", "snapshot_id"], ["career.job_snapshots.owner_id", "career.job_snapshots.id"], ondelete="CASCADE", name="fk_runs_owned_snapshot"),
        sa.UniqueConstraint("owner_id", "id", name="uq_runs_owned"), schema="career")
    op.create_table("job_claims",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("field_key", sa.String(40), nullable=False),
        sa.Column("knowledge", sa.String(12), nullable=False),
        sa.Column("requirement", sa.String(13)),
        sa.Column("value", postgresql.JSONB(none_as_null=True)),
        sa.Column("basis", sa.Text()),
        sa.ForeignKeyConstraint(["owner_id", "run_id"], ["career.extraction_runs.owner_id", "career.extraction_runs.id"], ondelete="CASCADE", name="fk_claims_owned_run"),
        sa.UniqueConstraint("owner_id", "id", name="uq_claims_owned"),
        sa.CheckConstraint("knowledge IN ('explicit', 'inferred', 'not_provided')", name="ck_claims_knowledge"),
        sa.CheckConstraint("requirement IS NULL OR requirement IN ('required', 'preferred', 'informational')", name="ck_claims_requirement"),
        sa.CheckConstraint("(knowledge = 'not_provided') = (value IS NULL)", name="ck_claims_value_matches_knowledge"),
        sa.CheckConstraint("knowledge <> 'inferred' OR basis IS NOT NULL", name="ck_claims_inference_basis"), schema="career")
    op.create_table("claim_evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("start_char", sa.Integer(), nullable=False),
        sa.Column("end_char", sa.Integer(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id", "claim_id"], ["career.job_claims.owner_id", "career.job_claims.id"], ondelete="CASCADE", name="fk_evidence_owned_claim"),
        sa.CheckConstraint("start_char >= 0 AND end_char > start_char", name="ck_evidence_range"), schema="career")

def downgrade():
    op.drop_table("claim_evidence", schema="career")
    op.drop_table("job_claims", schema="career")
    op.drop_table("extraction_runs", schema="career")
    op.drop_constraint("uq_snapshots_owned", "job_snapshots", schema="career", type_="unique")
