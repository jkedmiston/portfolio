"""add_report_result
 
Revision ID: ebac28ee0d6a
Revises: 7346fd820f47
Create Date: 2020-12-29 05:53:22.488714

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils

# revision identifiers, used by Alembic.
revision = 'ebac28ee0d6a'
down_revision = '7346fd820f47'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('report_results',
                    sa.Column('user_email', sqlalchemy_utils.types.email.EmailType(
                        length=255), nullable=True),
                    sa.Column('service_email', sqlalchemy_utils.types.email.EmailType(
                        length=255), nullable=True),
                    sa.Column('slides_url', sqlalchemy_utils.types.url.URLType(),
                              nullable=True),
                    sa.Column('unique_tag', sqlalchemy_utils.types.uuid.UUIDType(
                        binary=False), nullable=True),
                    sa.Column('id', sa.Integer(),
                              autoincrement=True, nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.add_column('example_data', sa.Column(
        'created_at', sa.DateTime(), nullable=True))
    op.add_column('pubsub_messages', sa.Column(
        'created_at', sa.DateTime(), nullable=True))
    op.add_column('random_data', sa.Column(
        'created_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('random_data', 'created_at')
    op.drop_column('pubsub_messages', 'created_at')
    op.drop_column('example_data', 'created_at')
    op.drop_table('report_results')
    # ### end Alembic commands ###
