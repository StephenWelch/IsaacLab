from __future__ import annotations

import torch
from typing import TYPE_CHECKING
import pinocchio as pin
from pinocchio import casadi as cpin

import isaaclab.utils.math as math_utils
from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers.manager_base import ManagerTermBase
from isaaclab.managers.manager_term_cfg import ObservationTermCfg
from isaaclab.sensors import Camera, Imu, RayCaster, RayCasterCamera, TiledCamera
from isaaclab_tasks.manager_based.sandbox.locomotion.velocity.mdp import casadi
from cusadi import CusadiWrapper

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedEnv, ManagerBasedRLEnv

class centroidal_momentum(ManagerTermBase):

    def __init__(self, cfg: ObservationTermCfg, env: ManagerBasedEnv):
        super().__init__(cfg, env)

        asset_cfg = cfg.params.get("asset_cfg", SceneEntityCfg("robot"))

        self.cpin_model, self.cpin_data = casadi.build_model_data(casadi.G1_MJCF_PATH)

        self.cmm = CusadiWrapper(
            lambda: casadi.cmm(self.cpin_model, self.cpin_data),
            env.num_envs,
            gen_pytorch=True,
        )
        self.pinocchio_helper = casadi.PinocchioHelper(
            env,
            self.cpin_model,
            self.cpin_data,
            asset_cfg,
            dtype=torch.double,
        )

    def __call__(self, env: ManagerBasedEnv, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
        outputs = self.cmm([
            self.pinocchio_helper.get_q(),
            self.pinocchio_helper.get_v()
        ])

        return outputs[0].to(torch.float32)
