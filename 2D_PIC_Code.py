import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time as time
from functools import partial

from ParticleManager import ParticleManager
from ParticleSource import ParticleSource
from Diagnostics import EnergyDiagnostic, ParticleSystemHistory
from HelperFunctions import*

# THIS CODE IS 54% RILEY APPROVED


# TODO: Save animation to video
# ANIMATION
def animate_step(i):
    particle_system.update_step()

    # animate particles
    # positions.set_data(particle_system.particle_positions[0, :], particle_system.particle_positions[1, :])

    # animate charge density
    densities.set_data(particle_system.grid_charge_densities.T[::-1])

    # animate potentials
    potentials.set_array(particle_system.grid_potentials.T[::-1])

    return potentials, densities,


def animate_history(i):
    # animate particles
    # positions.set_data(particle_system.particle_positions[0, :], particle_system.particle_positions[1, :])

    # animate charge density
    densities.set_data(particle_system_history.grid_charge_densities_history[i].T)

    # animate potentials
    potentials.set_array(particle_system_history.grid_potentials_history[i].T)

    return potentials, densities,


# SIMULATION SETTINGS
animate_live = False  # animate simulation as it is running (VERY SLOW)
animate_at_end = True  # animate simulation at end
printout_interval = 500  # timesteps between printouts
snapshot_interval = 2  # timesteps between snapshots
num_time_steps = 1000  # num of time steps to simulate for


# INITIALISE PARTICLES
def initialise_test():
    # PARAMETERS
    eps_0 = 1  # permittivity of free space
    delta_t = 0.05  # step size
    num_x_nodes = 100
    num_y_nodes = 100
    x_length = 100
    y_length = 100
    delta_x = x_length / (num_x_nodes-1)  # grid resolution
    delta_y = y_length / (num_y_nodes-1)  # grid resolution

    num_particles = 100  # keep this as an even number for now

    # particle_positions = np.random.rand(2, num_particles)*[[x_length], [y_length]]
    # particle_velocities = np.random.rand(2, num_particles)*delta_x*1
    # particle_charges = np.append(np.zeros(int(num_particles/2))-10, np.zeros(int(num_particles/2))+10)
    # particle_masses = np.append(np.zeros(int(num_particles/2))+1, np.zeros(int(num_particles/2))+1)

    particle_positions = np.array([[], []])
    particle_velocities = np.array([[], []])
    particle_charges = np.array([])
    particle_masses = np.array([])

    test_vel = 1
    four_point_cross = ParticleSource(
        [[delta_x, x_length - delta_x, x_length / 3, x_length / 3 * 2],  # x pos
         [y_length / 3, y_length * 2 / 3, delta_y, y_length - delta_y]],  # y pos
        [[test_vel, -test_vel, 0, -0],  # x vel
         [0, 0, test_vel, -test_vel]],  # y vel
        [1, 1, 1, 1],  # mass
        [1, -1, -1, 1],  # charge
        1)  # freq

    side_input = ParticleSource(
        partial(uniform_side_flux, side="LEFT", x_length=x_length, y_length=y_length, delta_x=delta_x, delta_y=delta_y),
        partial(new_velocity, v_drift=np.array([[0], [0]]), v_thermal=10, M=3),
        [1],
        [5],
        1)

    positron_source = ParticleSource([[x_length/2], [y_length/3]], [[0], [0]], 1, 1, 0.5)
    electron_source = ParticleSource([[x_length/2], [y_length/3*2]], [[0], [0]], 1, -1, 0.5)

    particle_sources = [side_input]

    left_bc = create_uniform_edge_boundary(num_x_nodes, num_y_nodes, "LEFT", BoundaryTypes.DIRICHLET, 0)
    right_bc = create_uniform_edge_boundary(num_x_nodes, num_y_nodes, "RIGHT", BoundaryTypes.DIRICHLET, 0)
    upper_bc = create_uniform_edge_boundary(num_x_nodes, num_y_nodes, "UPPER", BoundaryTypes.DIRICHLET, 0)
    lower_bc = create_uniform_edge_boundary(num_x_nodes, num_y_nodes, "LOWER", BoundaryTypes.DIRICHLET, 0)

    # left_bc = create_dynamic_edge_boundary(num_x_nodes, num_y_nodes, "LEFT", BoundaryTypes.DIRICHLET, partial(sinusoidal, length=y_length, amplitude=2, period=20, phase=0))
    # right_bc = create_dynamic_edge_boundary(num_x_nodes, num_y_nodes, "RIGHT", BoundaryTypes.DIRICHLET, partial(sinusoidal, length=y_length, amplitude=2, period=20, phase=np.pi))
    # upper_bc = create_dynamic_edge_boundary(num_x_nodes, num_y_nodes, "UPPER", BoundaryTypes.DIRICHLET, cosinusoidal)
    # lower_bc = create_dynamic_edge_boundary(num_x_nodes, num_y_nodes, "LOWER", BoundaryTypes.DIRICHLET, cosinusoidal)

    charged_plate = create_charged_plate([50, 50], [55, 55], 1, BoundaryTypes.DIRICHLET)

    bcs = [left_bc, right_bc, upper_bc, lower_bc]

    left_boundary_interaction = BoundaryParticleInteraction.REFLECTIVE
    right_boundary_interaction = BoundaryParticleInteraction.REFLECTIVE
    upper_boundary_interaction = BoundaryParticleInteraction.REFLECTIVE
    lower_boundary_interaction = BoundaryParticleInteraction.REFLECTIVE

    return (particle_positions, particle_velocities, particle_charges, particle_masses, delta_t, eps_0,
            num_x_nodes, num_y_nodes, x_length, y_length, bcs, particle_sources,
            left_boundary_interaction, right_boundary_interaction, upper_boundary_interaction, lower_boundary_interaction)


def test_2():
    # Constants
    EPS_0 = 8.854e-12  # permittivity of free space, F/m
    QE = 1.602e-19  # elementary charge, C
    K = 1.381e-23  # boltzmann constant, m2kgs-2K-1
    MI = 32*1.661e-27  # ion mass, kg
    ME = 9.109e-31  # electron mass, kg

    # Sim settings
    n0 = 1e12  # neutral density, 1/m3
    phi0 = 0  # reference potential, V
    Te = 1  # electron temperature, eV
    Ti = 0.1  # ion velocity, eV
    v_drift = 7000  # ion injection velocity, m/s
    phi_p = -5  # wall potential, V

    # Calc plasma parameters
    lD = np.sqrt(EPS_0*Te / (n0*QE))  # Debye length, m
    vth = np.sqrt(2*QE*Ti/Mi)  # Thermal velocity of ions, eV

    # Sim domain
    nx = 16  # num x nodes
    ny = 10  # num y nodes
    ts = 200  # num time steps
    dh = lD  # cell width / height
    np_insert = (ny-1)*15  # number of particles to insert per cell

    # Other values
    nn = nx*ny  # total number of nodes
    dt = 0.1*dh/v_drift  # time step, s, cross 0.1dh per timestep
    Lx = (nx-1)*dh  # x domain length
    Ly = (ny-1)*dh  # y domain length

    # Plate dimensions
    lower_left = [np.floor(nx/3).astype(int), 0]
    upper_right = [np.floor(nx/3).astype(int)+2, np.floor(ny/2).astype(int)]

    # Calc specific weight
    flux = n0*v_drift*Ly  # flux of entering particles
    npt = flux*dt  # number of real particles created per time step
    spwt = npt/np_insert  # ratio of real particles per macroparticle
    mp_q = 1  # macroparticle charge

    # Particle arrays
    particle_positions = np.zeros((2, 0))
    particle_velocities = np.zeros((2, 0))
    particle_charges = np.zeros((1, 0))
    particle_masses = np.zeros((1, 0))

    # Boundary conditions
    left_bc = create_uniform_edge_boundary(nx, ny, "LEFT", BoundaryTypes.NEUMANN, 0)
    right_bc = create_uniform_edge_boundary(nx, ny, "RIGHT", BoundaryTypes.NEUMANN, 0)
    upper_bc = create_uniform_edge_boundary(nx, ny, "UPPER", BoundaryTypes.NEUMANN, 0)
    lower_bc = create_uniform_edge_boundary(nx, ny, "LOWER", BoundaryTypes.DIRICHLET, 0)

    left_boundary_interaction = BoundaryParticleInteraction.OPEN
    right_boundary_interaction = BoundaryParticleInteraction.OPEN
    upper_boundary_interaction = BoundaryParticleInteraction.OPEN
    lower_boundary_interaction = BoundaryParticleInteraction.REFLECTIVE

    bcs = [left_bc, right_bc, upper_bc, lower_bc]

    return (particle_positions, particle_velocities, particle_charges, particle_masses, dt, EPS_0,
            nx, ny, Lx, Ly, bcs, particle_sources,
            left_boundary_interaction, right_boundary_interaction, upper_boundary_interaction, lower_boundary_interaction)


# CREATE PARTICLE SYSTEM
particle_system = ParticleManager(*initialise_test())
particle_system_history = ParticleSystemHistory()
energy_diagnostic = EnergyDiagnostic()

# SET UP FIGURES
fig = plt.figure(figsize=(6, 8))

ax1 = fig.add_subplot(211)
ax1.set_title("Densities")
densities = ax1.imshow(np.zeros((particle_system.num_x_nodes, particle_system.num_y_nodes)), vmin=-7, vmax=7,
                       interpolation="bicubic", origin="lower",
                       extent=[0, particle_system.x_length, 0, particle_system.y_length])

ax2 = fig.add_subplot(212)
ax2.set_title("Potential")
potentials = ax2.imshow(np.zeros((particle_system.num_x_nodes, particle_system.num_y_nodes)), vmin=-7, vmax=7,
                        interpolation="bicubic", origin="lower",
                        extent=[0, particle_system.x_length, 0, particle_system.y_length])

if animate_live:
    animation_object = animation.FuncAnimation(fig, animate_step, interval=1, blit=True)
    plt.show()
else:
    for i in range(num_time_steps):
        particle_system.update_step()

        # printout system state
        if particle_system.current_t_step % printout_interval == 0:
            print(f'{particle_system.current_t_step/num_time_steps*100:<6.2f}% completion')
            print("Computational Time Elapsed =", time.time() - particle_system.start_time, "s")
            average_time_per_step = (time.time() - particle_system.start_time) / particle_system.current_t_step
            steps_to_go = num_time_steps - particle_system.current_t_step
            approx_time_to_go = steps_to_go*average_time_per_step
            print("Approx Time To Finish =", round(approx_time_to_go), "s")
            print("T Step =", particle_system.current_t_step, "/", num_time_steps)
            print("Simulation Time =", particle_system.current_t_step*particle_system.delta_t, "s")
            print("Total Energy =", energy_diagnostic.energy_total_history[-1])
            print("Num Particles =", particle_system.num_particles)
            print(" ")

        # take a system snapshot for animation
        if particle_system.current_t_step % snapshot_interval == 0:
            particle_system_history.take_snapshot(particle_system)
            energy_diagnostic.calc_system_energy(particle_system)

print("Simulation finished!")
input("Press ENTER to play animation")

if animate_at_end:  # run animation
    animation_object = animation.FuncAnimation(fig, animate_history, frames=len(particle_system_history.grid_potentials_history), save_count=len(particle_system_history.grid_potentials_history), interval=1, blit=True)
    plt.show()

# plot energy
energy_diagnostic.plot_energy_history()
