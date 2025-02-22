"""
 OpenVINO DL Workbench
 Class for ORM model described System Resources of a Target

 Copyright (c) 2020 Intel Corporation

 LEGAL NOTICE: Your use of this software and any required dependent software (the “Software Package”) is subject to
 the terms and conditions of the software license agreements for Software Package, which may also include
 notices, disclaimers, or license terms for third party or open source software
 included in or with the Software Package, and your use indicates your acceptance of all such terms.
 Please refer to the “third-party-programs.txt” or other similarly-named text file included with the Software Package
 for additional details.
 You may obtain a copy of the License at
      https://software.intel.com/content/dam/develop/external/us/en/documents/intel-openvino-license-agreements.pdf
"""

from sqlalchemy import Column, Integer, Float
from sqlalchemy.orm import Session

from wb.main.models.base_model import BaseModel


# pylint: disable=too-many-instance-attributes
class SystemResourcesModel(BaseModel):
    __tablename__ = 'system_resources'

    id = Column(Integer, primary_key=True, autoincrement=True)

    cpu_usage = Column(Float, nullable=True)

    ram_total = Column(Float, nullable=True)
    ram_used = Column(Float, nullable=True)
    ram_available = Column(Float, nullable=True)
    ram_percentage = Column(Float, nullable=True)

    swap_total = Column(Float, nullable=True)
    swap_used = Column(Float, nullable=True)
    swap_available = Column(Float, nullable=True)
    swap_percentage = Column(Float, nullable=True)

    disk_total = Column(Float, nullable=True)
    disk_used = Column(Float, nullable=True)
    disk_available = Column(Float, nullable=True)
    disk_percentage = Column(Float, nullable=True)

    def update(self, data: dict, session: Session):
        cpu_data = data.get('CPU')
        if cpu_data:
            self.cpu_usage = sum(cpu_data) / len(cpu_data)
        self.set_ram_information(data['RAM'])
        self.set_swap_information(data['RAM']['SWAP'])
        self.set_disk_information(data['DISK'])
        self.write_record(session)

    def set_ram_information(self, data: dict):
        self.ram_total = data['TOTAL']
        self.ram_used = data['USED']
        self.ram_available = data['AVAILABLE']
        self.ram_percentage = data['PERCENTAGE']

    def set_swap_information(self, data: dict):
        self.swap_total = data['TOTAL']
        self.swap_used = data['USED']
        self.swap_available = data['AVAILABLE']
        self.swap_percentage = data['PERCENTAGE']

    def set_disk_information(self, data: dict):
        self.disk_total = data['TOTAL']
        self.disk_used = data['USED']
        self.disk_available = data['AVAILABLE']
        self.disk_percentage = data['PERCENTAGE']

    def json(self) -> dict:
        return {
            'cpuUsage': self.cpu_usage,
            'ram': {
                'total': self.ram_total,
                'used': self.ram_used,
                'available': self.ram_available,
                'percentage': self.ram_percentage,
            },
            'swap': {
                'total': self.swap_total,
                'used': self.swap_used,
                'available': self.swap_available,
                'percentage': self.swap_percentage,
            },
            'disk': {
                'total': self.disk_total,
                'used': self.disk_used,
                'available': self.disk_available,
                'percentage': self.disk_percentage,
            },
        }
