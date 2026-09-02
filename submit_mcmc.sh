#!/bin/bash
#SBATCH --job-name=cosmo_mcmc
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=32
#SBATCH --cpus-per-task=1
#SBATCH --time=72:00:00
#SBATCH --partition=compute
#SBATCH --output=logs/mcmc_run_%j.log

module load python/3.10
module load mpi/openmpi-x86_64
source /opt/cosmology/venv/bin/activate

echo "=========================================================================="
echo "LAUNCHING HIGH-PRECISION STAGE-IV JOINT MULTI-PROBE PRODUCTION CHAIN"
echo "=========================================================================="

# Run Cobaya under MPI to split parameter sampling paths into individual parallel chains
mpirun -np $SLURM_NTASKS cobaya-run production_mcmc.yaml --resume

echo "MCMC execution loop completed or reached target Gelman-Rubin convergence."
