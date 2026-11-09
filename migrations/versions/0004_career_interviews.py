"""Persist confirmed career interview facts and their original answers."""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004_career_interviews"
down_revision = "0003_extractions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "career_interviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("answers", JSONB(), nullable=False),
        sa.Column("facts", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["career.owners.id"], ondelete="CASCADE"),
        schema="career",
    )
    op.create_index("ix_career_interviews_owner_id", "career_interviews", ["owner_id"], schema="career")


def downgrade():
    op.drop_table("career_interviews", schema="career")
