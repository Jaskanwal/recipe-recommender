# Define the environment name as a variable
env_name = recipe_recommender

# Target: export_requirements
# Export the environment to an environment.yml file without including build information
export_requirements:
	@echo "Exporting environment to environment.yml"
	conda env export --no-build> environment.yml

# Target: create_env
# Create a new conda environment with the specified name
create_env: environment.yml
	@echo "Creating conda environment: $(env_name)"
	conda create --name $(env_name) -y && \
	conda env update --name $(env_name) --file environment.yml
	@echo "Activate your environment with: conda activate $(env_name)"

# Target: update_requirements
# Update the conda environment based on the environment.yml file, pruning unused packages
update_requirements: environment.yml
	@echo "Updating conda environment from environment.yml"
	conda env update --name $(env_name) --file environment.yml
