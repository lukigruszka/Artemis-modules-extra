import subprocess

from artemis import utils, load_risk_class
from artemis.binds import TaskStatus, TaskType, Service
from artemis.module_base import ArtemisBase
from artemis.task_utils import get_target_url, get_target_host
from karton.core import Task
import string

from extra_modules_config import ExtraModulesConfig

logger = utils.build_logger(__name__)

@load_risk_class.load_risk_class(load_risk_class.LoadRiskClass.LOW)
class WhatVPN(ArtemisBase):
    """ 
    Runs what-vpn -> SSL VPN identifier
    """
    
    identity = "what-vpn"
    filters = [
        {"type": TaskType.IP.value}
    ]

    def _process(self, current_task: Task, host: str) -> None:
        output = subprocess.run(
            [
                "what-vpn",
                "--keep-going-after-exception",
                "--timeout",
                ExtraModulesConfig.WHATVPN_TIMEOUT_S,
                host
            ],
            capture_output=True
        )
        output = output.stdout.decode("utf-8")
        detected_vpn = []

        error_messages = ["error", "timeout", "no match"]
        if any(msg in output for msg in error_messages):
            status = TaskStatus.OK
            status_reason = "Could not identify a VPN gateway"
        else:
            # Format of what-vpn output:
            # scanned_host: identified_VPN [VPN_version]
            detected_vpn.append(output.split(' ', 1)[1])
            status = TaskStatus.INTERESTING
            status_reason = f"Detected {detected_vpn}"

        # Save the task result to the database
        self.db.save_task_result(
            task=current_task,
            status = status,
            status_reason=status_reason,
            data=detected_vpn,
        )

    def run(self, current_task: Task) -> None:
        target_host = get_target_host(current_task)
        
        self.log.info("Requested to check if %s is a VPN gateway", target_host)

        self._process(current_task, target_host)


if __name__ == "__main__":
    WhatVPN().loop()