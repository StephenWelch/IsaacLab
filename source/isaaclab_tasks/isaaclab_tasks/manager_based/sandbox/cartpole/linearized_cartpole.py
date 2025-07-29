import casadi as ca
import pinocchio as pin
import pinocchio.casadi as cpin

model, collision_model, visual_model = pin.buildModelsFromMJCF("inverted_pendulum.xml")