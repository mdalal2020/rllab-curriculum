from __future__ import print_function
from __future__ import absolute_import
from sandbox.rocky.tf.policies.base import StochasticPolicy
import numpy as np


class FixedClockPolicy(StochasticPolicy):
    def __init__(self, env_spec, high_policy, low_policy, subgoal_interval):
        self.high_policy = high_policy
        self.low_policy = low_policy
        self.ts = None
        self.subgoals = None
        self.subgoal_interval = subgoal_interval
        super(FixedClockPolicy, self).__init__(env_spec=env_spec)

    def reset(self, dones=None):
        self.high_policy.reset(dones)
        self.low_policy.reset(dones)
        if dones is None:
            dones = [True]
        dones = np.asarray(dones)
        if self.ts is None or len(dones) != len(self.ts):
            self.ts = np.array([-1] * len(dones))
            self.subgoals = np.zeros((len(dones),))
        self.ts[dones] = -1
        self.subgoals[dones] = np.nan

    def get_action(self, observation):
        actions, infos = self.get_actions([observation])
        return actions[0], {k: v[0] for k, v in infos.iteritems()}

    def get_actions(self, observations):
        self.ts += 1
        subgoals, _ = self.high_policy.get_actions(observations)
        update_mask = self.ts % self.subgoal_interval == 0
        self.subgoals[update_mask] = np.asarray(subgoals)[update_mask]
        act, _ = self.low_policy.get_actions(zip(observations, self.subgoals))
        return act, dict()
