"""Add binary flag to ProfilingJob

Revision ID: 0cae866b8e0b
Revises: 6ad584444fd1
Create Date: 2021-10-27 20:10:42.644969

"""

"""
 OpenVINO DL Workbench
 Migration: Add binary flag to ProfilingJob

 Copyright (c) 2021 Intel Corporation

 LEGAL NOTICE: Your use of this software and any required dependent software (the “Software Package”) is subject to
 the terms and conditions of the software license agreements for Software Package, which may also include
 notices, disclaimers, or license terms for third party or open source software
 included in or with the Software Package, and your use indicates your acceptance of all such terms.
 Please refer to the “third-party-programs.txt” or other similarly-named text file included with the Software Package
 for additional details.
 You may obtain a copy of the License at
      https://software.intel.com/content/dam/develop/external/us/en/documents/intel-openvino-license-agreements.pdf
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0cae866b8e0b'
down_revision = '6ad584444fd1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('profiling_jobs', sa.Column('binary', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('profiling_jobs', 'binary')
    # ### end Alembic commands ###
