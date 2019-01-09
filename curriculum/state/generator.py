import numpy as np
from rllab.misc.overrides import overrides
from curriculum.gan.gan import FCGAN


class StateGenerator(object):
    """A base class for state generation."""

    def pretrain_uniform(self):
        """Pretrain the generator distribution to uniform distribution in the limit."""
        raise NotImplementedError

    def pretrain(self, states):
        """Pretrain with state distribution in the states list."""
        raise NotImplementedError

    def sample_states(self, size):
        """Sample states with given size."""
        raise NotImplementedError

    def sample_states_with_noise(self, size):
        """Sample states with noise."""
        raise NotImplementedError

    def train(self, states, labels):
        """Train with respect to given states and labels."""
        raise NotImplementedError


class CrossEntropyStateGenerator(StateGenerator):
    """Maintain a state list and add noise to current states to generate new states."""

    def __init__(self, state_size, state_range, noise_std=1.0,
                 state_center=None):
        self.state_list = np.array([])
        self.state_range = state_range
        self.noise_std = noise_std
        self.state_center = np.array(state_center) if state_center is not None else np.zeros(state_size)

    def pretrain_uniform(self, size=1000):
        states = self.state_center + np.random.uniform(
            -self.state_range, self.state_range, size=(size, self.state_size)
        )
        return self.pretrain(states)

    def pretrain(self, states):
        self.state_list = np.array(states)

    def sample_states(self, size):
        if len(self.state_list) == 0:
            raise ValueError('Generator uninitialized!')

        states = sample_matrix_row(self.state_list, size)
        return np.clip(
            states + np.random.randn(*states.shape) * self.noise_std,
            self.state_center - self.state_range, self.state_center + self.state_range
        )

    def sample_states_with_noise(self, size):
        return self.sample_states(size)

    def train(self, states, labels):
        labels = np.mean(labels, axis=1) >= 1
        good_states = np.array(states)[labels, :]
        if len(good_states) != 0:
            self.state_list = good_states


class StateGAN(StateGenerator):
    """A GAN for generating states. It is just a wrapper for clgan.GAN.FCGAN"""

    def __init__(self, state_size, evaluater_size,
                 state_noise_level, state_range=None, state_center=None, state_bounds=None, *args, **kwargs):
        self.gan = FCGAN(
            generator_output_size=state_size,
            discriminator_output_size=evaluater_size,
            *args,
            **kwargs
        )
        self.state_size = state_size
        self.evaluater_size = evaluater_size
        self.state_noise_level = state_noise_level

    def pretrain(self, states, outer_iters=500, generator_iters=None, discriminator_iters=None):
        """
        Pretrain the state GAN to match the distribution of given states.
        :param states: the state distribution to match
        :param outer_iters: of the GAN
        """
        labels = np.ones((states.shape[0], self.evaluater_size))  # all state same label --> uniform
        return self.train(
            states, labels, outer_iters, generator_iters, discriminator_iters
        )

    def sample_states(self, size):  # un-normalizes the states
        return self.gan.sample_generator(size)

    @overrides
    def train(self, states, labels, outer_iters, generator_iters=None, discriminator_iters=None):
        return self.gan.train(
            states, labels, outer_iters, generator_iters, discriminator_iters
        )

    def discriminator_predict(self, states):
        return self.gan.discriminator_predict(states)
