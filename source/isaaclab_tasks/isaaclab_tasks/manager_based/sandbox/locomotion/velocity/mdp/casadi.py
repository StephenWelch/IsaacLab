import torch
import casadi as ca
import pinocchio as pin
from pinocchio import casadi as cpin
from isaaclab.assets.articulation.articulation import Articulation
from isaaclab.envs.manager_based_env import ManagerBasedEnv
from isaaclab.managers import SceneEntityCfg

G1_MJCF_PATH = "/home/stephen/code/IsaacLab/source/isaaclab_tasks/isaaclab_tasks/manager_based/sandbox/locomotion/velocity/config/g1/mjcf/g1.xml"
MJ_TO_IL_JOINT_MAP = {
    "waist_yaw_joint": "torso_joint",
}

def build_model_data(mjcf_path: str) -> tuple[cpin.Model, cpin.Data]:
    pin_model = pin.buildModelFromMJCF(mjcf_path)
    cpin_model = cpin.Model(pin_model)
    cpin_data = cpin_model.createData()
    return cpin_model, cpin_data

class PinocchioHelper:
    def __init__(self, env: ManagerBasedEnv, model: cpin.Model, data: cpin.Data, asset_cfg: SceneEntityCfg, dtype: torch.dtype = torch.double):
        self.model = model
        self.data = data
        self.dtype = dtype
        self.asset_cfg = asset_cfg

        # Build mapping between IL and pinocchio joint indices
        # Joints that exist in the pinocchio model but not in the asset are ignored
        self.asset = env.scene[asset_cfg.name]
        self.asset_joint_idxs = []
        self.pin_joint_idxs = []
        for i, name in enumerate(self.joint_names):
            if name in self.asset.joint_names:
                self.asset_joint_idxs.append(self.asset.joint_names.index(name))
                self.pin_joint_idxs.append(i)
            else:
                print(f"Joint {name} not found in asset {asset_cfg.name}")

        # Preallocate tensors for joint positions and velocities to help with reordering
        # TODO incoming tensors should be cast to self.dtype instead of this being float32
        self._jnt_pos = torch.zeros(env.num_envs, len(self.joint_names), device=env.device, dtype=torch.float32)
        self._jnt_vel = torch.zeros(env.num_envs, len(self.joint_names), device=env.device, dtype=torch.float32)

    def build_q(
        self,
        root_pos_w: torch.Tensor,
        root_quat_w: torch.Tensor,
        jnt_pos: torch.Tensor,
    ) -> torch.Tensor: 
        self._jnt_pos[:, self.pin_joint_idxs] = jnt_pos[:, self.asset_joint_idxs]
        return torch.cat([
            root_pos_w,
            # Pinocchio uses x, y, z, w
            root_quat_w[:, 1:4],
            root_quat_w[:, 0:1],
            self._jnt_pos,
        ], dim=1).to(self.dtype)
        
    def build_v(
        self,
        root_lin_vel_w: torch.Tensor,
        root_ang_vel_b: torch.Tensor,
        jnt_vel: torch.Tensor,
    ) -> torch.Tensor:
        self._jnt_vel[:, self.pin_joint_idxs] = jnt_vel[:, self.asset_joint_idxs]
        return torch.cat([
            root_lin_vel_w,
            root_ang_vel_b,
            self._jnt_vel,
        ], dim=1).to(self.dtype)

    def get_q(self) -> torch.Tensor:
        return self.build_q(
            self.asset.data.root_pos_w,
            self.asset.data.root_quat_w,
            self.asset.data.joint_pos,
        )
        
    def get_v(self) -> torch.Tensor:
        return self.build_v(
            self.asset.data.root_lin_vel_w,
            self.asset.data.root_ang_vel_b,
            self.asset.data.joint_vel,
        )

    @property
    def joint_names(self) -> list[str]:
        return [MJ_TO_IL_JOINT_MAP.get(n, str(n)) for n in self.model.names][2:]

def ccrba(cpin_model: cpin.Model, cpin_data: cpin.Data) -> ca.Function:
    q = ca.SX.sym("q", cpin_model.nq)
    v = ca.SX.sym("v", cpin_model.nv)
    
    def _compute(q: ca.SX, v: ca.SX):
        cpin.ccrba(cpin_model, cpin_data, q, v)
        return [cpin_data.Ig.inertia, cpin_data.Ag, cpin_data.hg.vector]
    
    return ca.Function(
        "ccrba",
        [q, v],
        _compute(q, v)
    )

# def cmm(cpin_model: cpin.Model, cpin_data: cpin.Data) -> ca.Function:
#     q = ca.SX.sym("q", cpin_model.nq)
#     v = ca.SX.sym("v", cpin_model.nv)
#     return ca.Function(
#         "cmm",
#         [q, v],
#         [
#             cpin.computeCentroidalMomentum(cpin_model, cpin_data, q, v).vector
#         ]
#     )