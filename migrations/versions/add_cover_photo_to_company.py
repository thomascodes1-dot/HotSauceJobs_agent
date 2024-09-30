"""Add cover_photo to Company model

Revision ID: add_cover_photo_to_company
Revises: 1b551c0b2201
Create Date: 2024-09-30 23:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_cover_photo_to_company'
down_revision = '1b551c0b2201'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('company', sa.Column('cover_photo', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('company', 'cover_photo')
