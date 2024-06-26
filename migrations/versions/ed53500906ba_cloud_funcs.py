"""cloud funcs

Revision ID: ed53500906ba
Revises: c8074206d00a
Create Date: 2023-11-17 04:00:34.028562

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ed53500906ba'
down_revision = 'c8074206d00a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cloud_functions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('definition', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('cloud_functions')
    # ### end Alembic commands ###
