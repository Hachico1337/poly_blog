"""add likes and comments

Revision ID: 00dc9741eb4f
Revises: 7a035f2af7db
Create Date: 2024-06-02 19:27:42.120070

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00dc9741eb4f'
down_revision = '7a035f2af7db'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('like',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['post_id'], ['post.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('like', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_like_timestamp'), ['timestamp'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('like', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_like_timestamp'))

    op.drop_table('like')
    # ### end Alembic commands ###